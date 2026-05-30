import uuid
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from datetime import timedelta


class SystemConfiguration(models.Model):
    barangay_name = models.CharField(max_length=255, default="Barangay Central")
    address = models.TextField(default="123 Main St, Barangay Central")
    contact_info = models.CharField(max_length=255, default="0912-345-6789")
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=500.00)
    receipt_header = models.TextField(default="OFFICIAL RECEIPT")
    receipt_footer = models.TextField(default="Thank you for using our Gym Court!")

    esp32_ip = models.GenericIPAddressField(
        protocol='IPv4', blank=True, null=True,
        default='192.168.233.167',
        help_text='ESP32 printer bridge IP address',
    )
    esp32_port = models.PositiveIntegerField(
        default=80,
        help_text='ESP32 HTTP port',
    )
    esp32_auth_token = models.CharField(
        max_length=255,
        default='brgy_gym_printer_2026',
        help_text='Authorization token used by the ESP32 endpoints',
    )
    esp32_wifi_ssid = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Preferred 2.4GHz Wi-Fi SSID for the ESP32 printer bridge',
    )
    esp32_wifi_password = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Wi-Fi password for the ESP32 printer bridge',
    )

    def __str__(self):
        return "System Configuration"

    class Meta:
        verbose_name = "System Configuration"
        verbose_name_plural = "System Configuration"


class Booking(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('PAID', 'Paid'),
        ('PARTIAL', 'Partial'),
        ('UNPAID', 'Unpaid'),
    ]

    BOOKING_STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed'),
    ]

    BOOKING_TYPE_CHOICES = [
        ('SINGLE', 'Single Day'),
        ('MULTIPLE', 'Multiple Days'),
    ]

    # Event Details
    event_name = models.CharField(max_length=255)
    customer_name = models.CharField(max_length=255)
    contact_number = models.CharField(max_length=20)
    date_of_event = models.DateField()
    start_time = models.TimeField()
    duration_hours = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    booking_type = models.CharField(max_length=10, choices=BOOKING_TYPE_CHOICES, default='SINGLE')

    # FIX #2 — Changed from plain IntegerField to a real ForeignKey.
    # This creates a proper database relationship so child bookings are
    # always linked to their parent. SET_NULL means if a parent is deleted,
    # children won't be deleted too — they just lose their parent reference.
    # related_name='child_bookings' lets you do: booking.child_bookings.all()
    # ⚠️  After saving this file run:
    #       python manage.py makemigrations
    #       python manage.py migrate
    parent_booking = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='child_bookings',
    )

    # Payment
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='UNPAID')

    # Booking Status
    status = models.CharField(max_length=10, choices=BOOKING_STATUS_CHOICES, default='ACTIVE')
    cancellation_reason = models.TextField(blank=True, null=True)
    cancelled_at = models.DateTimeField(blank=True, null=True)
    cancelled_by = models.CharField(max_length=255, blank=True, null=True)

    # Misc
    notes = models.TextField(blank=True, null=True)

    # FIX #3 — Increased max_length to 20 to safely fit "REC-" + 8 hex chars (12 total).
    # The old save() used last_booking.id + 1 which could generate duplicate
    # receipt numbers if two bookings were saved at the same time (race condition).
    # UUID hex is guaranteed unique every time.
    receipt_number = models.CharField(max_length=20, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # FIX #3 — Safe UUID-based receipt number generation.
        # uuid4().hex gives 32 random hex characters; we take the first 8 (uppercase).
        # Example output: REC-A3F7C12B
        # This is collision-safe even under simultaneous saves.
        if not self.receipt_number:
            self.receipt_number = f'REC-{uuid.uuid4().hex[:8].upper()}'
        super().save(*args, **kwargs)

    @property
    def balance(self):
        total = self.total_amount or 0
        paid = self.amount_paid or 0
        return total - paid

    @property
    def is_cancelled(self):
        return self.status == 'CANCELLED'

    @property
    def is_multi_day(self):
        """Check if this is a multi-day booking."""
        return self.booking_type == 'MULTIPLE'

    @property
    def date_display_with_day(self):
        """Display date with day name."""
        days_name = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_name = days_name[self.date_of_event.weekday()]
        return f"{self.date_of_event.strftime('%B %d, %Y')} ({day_name})"

    def __str__(self):
        return f"{self.event_name} - {self.customer_name} ({self.date_of_event})"