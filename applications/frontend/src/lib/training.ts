import type { PVSystem } from "@/types"

const TRAINING_DAYS_REQUIRED = 365

export function daysSince(isoDate: string): number {
  const ms = Date.now() - new Date(isoDate).getTime()
  return Math.max(0, Math.floor(ms / (1000 * 60 * 60 * 24)))
}

export function trainingProgressPct(system: PVSystem): number {
  if (system.status !== "training") return system.status === "model_active" ? 100 : 0
  const elapsed = daysSince(system.trainingStartedAt)
  return Math.min(100, Math.round((elapsed / TRAINING_DAYS_REQUIRED) * 100))
}

export function trainingDaysRemaining(system: PVSystem): number {
  const elapsed = daysSince(system.trainingStartedAt)
  return Math.max(0, TRAINING_DAYS_REQUIRED - elapsed)
}

export function formatFreshness(seconds: number): string {
  if (seconds < 60) return `${seconds}s`
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  return remainingSeconds === 0 ? `${minutes}min` : `${minutes}min ${remainingSeconds}s`
}
