import { useEffect, useMemo, useState } from "react"
import { addDays, format } from "date-fns"
import { ptBR } from "date-fns/locale"
import { CalendarClock, CalendarDays, CalendarRange, CircleAlert, CircleCheck, TriangleAlert, Zap, type LucideIcon } from "lucide-react"
import { CartesianGrid, Line, LineChart, XAxis, YAxis } from "recharts"
import { Button } from "@/components/ui/button"
import { ChartContainer, ChartLegend, ChartLegendContent, ChartTooltip, ChartTooltipContent, type ChartConfig } from "@/components/ui/chart"
import {
  bucketLabel,
  energyPeriodOptions,
  formatKwh,
  getEnergyOverview,
  healthCopy,
  listEnergySeries,
  shownBuckets,
} from "@/lib/energyOverview"
import { kwhTick, roundKwh } from "@/lib/plantHourly"
import type { EnergyBucket, EnergyOverview, EnergyPeriod, HealthState, PlantHealth } from "@/types"
import { StatCard } from "./StatCard"

const REFRESH_MS = 5 * 60_000

const chartConfig = {
  real: { label: "Real", color: "var(--primary)" },
  expected: { label: "Previsto", color: "var(--muted-foreground)" },
} satisfies ChartConfig

const healthStyle: Record<HealthState, { icon: LucideIcon; className: string }> = {
  normal: {
    icon: CircleCheck,
    className: "border-emerald-500/40 bg-emerald-500/10 text-emerald-700 dark:text-emerald-400",
  },
  attention: {
    icon: CircleAlert,
    className: "border-amber-500/40 bg-amber-500/10 text-amber-700 dark:text-amber-400",
  },
  maintenance: {
    icon: TriangleAlert,
    className: "border-destructive/40 bg-destructive/10 text-destructive",
  },
}

const kwhOrDash = (wh: number | null) => (wh === null ? "—" : formatKwh(wh))

