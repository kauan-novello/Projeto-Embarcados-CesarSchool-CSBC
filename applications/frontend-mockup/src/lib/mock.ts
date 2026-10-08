import type { CurrentUser, LiveMetrics, MLMetrics, PVSystem } from "@/types"

const TRAINING_DAYS_REQUIRED = 365

export const DEMO_USER: CurrentUser = { name: "Cliente Demo", email: "cliente@demo.com" }

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

export function makeDemoSystem(
  status: PVSystem["status"],
  overrides: Partial<PVSystem> = {},
): PVSystem {
  const now = new Date()
  const trainingStartedAt =
    status === "training"
      ? new Date(now.getTime() - 1000 * 60 * 60 * 24 * 140).toISOString() // 140 dias já treinando
      : status === "model_active"
        ? new Date(now.getTime() - 1000 * 60 * 60 * 24 * 380).toISOString()
        : now.toISOString()

  return {
    id: crypto.randomUUID(),
    name: "Instalação Residencial — Boa Viagem",
    location: "Recife, PE",
    installedPowerKw: 4.5,
    inverterType: "on_grid",
    status,
    trainingStartedAt,
    deviceOnline: true,
    ...overrides,
  }
}

export function makeDemoSystems(): PVSystem[] {
  return [
    makeDemoSystem("model_active", {
      name: "Instalação Residencial — Boa Viagem",
      location: "Recife, PE",
      photoUrl: "/systems/boa-viagem.avif",
    }),
    makeDemoSystem("training", {
      name: "Instalação Comercial — Casa Forte",
      location: "Recife, PE",
      installedPowerKw: 9.2,
      deviceOnline: false,
      photoUrl: "/systems/casa-forte.jpeg",
    }),
    makeDemoSystem("awaiting_pairing", {
      name: "Instalação Residencial — Piedade",
      location: "Jaboatão dos Guararapes, PE",
      installedPowerKw: 3.1,
      photoUrl: "/systems/piedade.avif",
    }),
  ]
}

export function makeLiveMetrics(): LiveMetrics {
  const hour = new Date().getHours()
  const daylightFactor = hour >= 6 && hour <= 18 ? Math.sin(((hour - 6) / 12) * Math.PI) : 0

  return {
    powerW: Math.round(daylightFactor * 1800 + Math.random() * 60),
    panelTempC: Math.round((28 + daylightFactor * 22 + Math.random() * 3) * 10) / 10,
    ambientTempC: Math.round((24 + daylightFactor * 6 + Math.random() * 2) * 10) / 10,
    ambientHumidityPct: Math.round(55 + Math.random() * 15),
    irradiance: Math.round(daylightFactor * 95 + Math.random() * 5),
  }
}

export function makeMLMetrics(): MLMetrics {
  return {
    predictedEfficiencyPct: 17.8,
    predictedGenerationKwhNextDay: 21.4,
    modelVersion: "rf-v3 (MLflow run 8f2a1c)",
  }
}

export const OFFLINE_THRESHOLD_SECONDS = 12

export function formatFreshness(seconds: number): string {
  if (seconds < 60) return `${seconds}s`
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  return remainingSeconds === 0 ? `${minutes}min` : `${minutes}min ${remainingSeconds}s`
}
