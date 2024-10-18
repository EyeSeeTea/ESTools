// Utility function to calculate Unix time for last n days
export function getUnixTimeForLastNDays(n: number): { startUnixTime: number, endUnixTime: number } {
  const now = new Date();
  const endUnixTime = now.getTime(); // Current time in milliseconds

  const startDate = new Date(now);
  startDate.setDate(now.getDate() - n);
  const startUnixTime = startDate.getTime(); // n days before now in milliseconds

  return { startUnixTime, endUnixTime };
}

export function formatDuration(ms: number): string {
  const hours = ms / 3600000;
  return hours.toFixed(2);
}