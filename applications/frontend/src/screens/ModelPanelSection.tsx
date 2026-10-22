import { useEffect, useMemo, useState } from "react"
import { format } from "date-fns"
import { CalendarCheck, Gauge, Ruler, Trophy } from "lucide-react"
import { Bar, BarChart, CartesianGrid, Line, LineChart, ReferenceLine, XAxis, YAxis } from "recharts"
import { Badge } from "@/components/ui/badge"
import {
  ChartContainer,
  ChartLegend,
  ChartLegendContent,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { getModelReport, modelLabel } from "@/lib/modelReport"
import { kwhTick, roundKwh } from "@/lib/plantHourly"
import type { ModelReport } from "@/types"
import { StatCard } from "./StatCard"

const foldsConfig = {
  train: { label: "Treino", color: "var(--muted-foreground)" },
  validation: { label: "Validação", color: "var(--primary)" },
} satisfies ChartConfig

const kwh = (wh: number, digits = 2) => `${(wh / 1000).toLocaleString("pt-BR", { maximumFractionDigits: digits, minimumFractionDigits: digits })} kWh`
const pct = (value: number) => `${Math.round(value)}%`
const day = (date: Date) => format(date, "dd/MM/yy")

export function ModelPanelSection({ systemId }: { systemId: string }) {
  const [report, setReport] = useState<ModelReport | null>(null)

  useEffect(() => {
    let cancelled = false
    getModelReport(systemId).then((r) => {
      if (!cancelled) setReport(r)
    })
    return () => {
      cancelled = true
    }
  }, [systemId])

  const residualsConfig = useMemo(
    () =>
      ({
        baseline: { label: modelLabel("baseline"), color: "var(--muted-foreground)" },
        champion: { label: report ? modelLabel(report.modelType) : "Campeão", color: "var(--primary)" },
      }) satisfies ChartConfig,
    [report],
  )

  if (report === null) return null

  const champion = report.models.find((m) => m.isChampion)
  const baseline = report.models.find((m) => m.isBaseline)
  if (!champion) return null
  const testGainPct = baseline ? (1 - champion.testRmseWh / baseline.testRmseWh) * 100 : null

  const foldRows = report.championFolds.map((f) => ({
    label: `Fold ${f.fold}`,
    train: roundKwh(f.trainRmseWh),
    validation: roundKwh(f.validationRmseWh),
  }))
  const residualRows = report.residualsByHour.map((h) => ({
    label: `${h.hour}h`,
    baseline: roundKwh(h.baselineWh),
    champion: roundKwh(h.championWh),
  }))

  return (
    <div className="space-y-4 rounded-xl border-2 border-primary/20 bg-primary/5 p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-sm font-medium">
          Modelo em uso: {modelLabel(report.modelType)} <span className="text-muted-foreground">(versão {report.version})</span>
        </p>
        <span className="text-xs text-muted-foreground">
          Treinado em {format(report.trainedAt, "dd/MM/yyyy HH:mm")} · {report.nHours.toLocaleString("pt-BR")} horas ·
          treino {day(report.trainPeriod[0])}–{day(report.trainPeriod[1])} · teste {day(report.testPeriod[0])}–
          {day(report.testPeriod[1])}
        </span>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard icon={Gauge} label="R² no teste" value={champion.testR2.toLocaleString("pt-BR", { maximumFractionDigits: 3 })} hint="variação explicada" />
        <StatCard icon={Ruler} label="Erro por hora (RMSE)" value={kwh(champion.testRmseWh)} hint="no período de teste" />
        <StatCard icon={CalendarCheck} label="Erro no total do dia" value={pct(champion.testDailyMapePct)} hint="MAPE diário no teste" />
        {testGainPct !== null && (
          <StatCard
            icon={Trophy}
            label="Ganho sobre o baseline"
            value={pct(testGainPct)}
            hint={`no teste; ${pct(report.gainOverBaselinePct)} na validação temporal`}
          />
        )}
      </div>

      <div className="rounded-lg border bg-background p-4">
        <p className="mb-1 text-sm font-medium">Comparação dos modelos</p>
        <p className="mb-3 text-xs text-muted-foreground">
          RMSE por hora. O campeão é o de menor erro na validação temporal (TimeSeriesSplit, 5 folds), nunca escolhido pelo
          teste. O baseline físico é radiação × potência instalada × PR ({report.performanceRatio.toLocaleString("pt-BR", { maximumFractionDigits: 2 })}),
          a régua que os modelos precisam vencer.
        </p>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Modelo</TableHead>
              <TableHead className="text-right">Treino</TableHead>
              <TableHead className="text-right">Validação</TableHead>
              <TableHead className="text-right">Teste</TableHead>
              <TableHead className="text-right">R² teste</TableHead>
              <TableHead className="text-right">Erro diário</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {report.models.map((m) => (
              <TableRow key={m.name} className={m.isBaseline ? "text-muted-foreground" : undefined}>
                <TableCell className="font-medium">
                  {modelLabel(m.name)} {m.isChampion && <Badge className="ml-1">Campeão</Badge>}
                </TableCell>
                <TableCell className="text-right">{kwh(m.cvTrainRmseWh)}</TableCell>
                <TableCell className="text-right">
                  {kwh(m.cvRmseWh)} <span className="text-xs text-muted-foreground">± {kwh(m.cvRmseStdWh)}</span>
                </TableCell>
                <TableCell className="text-right">{kwh(m.testRmseWh)}</TableCell>
                <TableCell className="text-right">{m.testR2.toLocaleString("pt-BR", { maximumFractionDigits: 3 })}</TableCell>
                <TableCell className="text-right">{pct(m.testDailyMapePct)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        <p className="mt-2 text-xs text-muted-foreground">
          Treino e validação são a média dos mesmos 5 folds: quanto maior a distância entre eles, mais o modelo decorou o
          treino em vez de generalizar (overfitting). Erro de treino zero é memorização pura.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="rounded-lg border bg-background p-4">
          <p className="mb-1 text-sm font-medium">Treino × validação do campeão</p>
          <p className="mb-2 text-xs text-muted-foreground">RMSE em cada fold, do mais antigo ao mais recente.</p>
          <ChartContainer config={foldsConfig} className="h-[200px] w-full">
            <BarChart data={foldRows} margin={{ left: 12, right: 12, top: 8 }}>
              <CartesianGrid vertical={false} />
              <XAxis dataKey="label" tickLine={false} axisLine={false} tickMargin={8} />
              <YAxis tickLine={false} axisLine={false} tickMargin={8} width={56} unit=" kWh" tickFormatter={kwhTick} />
              <ChartTooltip content={<ChartTooltipContent />} />
              <ChartLegend content={<ChartLegendContent />} />
              <Bar dataKey="train" fill="var(--color-train)" radius={3} isAnimationActive={false} />
              <Bar dataKey="validation" fill="var(--color-validation)" radius={3} isAnimationActive={false} />
            </BarChart>
          </ChartContainer>
        </div>
        <div className="rounded-lg border bg-background p-4">
          <p className="mb-1 text-sm font-medium">Resíduo médio por hora do dia</p>
          <p className="mb-2 text-xs text-muted-foreground">
            Real − previsto no teste: acima de zero o modelo subestima, abaixo superestima.
          </p>
          <ChartContainer config={residualsConfig} className="h-[200px] w-full">
            <LineChart data={residualRows} margin={{ left: 12, right: 12, top: 8 }}>
              <CartesianGrid vertical={false} />
              <XAxis dataKey="label" tickLine={false} axisLine={false} tickMargin={8} />
              <YAxis tickLine={false} axisLine={false} tickMargin={8} width={56} unit=" kWh" tickFormatter={kwhTick} />
              <ReferenceLine y={0} stroke="var(--border)" />
              <ChartTooltip content={<ChartTooltipContent />} />
              <ChartLegend content={<ChartLegendContent />} />
              <Line dataKey="baseline" stroke="var(--color-baseline)" strokeDasharray="4 4" dot={false} isAnimationActive={false} />
              <Line dataKey="champion" stroke="var(--color-champion)" strokeWidth={2} dot={false} isAnimationActive={false} />
            </LineChart>
          </ChartContainer>
        </div>
      </div>
    </div>
  )
}
