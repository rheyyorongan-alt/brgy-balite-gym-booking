/**
 * dashboard.js
 * Barangay Gym Court Booking System
 * ─────────────────────────────────────────────────
 * General dashboard utilities:
 *   - Auto-dismiss flash messages
 *   - Sidebar toggle (mobile)
 *   - Confirm dialogs for destructive actions
 */

'use strict';


/* ─── Auto-dismiss Bootstrap alerts ────────────────────── */

function autoDismissAlerts(delayMs = 5000) {
    document.querySelectorAll('.alert-dismissible').forEach(function (alertEl) {
        setTimeout(function () {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alertEl);
            if (bsAlert) bsAlert.close();
        }, delayMs);
    });
}


/* ─── Sidebar toggle for mobile ────────────────────────── */

function initSidebarToggle() {
    const toggleBtn = document.getElementById('sidebar-toggle');
    const sidebar   = document.getElementById('sidebar');
    if (!toggleBtn || !sidebar) return;

    toggleBtn.addEventListener('click', function () {
        sidebar.classList.toggle('show');
    });

    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', function (e) {
        if (
            window.innerWidth < 768 &&
            sidebar.classList.contains('show') &&
            !sidebar.contains(e.target) &&
            e.target !== toggleBtn
        ) {
            sidebar.classList.remove('show');
        }
    });
}


/* ─── Confirm delete / cancel actions ──────────────────── */

function initConfirmActions() {
    document.querySelectorAll('[data-confirm]').forEach(function (el) {
        el.addEventListener('click', function (e) {
            const msg = el.getAttribute('data-confirm');
            if (!confirm(msg)) {
                e.preventDefault();
                return false;
            }
        });
    });
}


/* ─── Highlight today's row in tables ──────────────────── */

function highlightTodayRows() {
    const today = new Date().toISOString().split('T')[0]; // "YYYY-MM-DD"
    document.querySelectorAll('[data-event-date]').forEach(function (el) {
        if (el.getAttribute('data-event-date') === today) {
            el.classList.add('table-info');
        }
    });
}


/* ─── Print receipt helper ─────────────────────────────── */

/**
 * Optionally show a loading state on print buttons.
 */
function initPrintButtons() {
    document.querySelectorAll('.btn-print-receipt').forEach(function (btn) {
        btn.addEventListener('click', function () {
            btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Sending...';
            btn.disabled = true;
            // The page will redirect after print, re-enabling is handled by page reload
        });
    });
}


/* ─── Bootstrap ─────────────────────────────────────────── */

document.addEventListener('DOMContentLoaded', function () {
    autoDismissAlerts(6000);
    initSidebarToggle();
    initConfirmActions();
    highlightTodayRows();
    initPrintButtons();
    console.info('[dashboard.js] Initialized.');
});