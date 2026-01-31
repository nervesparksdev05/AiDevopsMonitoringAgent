/**
 * Time formatting utilities for Indian Standard Time (IST)
 */

const IST_LOCALE = 'en-IN';
const IST_TIMEZONE = 'Asia/Kolkata';

/**
 * Format a timestamp to IST date and time
 * @param {string|Date} timestamp - ISO timestamp or Date object
 * @returns {string} Formatted date and time in IST
 */
export function formatDateTime(timestamp) {
    if (!timestamp) return 'N/A';

    try {
        const date = new Date(timestamp);
        return date.toLocaleString(IST_LOCALE, {
            timeZone: IST_TIMEZONE,
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: true
        });
    } catch {
        return timestamp;
    }
}

/**
 * Format a timestamp to IST date only
 * @param {string|Date} timestamp - ISO timestamp or Date object
 * @returns {string} Formatted date in IST
 */
export function formatDate(timestamp) {
    if (!timestamp) return 'N/A';

    try {
        const date = new Date(timestamp);
        return date.toLocaleDateString(IST_LOCALE, {
            timeZone: IST_TIMEZONE,
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    } catch {
        return timestamp;
    }
}

/**
 * Format a timestamp to IST time only
 * @param {string|Date} timestamp - ISO timestamp or Date object
 * @returns {string} Formatted time in IST
 */
export function formatTime(timestamp) {
    if (!timestamp) return 'N/A';

    try {
        const date = new Date(timestamp);
        return date.toLocaleTimeString(IST_LOCALE, {
            timeZone: IST_TIMEZONE,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: true
        });
    } catch {
        return timestamp;
    }
}

/**
 * Get current time in IST
 * @returns {string} Current date and time in IST
 */
export function getCurrentIST() {
    return formatDateTime(new Date());
}