export function PlantOverviewSection({ systemId }: { systemId: string }) {
  const [overview, setOverview] = useState<EnergyOverview | null>(null)
  const [period, setPeriod] = useState<EnergyPeriod>("week")
  const [series, setSeries] = useState<{ period: EnergyPeriod; buckets: EnergyBucket[] } | null>(null)

  useEffect(() => {
    let cancelled = false
    function load() {
      getEnergyOverview(systemId).then((o) => {
        if (!cancelled) setOverview(o)
      })
    }
    load()
    const interval = setInterval(load, REFRESH_MS)
    return () => {
      cancelled = true
      clearInterval(interval)
    }
  }, [systemId])

  useEffect(() => {
    let cancelled = false
    function load() {
      listEnergySeries(systemId, period).then((buckets) => {
        if (!cancelled) setSeries({ period, buckets })
      })
    }
    load()
    const interval = setInterval(load, REFRESH_MS)
    return () => {
      cancelled = true
      clearInterval(interval)
    }
  }, [systemId, period])

  const chartRows = useMemo(
    () =>
      series
        ? shownBuckets(series.buckets, series.period, new Date()).map((b) => ({
            label: bucketLabel(b.start, series.period),
            real: b.realWh === null ? null : roundKwh(b.realWh, 1),
            expected: b.expectedWh === null ? null : roundKwh(b.expectedWh, 1),
          }))
        : [],
    [series],
  )

  if (overview === null) return null

  const { month } = overview
  const monthName = format(month.start, "MMMM", { locale: ptBR })
  const typicalRange =
    month.typicalLowWh !== null && month.typicalHighWh !== null
      ? ` · típico: ${Math.round(month.typicalLowWh / 1000).toLocaleString("pt-BR")} a ${formatKwh(month.typicalHighWh)}`
      : ""

  return (
    <div className="space-y-4 rounded-xl border-2 border-primary/20 bg-primary/5 p-4">
      <HealthBanner health={overview.health} />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard icon={Zap} label="Gerado hoje" value={kwhOrDash(overview.generatedTodayWh)} hint="até agora" />
        <StatCard
          icon={CalendarClock}
          label="Restante de hoje"
          value={kwhOrDash(overview.remainingTodayWh)}
          hint="previsão até o fim do dia"
        />
        <StatCard
          icon={CalendarDays}
          label={`Amanhã (${format(addDays(new Date(), 1), "EEEE", { locale: ptBR })})`}
          value={kwhOrDash(overview.tomorrowWh)}
          hint="previsão"
        />
        {month.projectedWh !== null ? (
          <StatCard
            icon={CalendarRange}
            label={`${capitalize(monthName)} deve fechar em`}
            value={`~${formatKwh(month.projectedWh)}`}
            hint={`${formatKwh(month.generatedWh)} até agora${typicalRange}`}
          />
        ) : (
          <StatCard icon={CalendarRange} label={`Gerado em ${monthName}`} value={formatKwh(month.generatedWh)} hint="até agora" />
        )}
      </div>

      <div className="rounded-lg border bg-background p-4">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <p className="text-sm font-medium">Previsto × real</p>
          <div className="flex gap-1" role="group" aria-label="Período">
            {energyPeriodOptions.map((option) => (
              <Button
                key={option.value}
                size="sm"
                variant={option.value === period ? "default" : "outline"}
                aria-pressed={option.value === period}
                onClick={() => setPeriod(option.value)}
              >
                {option.label}
              </Button>
            ))}
          </div>
        </div>
        <ChartContainer config={chartConfig} className="h-[240px] w-full">
          <LineChart data={chartRows} margin={{ left: 12, right: 12, top: 8 }}>
            <CartesianGrid vertical={false} />
            <XAxis dataKey="label" tickLine={false} axisLine={false} tickMargin={8} minTickGap={24} />
            <YAxis tickLine={false} axisLine={false} tickMargin={8} width={64} unit=" kWh" tickFormatter={kwhTick} />
            <ChartTooltip content={<ChartTooltipContent />} />
            <ChartLegend content={<ChartLegendContent />} />
            <Line dataKey="expected" type="monotone" stroke="var(--color-expected)" strokeDasharray="4 4" dot={false} connectNulls={false} isAnimationActive={false} />
            <Line dataKey="real" type="monotone" stroke="var(--color-real)" strokeWidth={2} dot={{ r: 2 }} connectNulls={false} isAnimationActive={false} />
          </LineChart>
        </ChartContainer>
        <p className="mt-2 text-xs text-muted-foreground">
          Previsto é o que a usina deveria gerar com o clima de cada período. Para os dias à frente vem da previsão do
          tempo e, além do alcance dela, do que a época do ano costuma render. O dia e o mês em andamento entram no
          real quando fecham.
        </p>
      </div>
    </div>
  )
}

function HealthBanner({ health }: { health: PlantHealth | null }) {
  if (health === null) {
    return (
      <div className="rounded-lg border border-dashed bg-background p-4 text-sm text-muted-foreground">
        Ainda não há horas suficientes de geração para avaliar a usina.
      </div>
    )
  }
  const { icon: Icon, className } = healthStyle[health.state]
  const { title, advice } = healthCopy[health.state]
  return (
    <div className={`flex items-start gap-3 rounded-lg border p-4 ${className}`}>
      <Icon className="mt-0.5 size-5 shrink-0" />
      <div>
        <p className="font-semibold">{title}</p>
        <p className="text-sm text-foreground">
          Últimos {health.days} dias: {health.performancePct}% do previsto para o clima que fez ({formatKwh(health.realWh)}{" "}
          de {formatKwh(health.expectedWh)}).{advice && ` ${advice}`}
        </p>
      </div>
    </div>
  )
}

function capitalize(text: string): string {
  return text.charAt(0).toUpperCase() + text.slice(1)
}
