from django import forms
from django.core.exceptions import ValidationError
from .models import Booking, SystemConfiguration
from datetime import datetime, timedelta


class BookingForm(forms.ModelForm):
    """
    Custom booking form with conflict detection and day selection.
    """

    date_of_event = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control form-control-modern',
            'id': 'id_date_of_event'
        }),
        label='Start Date (week beginning)',
    )

    # Days selection for multiple bookings
    days_to_book = forms.MultipleChoiceField(
        choices=[
            ('0', 'Monday'),
            ('1', 'Tuesday'),
            ('2', 'Wednesday'),
            ('3', 'Thursday'),
            ('4', 'Friday'),
            ('5', 'Saturday'),
            ('6', 'Sunday'),
        ],
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label='Select Days to Book',
        required=False,
    )

    start_time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': 'form-control form-control-modern'
        }),
        label='Start Time',
    )

    booking_type = forms.ChoiceField(
        choices=Booking.BOOKING_TYPE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label='Booking Type',
        initial='SINGLE',
    )

    class Meta:
        model = Booking
        fields = [
            'event_name',
            'customer_name',
            'contact_number',
            'booking_type',
            'date_of_event',
            'start_time',
            'duration_hours',
            'payment_status',
            'notes',
        ]
        labels = {
            'event_name':     'Event Name',
            'customer_name':  'Customer Name',
            'contact_number': 'Contact Number',
            'booking_type':   'Booking Type',
            'duration_hours': 'Duration (hours)',
            'payment_status': 'Payment Status',
            'notes':          'Notes (optional)',
        }
        widgets = {
            'event_name':     forms.TextInput(attrs={
                'class': 'form-control form-control-modern',
                'placeholder': 'e.g. Basketball Tournament'
            }),
            'customer_name':  forms.TextInput(attrs={
                'class': 'form-control form-control-modern',
                'placeholder': 'Full name of booker'
            }),
            'contact_number': forms.TextInput(attrs={
                'class': 'form-control form-control-modern',
                'placeholder': 'e.g. 09XX-XXX-XXXX'
            }),
            'duration_hours': forms.NumberInput(attrs={
                'class': 'form-control form-control-modern',
                'min': 1,
                'placeholder': '1'
            }),
            'payment_status': forms.Select(attrs={
                'class': 'form-select form-control-modern'
            }),
            'notes':          forms.Textarea(attrs={
                'class': 'form-control form-control-modern',
                'rows': 3,
                'placeholder': 'Any additional notes...'
            }),
        }

    def clean(self):
        """Validate form and check for booking conflicts."""
        cleaned_data = super().clean()

        booking_type = cleaned_data.get('booking_type')
        start_date   = cleaned_data.get('date_of_event')
        days_to_book = cleaned_data.get('days_to_book')

        # Validate start date is not in the past
        if start_date and start_date < datetime.now().date():
            raise ValidationError("Start date cannot be in the past.")

        # Validate days for multi-day bookings
        if booking_type == 'MULTIPLE':
            if not days_to_book or len(days_to_book) == 0:
                raise ValidationError("Please select at least one day for multiple-day bookings.")
            if len(days_to_book) == 1:
                raise ValidationError("For single-day bookings, please select 'Single Day' type instead.")

        # FIX #1 — Check for time-based conflicts (not just date-based).
        # Old code blocked the entire day if any booking existed.
        # New code only blocks if the time slots actually overlap.
        conflicts = self.check_booking_conflicts(start_date, days_to_book, booking_type)
        if conflicts:
            conflict_info = "\n".join([
                f"• {c['date']}: {c['event']} by {c['customer']} "
                f"({c['existing_start']} – {c['existing_end']})"
                for c in conflicts
            ])
            raise ValidationError(
                f"Booking conflict(s) detected — the time slot is already taken:\n{conflict_info}\n\n"
                f"Please choose a different time or date."
            )

        return cleaned_data

    def check_booking_conflicts(self, start_date, days_to_book, booking_type):
        """
        FIX #1 — Check for time-slot overlaps, not just date matches.

        A conflict only happens when two bookings share the same date AND
        their time windows actually overlap.

        Overlap condition:
            new booking starts BEFORE existing ends
            AND new booking ends AFTER existing starts

        Also excludes the booking being edited (edit mode) so it doesn't
        conflict with itself.
        """
        conflicts = []

        if not start_date:
            return conflicts

        # We need start_time and duration to calculate the new booking's window
        start_time     = self.cleaned_data.get('start_time')
        duration_hours = self.cleaned_data.get('duration_hours')

        if not start_time or not duration_hours:
            return conflicts

        # Calculate new booking's start and end as full datetimes
        new_start = datetime.combine(start_date, start_time)
        new_end   = new_start + timedelta(hours=int(duration_hours))

        # Determine which dates to check
        if booking_type == 'MULTIPLE' and days_to_book:
            dates_to_check = self.get_dates_for_days(start_date, days_to_book)
        else:
            dates_to_check = [start_date]

        # If editing an existing booking, exclude it from conflict check
        # so the booking doesn't conflict with its own saved time slot
        instance_id = self.instance.id if self.instance and self.instance.pk else None

        for check_date in dates_to_check:
            # Recalculate new_start/new_end for each date (important for multi-day)
            new_start_for_date = datetime.combine(check_date, start_time)
            new_end_for_date   = new_start_for_date + timedelta(hours=int(duration_hours))

            existing_bookings = Booking.objects.filter(
                date_of_event=check_date,
                status='ACTIVE',
            )

            # Exclude self when editing
            if instance_id:
                existing_bookings = existing_bookings.exclude(id=instance_id)

            for booking in existing_bookings:
                # Calculate existing booking's time window
                existing_start = datetime.combine(check_date, booking.start_time)
                existing_end   = existing_start + timedelta(hours=int(booking.duration_hours))

                # Check overlap:
                # new starts before existing ends AND new ends after existing starts
                if new_start_for_date < existing_end and new_end_for_date > existing_start:
                    conflicts.append({
                        'date':          check_date.strftime('%B %d, %Y (%A)'),
                        'event':         booking.event_name,
                        'customer':      booking.customer_name,
                        'existing_start': existing_start.strftime('%I:%M %p'),
                        'existing_end':   existing_end.strftime('%I:%M %p'),
                    })

        return conflicts

    @staticmethod
    def get_dates_for_days(start_date, days_to_book):
        """
        Convert day numbers to actual dates based on the week of start_date.
        days_to_book: list of strings like ['0', '1', '4']  (0=Mon ... 6=Sun)
        start_date:   any date in the target week
        Returns:      list of date objects for the selected days
        """
        dates    = []
        days_int = sorted([int(d) for d in days_to_book])

        # Snap to Monday of the selected week
        days_until_monday = start_date.weekday()
        actual_monday     = start_date - timedelta(days=days_until_monday)

        for day_offset in days_int:
            dates.append(actual_monday + timedelta(days=day_offset))

        return dates


