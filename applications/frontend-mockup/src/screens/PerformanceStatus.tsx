import { useMemo, type ComponentType } from "react"
import { Minus, TrendingDown, TrendingUp } from "lucide-react"
import { generateHistoricalReadings } from "@/lib/history"
import { computePerformance } from "@/lib/performance"
import type { PVSystem } from "@/types"

interface StatusStyle {
  color: string
  bg: string
  icon: ComponentType<{ className?: string }>
  text: string
}

function statusFor(pct: number): StatusStyle {
  if (pct >= 105) {
    return { color: "text-emerald-600 dark:text-emerald-400", bg: "bg-emerald-500/10", icon: TrendingUp, text: "acima do previsto" }
  }
  if (pct < 95) {
    return { color: "text-destructive", bg: "bg-destructive/10", icon: TrendingDown, text: "abaixo do previsto" }
  }
  return { color: "text-muted-foreground", bg: "bg-muted", icon: Minus, text: "dentro do esperado" }
}

export function PerformanceStatus({ system }: { system: PVSystem }) {
  const stats = useMemo(() => {
    const readings = generateHistoricalReadings(system, 8)
    return [computePerformance(readings, 1, "Hoje"), computePerformance(readings, 7, "Esta semana")]
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [system.id])

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
      {stats.map((stat) => {
        const status = statusFor(stat.pct)
        const Icon = status.icon
        return (
          <div key={stat.label} className={`flex items-center justify-between rounded-lg p-4 ${status.bg}`}>
            <div>
              <p className="text-xs text-muted-foreground">{stat.label}</p>
              <p className={`text-2xl font-bold ${status.color}`}>{stat.pct}% do previsto</p>
              <p className="text-xs text-muted-foreground">
                {stat.actualKwh} kWh gerados de {stat.predictedKwh} kWh previstos — {status.text}
              </p>
            </div>
            <Icon className={`size-8 shrink-0 ${status.color}`} />
          </div>
        )
      })}
    </div>
  )
}
