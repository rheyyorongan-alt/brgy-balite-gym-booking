/**
 * booking_form.js
 * Barangay Gym Court Booking System
 * ─────────────────────────────────────────────────────────
 * Handles the Add / Edit Booking form UI:
 *   - Show/hide the "Days to Book" section based on booking type
 *   - Show/hide the Monday hint text based on booking type
 *   - Update date label text without wiping the red asterisk (FIX #7)
 *   - Client-side validation before submit
 *   - Submit button loading state to prevent double-clicks
 *
 * Place this file at:
 *   core/static/core/js/booking_form.js
 */

'use strict';

// ─── Toggle the "Days to Book" section ───────────────────────

function toggleDaysSelection() {
    const selectedRadio = document.querySelector('input[name="booking_type"]:checked');
    if (!selectedRadio) return;

    const bookingType    = selectedRadio.value;
    const daysContainer  = document.getElementById('days_container');
    const daysCheckboxes = document.querySelectorAll('input[name="days_to_book"]');

    // FIX #7 — Only swap the text node inside <span id="date-label-text">,
    // NOT the entire label. This preserves the red asterisk <span> beside it.
    const dateLabelText  = document.getElementById('date-label-text');

    // FIX #6 — The Monday hint is now a separate element we can show/hide.
    const mondayHint     = document.getElementById('monday-hint');

    if (!daysContainer) return;

    if (bookingType === 'MULTIPLE') {
        daysContainer.style.display = 'block';
        setTimeout(() => daysContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' }), 50);

        // FIX #7 — Safe label update: only changes the text span, asterisk stays intact
        if (dateLabelText) {
            dateLabelText.textContent = 'Start Date (Week Beginning – Monday)';
        }

        // FIX #6 — Show the Monday hint only for Multiple Days
        if (mondayHint) {
            mondayHint.style.display = 'inline';
        }

    } else {
        daysContainer.style.display = 'none';
        // Clear all day checkboxes when switching back to SINGLE
        daysCheckboxes.forEach(cb => cb.checked = false);

        // FIX #7 — Safe label update
        if (dateLabelText) {
            dateLabelText.textContent = 'Date of Event';
        }

        // FIX #6 — Hide the Monday hint for Single Day
        if (mondayHint) {
            mondayHint.style.display = 'none';
        }
    }
}

// ─── Client-side form validation ─────────────────────────────

function validateBookingForm(e) {
    const bookingType  = document.querySelector('input[name="booking_type"]:checked');
    const startDate    = document.getElementById('id_date_of_event');
    const startTime    = document.querySelector('input[name="start_time"]');
    const duration     = document.querySelector('input[name="duration_hours"]');
    const checkedDays  = document.querySelectorAll('input[name="days_to_book"]:checked');

    // Reset any previous custom validity
    if (startDate) startDate.setCustomValidity('');
    if (startTime) startTime.setCustomValidity('');
    if (duration)  duration.setCustomValidity('');

    // Start date required
    if (!startDate || !startDate.value) {
        startDate && startDate.setCustomValidity('Please select a date.');
        e.preventDefault();
        startDate && startDate.reportValidity();
        return false;
    }

    // Start date must not be in the past
    const today    = new Date();
    today.setHours(0, 0, 0, 0);
    const selected = new Date(startDate.value + 'T00:00:00');
    if (selected < today) {
        startDate.setCustomValidity('Event date cannot be in the past.');
        e.preventDefault();
        startDate.reportValidity();
        return false;
    }

    // Multi-day: at least 2 days required
    if (bookingType && bookingType.value === 'MULTIPLE') {
        if (checkedDays.length === 0) {
            e.preventDefault();
            // Insert alert near the days section for better visibility
            showFormAlert(
                'Please select at least one day for multiple-day bookings.',
                'danger',
                'days_container'
            );
            document.getElementById('days_container').scrollIntoView({ behavior: 'smooth' });
            return false;
        }
        if (checkedDays.length === 1) {
            e.preventDefault();
            showFormAlert(
                "You selected only 1 day — please use 'Single Day' booking type instead.",
                'warning',
                'days_container'
            );
            document.getElementById('days_container').scrollIntoView({ behavior: 'smooth' });
            return false;
        }
    }

    // Duration must be ≥ 1
    if (duration && parseInt(duration.value) < 1) {
        duration.setCustomValidity('Duration must be at least 1 hour.');
        e.preventDefault();
        duration.reportValidity();
        return false;
    }

    // All good — show loading state
    setSubmitLoading(true);
    return true;
}

// ─── Submit button loading state ─────────────────────────────

function setSubmitLoading(loading) {
    const btn = document.getElementById('submitBtn');
    if (!btn) return;

    if (loading) {
        btn.disabled = true;
        btn.dataset.originalText = btn.innerHTML;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>Saving…';
    } else {
        btn.disabled = false;
        if (btn.dataset.originalText) {
            btn.innerHTML = btn.dataset.originalText;
        }
    }
}

// ─── Inline alert helper ──────────────────────────────────────

/**
 * Show an alert message near a specific element (by id) or at the top of the form.
 * insertNearId: optional element id — alert is inserted BEFORE that element.
 */
function showFormAlert(message, type = 'danger', insertNearId = null) {
    // Remove any existing inline alert
    const existing = document.getElementById('js-form-alert');
    if (existing) existing.remove();

    const alert = document.createElement('div');
    alert.id = 'js-form-alert';
    alert.className = `alert alert-${type} alert-dismissible fade show mb-3`;
    alert.setAttribute('role', 'alert');
    alert.innerHTML = `
        <i class="bi bi-exclamation-circle me-2"></i>${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    if (insertNearId) {
        const target = document.getElementById(insertNearId);
        if (target) {
            target.parentNode.insertBefore(alert, target);
            return;
        }
    }

    // Fallback: prepend to form
    const form = document.getElementById('bookingForm');
    if (form) form.prepend(alert);
}

// ─── Highlight the selected day checkboxes ───────────────────

function initDayCheckboxHighlight() {
    document.querySelectorAll('input[name="days_to_book"]').forEach(function (cb) {
        const label = document.querySelector(`label[for="${cb.id}"]`);
        if (!label) return;

        const updateStyle = () => {
            label.style.color      = cb.checked ? '#1a56db' : '';
            label.style.fontWeight = cb.checked ? '700'     : '500';
        };

        cb.addEventListener('change', updateStyle);
        updateStyle(); // apply on page load (restores highlight after validation error)
    });
}

// ─── Bootstrap ───────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', function () {
    // Attach booking-type change listener to all radio buttons
    document.querySelectorAll('input[name="booking_type"]').forEach(function (radio) {
        radio.addEventListener('change', toggleDaysSelection);
    });

    // Run once on page load to set correct initial state
    toggleDaysSelection();

    // Attach form submit validation
    const form = document.getElementById('bookingForm');
    if (form) {
        form.addEventListener('submit', validateBookingForm);
    }

    // Highlight selected days (also handles restored checkboxes after error)
    initDayCheckboxHighlight();

    console.info('[booking_form.js] Initialized.');
});