class Esp32WifiConfigForm(forms.ModelForm):
    class Meta:
        model = SystemConfiguration
        fields = [
            'esp32_ip',
            'esp32_port',
            'esp32_auth_token',
            'esp32_wifi_ssid',
            'esp32_wifi_password',
        ]
        labels = {
            'esp32_ip': 'ESP32 IP Address',
            'esp32_port': 'ESP32 Port',
            'esp32_auth_token': 'ESP32 Auth Token',
            'esp32_wifi_ssid': 'Wi-Fi SSID',
            'esp32_wifi_password': 'Wi-Fi Password',
        }
        widgets = {
            'esp32_ip': forms.TextInput(attrs={
                'class': 'form-control form-control-modern',
                'placeholder': '192.168.1.100'
            }),
            'esp32_port': forms.NumberInput(attrs={
                'class': 'form-control form-control-modern',
                'min': 1,
                'max': 65535,
            }),
            'esp32_auth_token': forms.TextInput(attrs={
                'class': 'form-control form-control-modern',
                'placeholder': 'ESP32 auth token'
            }),
            'esp32_wifi_ssid': forms.TextInput(attrs={
                'class': 'form-control form-control-modern',
                'placeholder': '2.4GHz Wi-Fi SSID'
            }),
            'esp32_wifi_password': forms.PasswordInput(attrs={
                'class': 'form-control form-control-modern',
                'placeholder': 'Wi-Fi Password',
            }),
        }

    def clean_esp32_port(self):
        port = self.cleaned_data.get('esp32_port')
        if port is None or port < 1 or port > 65535:
            raise ValidationError('Please enter a valid ESP32 port between 1 and 65535.')
        return port


class AdminPasswordChangeForm(forms.Form):
    """
    Custom password change form for admin profile settings.
    Validates current password and enforces strong password requirements.
    """
    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-modern',
            'placeholder': 'Enter your current password',
            'autocomplete': 'current-password',
        }),
        label='Current Password',
        help_text='Required for security purposes'
    )

    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-modern',
            'placeholder': 'Enter your new password',
            'autocomplete': 'new-password',
            'id': 'id_new_password',
        }),
        label='New Password',
        help_text='Minimum 8 characters, must include uppercase, lowercase, and numbers'
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-modern',
            'placeholder': 'Confirm your new password',
            'autocomplete': 'new-password',
            'id': 'id_confirm_password',
        }),
        label='Confirm Password',
        help_text='Must match the new password above'
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_current_password(self):
        """Verify that the current password is correct."""
        current_password = self.cleaned_data.get('current_password')
        
        if not self.user.check_password(current_password):
            raise ValidationError('Your current password is incorrect.')
        
        return current_password

    def clean_new_password(self):
        """Validate new password meets requirements."""
        new_password = self.cleaned_data.get('new_password')
        
        if not new_password:
            raise ValidationError('New password is required.')
        
        if len(new_password) < 8:
            raise ValidationError('Password must be at least 8 characters long.')
        
        if not any(char.isupper() for char in new_password):
            raise ValidationError('Password must contain at least one uppercase letter (A-Z).')
        
        if not any(char.islower() for char in new_password):
            raise ValidationError('Password must contain at least one lowercase letter (a-z).')
        
        if not any(char.isdigit() for char in new_password):
            raise ValidationError('Password must contain at least one number (0-9).')
        
        return new_password

    def clean(self):
        """Verify that passwords match."""
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if new_password and confirm_password:
            if new_password != confirm_password:
                raise ValidationError('The passwords do not match.')
        
        return cleaned_data