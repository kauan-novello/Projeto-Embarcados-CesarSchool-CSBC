import { useEffect, useMemo, useState } from "react"
import { addDays, format } from "date-fns"
import { ptBR } from "date-fns/locale"
import { CalendarClock, CalendarDays } from "lucide-react"
import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts"
import { ChartContainer, ChartTooltip, ChartTooltipContent, type ChartConfig } from "@/components/ui/chart"
import { formatNumber, kwhTick, roundKwh } from "@/lib/plantHourly"
import { listForecast, MIN_SUN_HOUR_WH, totalForDay } from "@/lib/predictions"
import type { HourComparison } from "@/types"
import { StatCard } from "./StatCard"

const REFRESH_MS = 15 * 60_000

const chartConfig = {
  expected: { label: "Previsão", color: "var(--primary)" },
} satisfies ChartConfig

export function ForecastSection({ systemId }: { systemId: string }) {
  const [hours, setHours] = useState<HourComparison[] | null>(null)
  const [now, setNow] = useState(() => new Date())

  useEffect(() => {
    let cancelled = false
    function load() {
      const at = new Date()
      listForecast(systemId, at).then((rows) => {
        if (cancelled) return
        setNow(at)
        setHours(rows)
      })
    }
    load()
    const interval = setInterval(load, REFRESH_MS)
    return () => {
      cancelled = true
      clearInterval(interval)
    }
  }, [systemId])

  const chartRows = useMemo(
    () =>
      (hours ?? [])
        .filter((h) => h.expectedWh >= MIN_SUN_HOUR_WH)
        .map((h) => ({ label: format(h.hourStart, "dd/MM HH'h'"), expected: roundKwh(h.expectedWh) })),
    [hours],
  )

  if (hours === null || hours.length === 0) return null

  const tomorrow = addDays(now, 1)
  return (
    <div className="space-y-4 rounded-xl border-2 border-primary/20 bg-primary/5 p-4">
      <p className="text-sm font-medium">Previsão de geração</p>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <StatCard
          icon={CalendarClock}
          label="Restante de hoje"
          value={formatNumber(totalForDay(hours, now) / 1000, " kWh")}
          hint={`a partir das ${format(now, "HH")}h`}
        />
        <StatCard
          icon={CalendarDays}
          label={`Amanhã (${format(tomorrow, "EEEE, dd/MM", { locale: ptBR })})`}
          value={formatNumber(totalForDay(hours, tomorrow) / 1000, " kWh")}
        />
      </div>
      <div className="rounded-lg border bg-background p-4">
        <ChartContainer config={chartConfig} className="h-[200px] w-full">
          <BarChart data={chartRows} margin={{ left: 12, right: 12, top: 8 }}>
            <CartesianGrid vertical={false} />
            <XAxis dataKey="label" tickLine={false} axisLine={false} tickMargin={8} minTickGap={32} />
            <YAxis tickLine={false} axisLine={false} tickMargin={8} width={56} unit=" kWh" tickFormatter={kwhTick} />
            <ChartTooltip content={<ChartTooltipContent />} />
            <Bar dataKey="expected" fill="var(--color-expected)" radius={3} isAnimationActive={false} />
          </BarChart>
        </ChartContainer>
        <p className="mt-2 text-xs text-muted-foreground">
          Energia prevista por hora com sol, a partir da previsão do tempo; atualizada a cada hora.
        </p>
      </div>
    </div>
  )
}
