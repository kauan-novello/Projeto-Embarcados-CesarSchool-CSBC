import { hashSeed, seededRandom } from "@/lib/prng"
import type { OverheatAlert, PVSystem } from "@/types"
import { daysSince } from "@/lib/mock"

export const OVERHEAT_THRESHOLD_C = 65
export const RECENT_ALERT_THRESHOLD_DAYS = 7
const DEMO_EMAIL = "cliente@demo.com"

/** Histórico determinístico de alertas de superaquecimento (~1 a cada 25 dias conectados). */
export function generateAlertHistory(system: PVSystem): OverheatAlert[] {
  const connectedDays = daysSince(system.trainingStartedAt)
  if (connectedDays === 0) return []

  const alertCount = Math.min(8, Math.floor(connectedDays / 25))
  const alerts: OverheatAlert[] = []

  for (let i = 0; i < alertCount; i++) {
    const seed = hashSeed(`${system.id}-alert`, i)
    const daysAgo = Math.floor(seededRandom(seed) * connectedDays)
    const timestamp = new Date(Date.now() - daysAgo * 24 * 60 * 60 * 1000)
    // horário de pico de sol, onde o superaquecimento é mais provável
    timestamp.setHours(12 + Math.floor(seededRandom(seed + 1) * 4), Math.floor(seededRandom(seed + 2) * 60))

    alerts.push({
      id: `${system.id}-alert-${i}`,
      timestamp,
      panelTempC: Math.round((OVERHEAT_THRESHOLD_C + 1 + seededRandom(seed + 3) * 8) * 10) / 10,
      thresholdC: OVERHEAT_THRESHOLD_C,
      emailTo: DEMO_EMAIL,
    })
  }

  return alerts.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
}

export function getLastAlert(system: PVSystem): OverheatAlert | null {
  return generateAlertHistory(system)[0] ?? null
}

/** True se o alerta ocorreu há menos de RECENT_ALERT_THRESHOLD_DAYS dias. */
export function isRecentAlert(alert: OverheatAlert): boolean {
  const daysSinceAlert = (Date.now() - alert.timestamp.getTime()) / (1000 * 60 * 60 * 24)
  return daysSinceAlert < RECENT_ALERT_THRESHOLD_DAYS
}
