import { format, isSameDay, isSameMonth, parseISO } from "date-fns"
import { ptBR } from "date-fns/locale"
import { apiFetch } from "./api"
import { MIN_SUN_HOUR_WH } from "./predictions"
import type { EnergyBucket, EnergyOverview, EnergyPeriod, HealthState } from "@/types"

interface EnergyOverviewResponse {
  health: {
    state: HealthState
    performance_pct: number
    real_energy_wh: number
    expected_energy_wh: number
    days: number
  } | null
  generated_today_wh: number | null
  remaining_today_wh: number | null
  tomorrow_wh: number | null
  month: {
    month_start: string
    generated_wh: number
    projected_wh: number | null
    typical_low_wh: number | null
    typical_high_wh: number | null
  }
}

interface EnergyBucketResponse {
  start: string
  real_energy_wh: number | null
  expected_energy_wh: number | null
}

export async function getEnergyOverview(systemId: string): Promise<EnergyOverview> {
  const r = await apiFetch<EnergyOverviewResponse>(`/systems/${systemId}/energy/overview`)
  return {
    health: r.health && {
      state: r.health.state,
      performancePct: r.health.performance_pct,
      realWh: r.health.real_energy_wh,
      expectedWh: r.health.expected_energy_wh,
      days: r.health.days,
    },
    generatedTodayWh: r.generated_today_wh,
    remainingTodayWh: r.remaining_today_wh,
    tomorrowWh: r.tomorrow_wh,
    month: {
      start: parseISO(r.month.month_start),
      generatedWh: r.month.generated_wh,
      projectedWh: r.month.projected_wh,
      typicalLowWh: r.month.typical_low_wh,
      typicalHighWh: r.month.typical_high_wh,
    },
  }
}

export async function listEnergySeries(systemId: string, period: EnergyPeriod): Promise<EnergyBucket[]> {
  const response = await apiFetch<EnergyBucketResponse[]>(`/systems/${systemId}/energy/series?period=${period}`)
  return response.map((row) => ({
    start: new Date(row.start),
    realWh: row.real_energy_wh,
    expectedWh: row.expected_energy_wh,
  }))
}

export const energyPeriodOptions: { value: EnergyPeriod; label: string }[] = [
  { value: "day", label: "Dia" },
  { value: "week", label: "Semana" },
  { value: "month", label: "Mês" },
  { value: "year", label: "Ano" },
]

const bucketLabelFormat: Record<EnergyPeriod, string> = {
  day: "HH'h'",
  week: "EEEEEE dd/MM",
  month: "dd/MM",
  year: "MMM",
}

export function bucketLabel(start: Date, period: EnergyPeriod): string {
  return format(start, bucketLabelFormat[period], { locale: ptBR })
}

export function shownBuckets(buckets: EnergyBucket[], period: EnergyPeriod, now: Date): EnergyBucket[] {
  if (period === "day") {
    return buckets.filter((b) => (b.expectedWh ?? 0) >= MIN_SUN_HOUR_WH || (b.realWh ?? 0) >= MIN_SUN_HOUR_WH)
  }
  const running = period === "year" ? isSameMonth : isSameDay
  return buckets.map((b) => (running(b.start, now) ? { ...b, realWh: null } : b))
}

const wholeKwh = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 0 })

export function formatKwh(wh: number): string {
  return `${wholeKwh.format(wh / 1000)} kWh`
}

export const healthCopy: Record<HealthState, { title: string; advice: string | null }> = {
  normal: { title: "Sua usina está gerando o esperado", advice: null },
  attention: {
    title: "Sua usina está gerando um pouco abaixo do esperado",
    advice: "Acompanhe nos próximos dias.",
  },
  maintenance: {
    title: "Sua usina está gerando bem abaixo do esperado",
    advice: "Recomendamos uma inspeção ou a limpeza dos painéis.",
  },
}
