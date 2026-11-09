/**
 * Format a date of the user accounts, "Never" when there is none
 * The short format (used in tables) omits the time
 */
export function formatAccountDate(dateString: string | null, short = false): string {
  if (!dateString) return 'Never';
  const options: Intl.DateTimeFormatOptions = short
    ? { year: 'numeric', month: 'short', day: 'numeric' }
    : { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' };
  return new Date(dateString).toLocaleDateString('en-US', options);
}
