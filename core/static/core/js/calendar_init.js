/**
 * calendar_init.js
 * Barangay Gym Court Booking System
 * ─────────────────────────────────────────────────
 * Initializes FullCalendar on the dashboard page.
 * Fetches booking events from the Django API endpoint.
 *
 * Requires:
 *   - FullCalendar v6 (loaded via CDN in dashboard.html)
 *   - A DOM element with id="booking-calendar"
 *   - A global variable `CALENDAR_EVENTS_URL` set in the template
 */

'use strict';

/**
 * Initialize the FullCalendar instance.
 * @param {string} eventsUrl - The API URL to fetch booking events JSON.
 */
function initBookingCalendar(eventsUrl) {
    const calendarEl = document.getElementById('booking-calendar');
    if (!calendarEl) {
        console.warn('[calendar_init] Element #booking-calendar not found.');
        return;
    }

    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',

        headerToolbar: {
            left:   'prev,next today',
            center: 'title',
            right:  'dayGridMonth,timeGridWeek,listWeek',
        },

        height: 540,
        nowIndicator: true,
        dayMaxEvents: 3,

        buttonText: {
            today: 'Today',
            month: 'Month',
            week:  'Week',
            list:  'List',
        },

        eventSources: [
            {
                url:    eventsUrl,
                method: 'GET',
                failure: function () {
                    console.error('[calendar_init] Failed to load calendar events from:', eventsUrl);
                },
            }
        ],

        /**
         * Navigate to the booking list filtered by the event when clicked.
         */
        eventClick: function (info) {
            info.jsEvent.preventDefault();
            if (info.event.url) {
                window.location.href = info.event.url;
            }
        },

        /**
         * Add a native tooltip with event info on mount.
         */
        eventDidMount: function (info) {
            const props = info.event.extendedProps;
            info.el.setAttribute(
                'title',
                [
                    '📅 ' + info.event.title,
                    '👤 Customer: ' + (props.customer    || 'N/A'),
                    '🔖 Status: '   + (props.status      || 'N/A'),
                    '💳 Payment: '  + (props.payment_status || 'N/A'),
                ].join('\n')
            );
        },
    });

    calendar.render();
    console.info('[calendar_init] FullCalendar initialized successfully.');
    return calendar;
}


/* ─── Dashboard-specific helpers ───────────────────────── */

/**
 * Update the topbar date display.
 */
function updateTopbarDate() {
    const el = document.getElementById('topbar-date');
    if (!el) return;
    const now = new Date();
    el.textContent = now.toLocaleDateString('en-PH', {
        weekday: 'short',
        year:    'numeric',
        month:   'short',
        day:     'numeric',
    });
}


/* ─── Bootstrap (run after DOM is ready) ───────────────── */

document.addEventListener('DOMContentLoaded', function () {
    updateTopbarDate();

    // The template should set: window.CALENDAR_EVENTS_URL = "{% url 'calendar_events' %}"
    if (typeof window.CALENDAR_EVENTS_URL !== 'undefined') {
        initBookingCalendar(window.CALENDAR_EVENTS_URL);
    }
});