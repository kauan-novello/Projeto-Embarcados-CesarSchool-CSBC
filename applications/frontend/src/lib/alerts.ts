import type { OverheatAlert } from "@/types"

export const RECENT_ALERT_THRESHOLD_DAYS = 7

export function isRecentAlert(alert: OverheatAlert): boolean {
  const daysSinceAlert = (Date.now() - alert.timestamp.getTime()) / (1000 * 60 * 60 * 24)
  return daysSinceAlert < RECENT_ALERT_THRESHOLD_DAYS
}
