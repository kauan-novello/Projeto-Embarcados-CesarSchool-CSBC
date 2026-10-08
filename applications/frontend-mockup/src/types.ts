export type SystemStatus = "awaiting_pairing" | "online_untrained" | "training" | "model_active"

export interface PVSystem {
  id: string
  name: string
  location: string
  installedPowerKw: number
  inverterType: "on_grid" | "off_grid"
  status: SystemStatus
  trainingStartedAt: string // ISO date
  photoUrl?: string
  /** Se o dispositivo pareado está enviando dado agora. Irrelevante enquanto status === "awaiting_pairing". */
  deviceOnline: boolean
}

export type NewSystemInput = Pick<
  PVSystem,
  "name" | "location" | "installedPowerKw" | "inverterType" | "photoUrl"
>

export interface LiveMetrics {
  powerW: number
  panelTempC: number
  ambientTempC: number
  ambientHumidityPct: number
  irradiance: number // 0-100, proxy via LDR
}

export interface MLMetrics {
  predictedEfficiencyPct: number
  predictedGenerationKwhNextDay: number
  modelVersion: string
}

export interface OverheatAlert {
  id: string
  timestamp: Date
  panelTempC: number
  thresholdC: number
  emailTo: string
}

export interface CurrentUser {
  name: string
  email: string
}
