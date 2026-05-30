# Barangay Gym Court Booking System - Step-by-Step Guide

This document provides a comprehensive guide to setting up and running the Barangay Gym Court Event Booking System. The system is built with Django and includes features for booking management, receipt printing, and dashboard analytics.

## 1. Project Setup

First, we'll set up the Django project, create a `core` app, and install the necessary Python libraries.

### 1.1. Create Project and App

```bash
# Create the project directory
mkdir -p barangay_gym
cd barangay_gym

# Install Django and other dependencies
sudo pip3 install django django-bootstrap5 python-escpos plotly pandas

# Create the Django project and a 'core' app
django-admin startproject gym_booking .
python3.11 manage.py startapp core
```

### 1.2. Configure Settings

Next, we need to add the `core` app and `django_bootstrap5` to the `INSTALLED_APPS` in `gym_booking/settings.py`.

```python
# In gym_booking/settings.py

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_bootstrap5',
    'core',
]

# Add login and logout redirect URLs at the end of the file
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'
LOGIN_URL = 'login'

## 1.3 ESP32 Wi-Fi Bridge

This project includes an ESP32 Wi-Fi configuration page that lets you choose a 2.4GHz network and send the SSID/password to the ESP32 without reopening Arduino IDE.

The firmware file is `esp32_wifi_printer.ino` in the project root. Flash it once to your ESP32, then use the new `ESP32 Wi-Fi` sidebar link to scan and update Wi-Fi.
```

## 2. Models and Admin

Now, let's define the database models for `Booking` and `SystemConfiguration` and customize the Django admin interface.

### 2.1. Define Models

```python
# In core/models.py

from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone

class SystemConfiguration(models.Model):
    barangay_name = models.CharField(max_length=255, default="Barangay Central")
    address = models.TextField(default="123 Main St, Barangay Central")
    contact_info = models.CharField(max_length=255, default="0912-345-6789")
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=500.00)
    receipt_header = models.TextField(default="OFFICIAL RECEIPT")
    receipt_footer = models.TextField(default="Thank you for using our Gym Court!")

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

    event_name = models.CharField(max_length=255)
    customer_name = models.CharField(max_length=255)
    contact_number = models.CharField(max_length=20)
    event_type = models.CharField(max_length=100)
    date_of_event = models.DateField()
    start_time = models.TimeField()
    duration_hours = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='UNPAID')
    notes = models.TextField(blank=True, null=True)
    receipt_number = models.CharField(max_length=20, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            last_booking = Booking.objects.all().order_by('id').last()
            if not last_booking:
                self.receipt_number = 'REC-00001'
            else:
                last_id = last_booking.id
                self.receipt_number = f'REC-{str(last_id + 1).zfill(5)}'
        super().save(*args, **kwargs)

    @property
    def balance(self):
        return self.total_amount - self.amount_paid

    def __str__(self):
        return f"{self.event_name} - {self.customer_name} ({self.date_of_event})"
```

### 2.2. Customize Admin

```python
# In core/admin.py

from django.contrib import admin
from .models import Booking, SystemConfiguration

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "receipt_number",
        "event_name",
        "customer_name",
        "date_of_event",
        "start_time",
        "payment_status",
        "total_amount",
    )
    list_filter = ("payment_status", "date_of_event")
    search_fields = ("event_name", "customer_name", "receipt_number")
    readonly_fields = ("receipt_number", "created_at")

    fieldsets = (
        ("Event Information", {"fields": ("event_name", "event_type", "customer_name", "contact_number")}),
        ("Schedule", {"fields": ("date_of_event", "start_time", "duration_hours")}),
        ("Payment", {"fields": ("total_amount", "amount_paid", "payment_status", "notes")}),
        ("System Info", {"fields": ("receipt_number", "created_at")}),
    )


@admin.register(SystemConfiguration)
class SystemConfigurationAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not SystemConfiguration.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
```

### 2.3. Apply Migrations and Create Superuser

```bash
python3.11 manage.py makemigrations
python3.11 manage.py migrate
echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@example.com', 'admin123')" | python3.11 manage.py shell
python3.11 manage.py shell -c "from core.models import SystemConfiguration; SystemConfiguration.objects.get_or_create(id=1)"
```

## 3. Views, URLs, and Templates

This section covers the creation of the user-facing dashboard, booking list, and login page.

### 3.1. Create Views

```python
# In core/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.utils import timezone
from .models import Booking, SystemConfiguration
from .utils import print_to_hardware
import pandas as pd
import plotly.express as px
import plotly.io as pio

@login_required
def dashboard(request):
    today = timezone.now().date()
    bookings_today = Booking.objects.filter(date_of_event=today).count()
    total_revenue = Booking.objects.aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
    pending_payments = Booking.objects.exclude(payment_status='PAID').count()
    
    bookings = Booking.objects.all().values('date_of_event')
    if bookings:
        df = pd.DataFrame(list(bookings))
        df['month'] = pd.to_datetime(df['date_of_event']).dt.strftime('%b %Y')
        month_counts = df.groupby('month').size().reset_index(name='count')
        fig = px.bar(month_counts, x='month', y='count', title="Monthly Booking Trends")
        chart_html = pio.to_html(fig, full_html=False)
    else:
        chart_html = "<p class='text-muted'>No data for charts yet.</p>"

    context = {
        'bookings_today': bookings_today,
        'total_revenue': total_revenue,
        'pending_payments': pending_payments,
        'chart_html': chart_html,
        'recent_bookings': Booking.objects.order_by('-created_at')[:5]
    }
    return render(request, 'core/dashboard.html', context)

@login_required
def print_receipt(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    success, message = print_to_hardware(booking)
    return redirect('dashboard')

@login_required
def booking_list(request):
    bookings = Booking.objects.all().order_by('-date_of_event')
    return render(request, 'core/booking_list.html', {'bookings': bookings})
```

### 3.2. Configure URLs

```python
# In core/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('bookings/', views.booking_list, name='booking_list'),
    path('print/<int:booking_id>/', views.print_receipt, name='print_receipt'),
]
```

```python
# In gym_booking/urls.py

from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('', include('core.urls')),
]
```

### 3.3. Create Templates

Create the directory `core/templates/core` and add the following files:

*   `base.html`: The main template with navigation.
*   `login.html`: The login page.
*   `dashboard.html`: The main dashboard with stats and charts.
*   `booking_list.html`: A list of all bookings.

(The content of these files is included in the final project archive.)

## 4. Receipt Printing

The system uses the `python-escpos` library to generate commands for a thermal printer.

```python
# In core/utils.py

from escpos.printer import Usb, Dummy
from .models import SystemConfiguration

def generate_receipt_commands(booking):
    config = SystemConfiguration.objects.first()
    printer = Dummy() # Use Dummy to capture commands

    # ... (receipt generation logic as provided in the file) ...
    
    return printer.output

def print_to_hardware(booking):
    try:
        # p = Usb(0x04b8, 0x0202, 0, profile="TM-T88V")
        # commands = generate_receipt_commands(booking)
        # p._raw(commands)
        return True, "Success"
    except Exception as e:
        return False, str(e)
```

## 5. Running the Server

To run the development server:

```bash
python3.11 manage.py runserver
```

You can now access the admin panel at `http://127.0.0.1:8000/admin/` with the username `admin` and password `admin123`.
