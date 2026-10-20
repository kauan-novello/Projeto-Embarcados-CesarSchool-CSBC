import { addHours, format } from "date-fns"
import { apiFetch } from "./api"
import { bucketFor } from "./history"
import { getSeason, type Season } from "./seasons"
import type { PlantHour } from "@/types"

export type PlantGrouping = "hour" | "day" | "week" | "month"

export const plantGroupingOptions: { value: PlantGrouping; label: string }[] = [
  { value: "hour", label: "Por hora" },
  { value: "day", label: "Por dia" },
  { value: "week", label: "Por semana" },
  { value: "month", label: "Por mês" },
]

interface PlantHourResponse {
  hour_start: string
  energy_wh: number
  radiation_wh_m2: number
  air_temp_c: number
  humidity_pct: number
  humidity_estimated: boolean
  pressure_hpa: number
  wind_speed_m_s: number
}

export async function listPlantHours(systemId: string): Promise<PlantHour[]> {
  const response = await apiFetch<PlantHourResponse[]>(`/systems/${systemId}/hourly`)
  return response.map((row) => ({
    hourStart: new Date(row.hour_start),
    energyWh: row.energy_wh,
    radiationWhM2: row.radiation_wh_m2,
    airTempC: row.air_temp_c,
    humidityPct: row.humidity_pct,
    humidityEstimated: row.humidity_estimated,
    pressureHpa: row.pressure_hpa,
    windSpeedMS: row.wind_speed_m_s,
  }))
}

export interface PlantRow {
  key: string
  label: string
  start: Date
  season: Season
  hours: number
  energyKwh: number
  radiationWhM2: number
  airTempC: number
  humidityPct: number
  pressureHpa: number
  windSpeedMS: number
}

const mean = (values: number[]) => values.reduce((sum, v) => sum + v, 0) / values.length
const sum = (values: number[]) => values.reduce((total, v) => total + v, 0)
const round = (value: number, decimals: number) => Math.round(value * 10 ** decimals) / 10 ** decimals

export function groupPlantHours(hours: PlantHour[], grouping: PlantGrouping): PlantRow[] {
  const buckets = new Map<string, { start: Date; label: string; items: PlantHour[] }>()
  for (const hour of hours) {
    const { key, start, label } = bucketFor(hour.hourStart, grouping)
    const bucket = buckets.get(key)
    if (bucket) bucket.items.push(hour)
    else buckets.set(key, { start, label, items: [hour] })
  }

  return Array.from(buckets.entries())
    .map(([key, { start, label, items }]) => ({
      key,
      label,
      start,
      season: getSeason(start),
      hours: items.length,
      energyKwh: round(sum(items.map((h) => h.energyWh)) / 1000, 1),
      radiationWhM2: round(sum(items.map((h) => h.radiationWhM2)), 0),
      airTempC: round(mean(items.map((h) => h.airTempC)), 1),
      humidityPct: round(mean(items.map((h) => h.humidityPct)), 0),
      pressureHpa: round(mean(items.map((h) => h.pressureHpa)), 1),
      windSpeedMS: round(mean(items.map((h) => h.windSpeedMS)), 1),
    }))
    .sort((a, b) => b.start.getTime() - a.start.getTime())
}

export function formatHourRange(hourStart: Date): string {
  return `${format(hourStart, "dd/MM, HH'h'")}–${format(addHours(hourStart, 1), "HH'h'")}`
}

const decimal = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 1 })

export function roundKwh(wh: number, digits = 2): number {
  return Math.round((wh / 1000) * 10 ** digits) / 10 ** digits
}

export const kwhTick = (value: number) => value.toLocaleString("pt-BR", { maximumFractionDigits: 1 })

export function formatNumber(value: number, unit: string): string {
  return `${decimal.format(value)}${unit}`
}
