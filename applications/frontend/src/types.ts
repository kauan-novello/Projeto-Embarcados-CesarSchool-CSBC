export type SystemStatus = "awaiting_pairing" | "online_untrained" | "training" | "model_active"

export interface PVSystem {
  id: string
  name: string
  location: string
  installedPowerKw: number
  inverterType: "on_grid" | "off_grid"
  status: SystemStatus
  trainingStartedAt: string
  photoUrl?: string
  deviceId: string | null
  weatherStationId: string | null
  lastReadingAt: string | null
}

export interface PairableDevice {
  id: string
  label: string
  lastSeenAt: string
}

export type NewSystemInput = Pick<
  PVSystem,
  "name" | "location" | "installedPowerKw" | "inverterType" | "photoUrl"
>

export interface CurrentUser {
  name: string
  email: string
}

export interface LiveMetrics {
  recordedAt: string
  powerW: number | null
  panelTempC: number | null
  ambientTempC: number | null
  ambientHumidityPct: number | null
  irradiance: number
  pressureHpa: number | null
  particulatePct: number | null
}

export interface InverterMetrics {
  recordedAt: string
  source: "cloud" | "modbus"
  powerW: number | null
  dcPowerW: number | null
  dailyYieldWh: number | null
  totalYieldWh: number | null
}

export interface PlantHour {
  hourStart: Date
  energyWh: number
  radiationWhM2: number
  airTempC: number
  humidityPct: number
  humidityEstimated: boolean
  pressureHpa: number
  windSpeedMS: number
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
  emailTo: string | null
}

export interface HourComparison {
  hourStart: Date
  expectedWh: number
  realWh: number | null
  modelVersion: string
}

export interface ModelScore {
  name: string
  isChampion: boolean
  isBaseline: boolean
  trainRmseWh: number
  cvTrainRmseWh: number
  cvRmseWh: number
  cvRmseStdWh: number
  testRmseWh: number
  testR2: number
  testDailyMapePct: number
}

export interface ModelReport {
  version: string
  modelType: string
  trainedAt: Date
  trainPeriod: [Date, Date]
  testPeriod: [Date, Date]
  nHours: number
  performanceRatio: number
  gainOverBaselinePct: number
  models: ModelScore[]
  championFolds: { fold: number; trainRmseWh: number; validationRmseWh: number }[]
  residualsByHour: { hour: number; baselineWh: number; championWh: number }[]
}

export type HealthState = "normal" | "attention" | "maintenance"

export interface PlantHealth {
  state: HealthState
  performancePct: number
  realWh: number
  expectedWh: number
  days: number
}

export interface EnergyOverview {
  health: PlantHealth | null
  generatedTodayWh: number | null
  remainingTodayWh: number | null
  tomorrowWh: number | null
  month: {
    start: Date
    generatedWh: number
    projectedWh: number | null
    typicalLowWh: number | null
    typicalHighWh: number | null
  }
}

export type EnergyPeriod = "day" | "week" | "month" | "year"

export interface EnergyBucket {
  start: Date
  realWh: number | null
  expectedWh: number | null
}
