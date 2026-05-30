from django.contrib import admin
from .models import Booking, SystemConfiguration


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'receipt_number',
        'event_name',
        'customer_name',
        'date_of_event',
        'start_time',
        'status',           # ← NEW: shows Active / Cancelled / Completed
        'payment_status',
        'total_amount',
        'created_at',
    )
    list_filter = ('status', 'payment_status', 'date_of_event')
    search_fields = ('event_name', 'customer_name', 'receipt_number', 'contact_number')
    readonly_fields = ('receipt_number', 'created_at', 'cancelled_at', 'cancelled_by')
    ordering = ('-created_at',)

    fieldsets = (
        ('Event Information', {
            'fields': ('event_name', 'date_of_event', 'start_time', 'duration_hours')
        }),
        ('Customer Information', {
            'fields': ('customer_name', 'contact_number')
        }),
        ('Payment', {
            'fields': ('payment_status',)
        }),
        ('Booking Status', {
            'fields': ('status',)
        }),
        ('Cancellation Details', {
            'fields': ('cancellation_reason', 'cancelled_at', 'cancelled_by'),
            'classes': ('collapse',),   # hidden by default, expands if cancelled
        }),
        ('System Info', {
            'fields': ('receipt_number', 'notes', 'created_at'),
            'classes': ('collapse',),
        }),
    )


@admin.register(SystemConfiguration)
class SystemConfigurationAdmin(admin.ModelAdmin):
    fieldsets = (
        ('General', {
            'fields': (
                'barangay_name',
                'address',
                'contact_info',
                'hourly_rate',
                'receipt_header',
                'receipt_footer',
            ),
        }),
        ('ESP32 Printer Bridge', {
            'fields': (
                'esp32_ip',
                'esp32_port',
                'esp32_auth_token',
                'esp32_wifi_ssid',
                'esp32_wifi_password',
            ),
        }),
    )

    def has_add_permission(self, request):
        # Only allow ONE configuration record to exist
        return not SystemConfiguration.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Prevent deleting the configuration
        return False