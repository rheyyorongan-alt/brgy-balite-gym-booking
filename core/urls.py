from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('bookings/', views.booking_list, name='booking_list'),
    path('bookings/add/', views.add_booking, name='add_booking'),
    path('bookings/edit/<int:booking_id>/', views.edit_booking, name='edit_booking'),
    path('bookings/cancel/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
    path('bookings/delete/<int:booking_id>/', views.delete_booking, name='delete_booking'),
    path('bookings/delete-selected/', views.bulk_delete_bookings, name='bulk_delete_bookings'),
    path('print/<int:booking_id>/', views.print_receipt, name='print_receipt'),
    path('esp32-wifi/', views.esp32_wifi_settings, name='esp32_wifi_settings'),
    path('api/calendar-events/', views.booking_calendar_data, name='calendar_events'),
    path('bookings/export/excel/', views.export_excel, name='export_excel'),
    path('bookings/export/pdf/',   views.export_pdf,   name='export_pdf'),
    path('settings/', views.profile_settings, name='profile_settings'),
]