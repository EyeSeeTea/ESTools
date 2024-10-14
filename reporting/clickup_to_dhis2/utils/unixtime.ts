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
    const totalSeconds = Math.floor(ms / 1000);
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;
  
    return `${hours}h ${minutes}m ${seconds}s`;
}