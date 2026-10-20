import { apiFetch } from "./api"
import type { LiveMetrics, MLMetrics, OverheatAlert } from "@/types"

interface ReadingResponse {
  id: string
  recorded_at: string
  power_w: number | null
  panel_temp_c: number | null
  ambient_temp_c: number | null
  ambient_humidity_pct: number | null
  irradiance: number
  pressure_hpa: number | null
  particulate_pct: number | null
}

interface OverheatAlertResponse {
  id: string
  panel_temp_c: number
  threshold_c: number
  email_to: string | null
  triggered_at: string
}

interface MLPredictionResponse {
  predicted_efficiency_pct: number
  predicted_generation_kwh_next_day: number
  model_version: string
}

function toLiveMetrics(response: ReadingResponse): LiveMetrics {
  return {
    recordedAt: response.recorded_at,
    powerW: response.power_w,
    panelTempC: response.panel_temp_c,
    ambientTempC: response.ambient_temp_c,
    ambientHumidityPct: response.ambient_humidity_pct,
    irradiance: response.irradiance,
    pressureHpa: response.pressure_hpa,
    particulatePct: response.particulate_pct,
  }
}

function toOverheatAlert(response: OverheatAlertResponse): OverheatAlert {
  return {
    id: response.id,
    timestamp: new Date(response.triggered_at),
    panelTempC: response.panel_temp_c,
    thresholdC: response.threshold_c,
    emailTo: response.email_to,
  }
}

function toMLMetrics(response: MLPredictionResponse): MLMetrics {
  return {
    predictedEfficiencyPct: response.predicted_efficiency_pct,
    predictedGenerationKwhNextDay: response.predicted_generation_kwh_next_day,
    modelVersion: response.model_version,
  }
}

export async function getLatestReading(systemId: string): Promise<LiveMetrics | null> {
  const response = await apiFetch<ReadingResponse | null>(`/systems/${systemId}/readings/latest`)
  return response ? toLiveMetrics(response) : null
}

export async function listReadings(
  systemId: string,
  from: Date,
  to: Date,
): Promise<(LiveMetrics & { recordedAt: string })[]> {
  const params = new URLSearchParams({ from: from.toISOString(), to: to.toISOString() })
  const response = await apiFetch<ReadingResponse[]>(`/systems/${systemId}/readings?${params}`)
  return response.map(toLiveMetrics)
}

export async function listAlerts(systemId: string): Promise<OverheatAlert[]> {
  const response = await apiFetch<OverheatAlertResponse[]>(`/systems/${systemId}/alerts`)
  return response.map(toOverheatAlert)
}

export async function getMlMetrics(systemId: string): Promise<MLMetrics | null> {
  const response = await apiFetch<MLPredictionResponse | null>(`/systems/${systemId}/ml-metrics`)
  return response ? toMLMetrics(response) : null
}
