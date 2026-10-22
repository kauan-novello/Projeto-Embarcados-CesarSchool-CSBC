import { useEffect, useMemo, useState } from "react"
import { format } from "date-fns"
import { Gauge, Sun, Zap } from "lucide-react"
import { CartesianGrid, Line, LineChart, XAxis, YAxis } from "recharts"
import { Card, CardContent } from "@/components/ui/card"
import { ChartContainer, ChartLegend, ChartLegendContent, ChartTooltip, ChartTooltipContent, type ChartConfig } from "@/components/ui/chart"
import { formatHourRange, formatNumber, kwhTick, roundKwh } from "@/lib/plantHourly"
import { comparedTotals, lastComparedHour, listRecentComparisons, performancePct } from "@/lib/predictions"
import type { HourComparison } from "@/types"
import { StatCard } from "./StatCard"

const REFRESH_MS = 5 * 60_000

const chartConfig = {
  real: { label: "Real", color: "var(--primary)" },
  expected: { label: "Esperado pelo modelo", color: "var(--muted-foreground)" },
} satisfies ChartConfig

export function ExpectedVsRealSection({ systemId }: { systemId: string }) {
  const [hours, setHours] = useState<HourComparison[] | null>(null)

  useEffect(() => {
    let cancelled = false
    function load() {
      listRecentComparisons(systemId, new Date()).then((rows) => {
        if (!cancelled) setHours(rows)
      })
    }
    load()
    const interval = setInterval(load, REFRESH_MS)
    return () => {
      cancelled = true
      clearInterval(interval)
    }
  }, [systemId])

  const last = useMemo(() => (hours ? lastComparedHour(hours) : null), [hours])
  const totals = useMemo(() => comparedTotals(hours ?? []), [hours])
  const chartRows = useMemo(
    () =>
      (hours ?? []).map((h) => ({
        label: format(h.hourStart, "dd/MM HH'h'"),
        real: h.realWh === null ? null : roundKwh(h.realWh),
        expected: roundKwh(h.expectedWh),
      })),
    [hours],
  )

  if (hours === null) return null
  if (hours.length === 0) {
    return (
      <Card className="border-dashed">
        <CardContent className="py-6 text-sm text-muted-foreground">
          O modelo ainda não fez previsões para este sistema.
        </CardContent>
      </Card>
    )
  }

  const lastPerformance = last ? performancePct(last.expectedWh, last.realWh) : null
  const weekPerformance = performancePct(totals.expectedWh, totals.realWh)

  return (
    <div className="space-y-4 rounded-xl border-2 border-primary/20 bg-primary/5 p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-sm font-medium">Geração real × esperada pelo modelo</p>
        {last && (
          <span className="text-xs text-muted-foreground">Última hora com sol: {formatHourRange(last.hourStart)}</span>
        )}
      </div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard icon={Zap} label="Gerado na hora" value={last?.realWh != null ? formatNumber(last.realWh / 1000, " kWh") : "—"} />
        <StatCard icon={Sun} label="Esperado pelo modelo" value={last ? formatNumber(last.expectedWh / 1000, " kWh") : "—"} />
        <StatCard
          icon={Gauge}
          label="Desempenho"
          value={lastPerformance === null ? "—" : `${lastPerformance}%`}
          tone={lastPerformance !== null && lastPerformance < 80 ? "warn" : undefined}
        />
      </div>
      <div className="rounded-lg border bg-background p-4">
        <ChartContainer config={chartConfig} className="h-[220px] w-full">
          <LineChart data={chartRows} margin={{ left: 12, right: 12, top: 8 }}>
            <CartesianGrid vertical={false} />
            <XAxis dataKey="label" tickLine={false} axisLine={false} tickMargin={8} minTickGap={48} />
            <YAxis tickLine={false} axisLine={false} tickMargin={8} width={56} unit=" kWh" tickFormatter={kwhTick} />
            <ChartTooltip content={<ChartTooltipContent />} />
            <ChartLegend content={<ChartLegendContent />} />
            <Line dataKey="expected" type="monotone" stroke="var(--color-expected)" strokeDasharray="4 4" dot={false} isAnimationActive={false} />
            <Line dataKey="real" type="monotone" stroke="var(--color-real)" strokeWidth={2} dot={false} connectNulls={false} isAnimationActive={false} />
          </LineChart>
        </ChartContainer>
        <p className="mt-2 text-xs text-muted-foreground">
          Últimos 7 dias: {formatNumber(totals.realWh / 1000, " kWh")} gerados, {formatNumber(totals.expectedWh / 1000, " kWh")} esperados
          {weekPerformance !== null && ` (desempenho de ${weekPerformance}%)`}.
        </p>
      </div>
    </div>
  )
}
