import { differenceInSeconds, formatDistanceStrict } from "date-fns"
import { ptBR } from "date-fns/locale"
import { apiFetch } from "./api"
import type { InverterMetrics } from "@/types"

export const INVERTER_STALE_SECONDS = 15 * 60

export type InverterStatus = "generating" | "idle" | "stale"

export const inverterStatusLabel: Record<InverterStatus, string> = {
  generating: "Gerando",
  idle: "Sem geração",
  stale: "Sem dados recentes",
}

interface InverterReadingResponse {
  recorded_at: string
  source: InverterMetrics["source"]
  power_w: number | null
  dc_power_w: number | null
  daily_yield_wh: number | null
  total_yield_wh: number | null
}

export async function getLatestInverterReading(systemId: string): Promise<InverterMetrics | null> {
  const response = await apiFetch<InverterReadingResponse | null>(`/systems/${systemId}/inverter/latest`)
  if (!response) return null
  return {
    recordedAt: response.recorded_at,
    source: response.source,
    powerW: response.power_w,
    dcPowerW: response.dc_power_w,
    dailyYieldWh: response.daily_yield_wh,
    totalYieldWh: response.total_yield_wh,
  }
}

export function isInverterReadingStale(reading: InverterMetrics, now: Date): boolean {
  return differenceInSeconds(now, new Date(reading.recordedAt)) > INVERTER_STALE_SECONDS
}

export function getInverterStatus(reading: InverterMetrics, now: Date): InverterStatus {
  if (isInverterReadingStale(reading, now)) return "stale"
  return (reading.powerW ?? 0) > 0 ? "generating" : "idle"
}

export function formatInverterAge(reading: InverterMetrics, now: Date): string {
  return formatDistanceStrict(new Date(reading.recordedAt), now, { locale: ptBR })
}

const decimal = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 1 })

export function formatPower(watts: number | null): string {
  return watts === null ? "—" : `${decimal.format(watts / 1000)} kW`
}

export function formatEnergy(wattHours: number | null): string {
  if (wattHours === null) return "—"
  return wattHours >= 1_000_000
    ? `${decimal.format(wattHours / 1_000_000)} MWh`
    : `${decimal.format(wattHours / 1000)} kWh`
}
