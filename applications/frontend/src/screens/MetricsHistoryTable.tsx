import { useEffect, useMemo, useState } from "react"
import {
  addMilliseconds,
  endOfDay,
  endOfMonth,
  endOfQuarter,
  endOfWeek,
  endOfYear,
  format,
  startOfDay,
  startOfMonth,
  startOfQuarter,
  startOfWeek,
  startOfYear,
  subDays,
  subMonths,
  subQuarters,
  subWeeks,
  subYears,
} from "date-fns"
import { ptBR } from "date-fns/locale"
import { CalendarIcon } from "lucide-react"
import { Area, AreaChart, CartesianGrid, ReferenceArea, XAxis, YAxis } from "recharts"
import type { DateRange } from "react-day-picker"
import { Button } from "@/components/ui/button"
import { Calendar } from "@/components/ui/calendar"
import { ChartContainer, ChartTooltip, ChartTooltipContent, type ChartConfig } from "@/components/ui/chart"
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { formatMetric } from "@/lib/format"
import { groupReadings, toReading, type GroupingLevel, type Reading } from "@/lib/history"
import { listReadings } from "@/lib/readings"
import { seasonColor, seasonLabel, toSeasonBlocks } from "@/lib/seasons"
import type { PVSystem } from "@/types"
import { SeasonLegend } from "./SeasonLegend"

const PAGE_SIZE = 10
const POLL_INTERVAL_MS = 2000

const groupingOptions: { value: GroupingLevel; label: string }[] = [
  { value: "reading", label: "Por leitura" },
  { value: "minute", label: "Por minuto" },
  { value: "hour", label: "Por hora" },
  { value: "day", label: "Por dia" },
  { value: "week", label: "Por semana" },
  { value: "month", label: "Por mês" },
]

type ChartMetric = "ambientTempC"
  | "ambientHumidityPct"
  | "irradiance"
  | "pressureHpa"
  | "particulatePct"

const metricOptions: { value: ChartMetric; label: string }[] = [
  { value: "ambientTempC", label: "Temp. ambiente (°C)" },
  { value: "ambientHumidityPct", label: "Umidade (%)" },
  { value: "irradiance", label: "Irradiância (%)" },
  { value: "pressureHpa", label: "Pressão (hPa)" },
  { value: "particulatePct", label: "Partículas (%)" },
]

export function MetricsHistoryTable({ system }: { system: PVSystem }) {
  const rangePresets = useMemo((): { label: string; getRange: () => DateRange }[] => {
    const today = new Date()
    const weekStartsOn = 1 as const

    return [
      { label: "Hoje", getRange: () => ({ from: today, to: today }) },
      { label: "Ontem", getRange: () => ({ from: subDays(today, 1), to: subDays(today, 1) }) },
      { label: "Esta semana", getRange: () => ({ from: startOfWeek(today, { weekStartsOn }), to: today }) },
      {
        label: "Semana passada",
        getRange: () => {
          const start = startOfWeek(subWeeks(today, 1), { weekStartsOn })
          return { from: start, to: endOfWeek(start, { weekStartsOn }) }
        },
      },
      { label: "Últimos 7 dias", getRange: () => ({ from: subDays(today, 6), to: today }) },
      { label: "Últimos 14 dias", getRange: () => ({ from: subDays(today, 13), to: today }) },
      { label: "Últimos 30 dias", getRange: () => ({ from: subDays(today, 29), to: today }) },
      { label: "Este mês", getRange: () => ({ from: startOfMonth(today), to: today }) },
      {
        label: "Mês passado",
        getRange: () => {
          const lastMonth = subMonths(today, 1)
          return { from: startOfMonth(lastMonth), to: endOfMonth(lastMonth) }
        },
      },
      { label: "Últimos 90 dias", getRange: () => ({ from: subDays(today, 89), to: today }) },
      { label: "Este trimestre", getRange: () => ({ from: startOfQuarter(today), to: today }) },
      {
        label: "Trimestre passado",
        getRange: () => {
          const lastQuarter = subQuarters(today, 1)
          return { from: startOfQuarter(lastQuarter), to: endOfQuarter(lastQuarter) }
        },
      },
      { label: "Últimos 12 meses", getRange: () => ({ from: subMonths(today, 12), to: today }) },
      { label: "Este ano", getRange: () => ({ from: startOfYear(today), to: today }) },
      {
        label: "Ano passado",
        getRange: () => {
          const lastYear = subYears(today, 1)
          return { from: startOfYear(lastYear), to: endOfYear(lastYear) }
        },
      },
      { label: "Desde o início", getRange: () => ({ from: new Date(system.trainingStartedAt), to: today }) },
    ]
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [system.trainingStartedAt])

  const [range, setRange] = useState<DateRange | undefined>({ from: new Date(), to: new Date() })
  const [grouping, setGrouping] = useState<GroupingLevel>("reading")
  const [metric, setMetric] = useState<ChartMetric>("irradiance")
  const chartConfig = useMemo(
    (): ChartConfig => ({
      [metric]: {
        label: metricOptions.find((opt) => opt.value === metric)?.label,
        color: "var(--chart-1)",
      },
    }),
    [metric],
  )
  const [page, setPage] = useState(1)
  const [readings, setReadings] = useState<Reading[]>([])
  const rows = useMemo(() => groupReadings(readings, grouping), [readings, grouping])

  useEffect(() => {
    setReadings([])
    if (!range?.from || !range?.to) return

    const start = startOfDay(range.from)
    const end = endOfDay(range.to)
    let cancelled = false
    let last: Date | null = null
    let inFlight = false

    const fetchNew = async () => {
      if (inFlight) return
      inFlight = true
      const from = last ? addMilliseconds(last, 1) : start
      const fresh = await listReadings(system.id, from, end)
        .then((list) => list.map(toReading))
        .finally(() => {
          inFlight = false
        })
      if (cancelled || fresh.length === 0) return
      last = fresh[fresh.length - 1].timestamp
      setReadings((prev) => [...prev, ...fresh])
    }

    void fetchNew()
    const includesNow = end.getTime() >= Date.now()
    const interval = includesNow ? setInterval(() => void fetchNew(), POLL_INTERVAL_MS) : undefined
    return () => {
      cancelled = true
      clearInterval(interval)
    }
  }, [system.id, range])

  useEffect(() => setPage(1), [range, grouping])

  const handleGroupingChange = (value: GroupingLevel) => {
    setGrouping(value)
    if (value === "reading" || value === "minute") {
      const today = new Date()
      setRange({ from: today, to: today })
    }
  }

  const totalPages = Math.max(1, Math.ceil(rows.length / PAGE_SIZE))
  const currentPage = Math.min(page, totalPages)
  const pageRows = rows.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE)
  const chartRows = useMemo(() => [...rows].reverse(), [rows])

  const seasonBlocks = useMemo(() => toSeasonBlocks(chartRows), [chartRows])

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-sm font-medium text-muted-foreground">Histórico de métricas coletadas</h2>
        <div className="flex flex-wrap items-center gap-2">
          <Popover>
            <PopoverTrigger asChild>
              <Button variant="outline" className="justify-start font-normal">
                <CalendarIcon className="size-4" />
                {range?.from && range?.to
                  ? `${format(range.from, "dd/MM/yyyy")} – ${format(range.to, "dd/MM/yyyy")}`
                  : "Selecionar período"}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0" align="end">
              <div className="flex">
                <div className="flex max-h-[336px] flex-col gap-0.5 overflow-y-auto border-r p-2">
                  {rangePresets.map((preset) => (
                    <Button
                      key={preset.label}
                      variant="ghost"
                      size="sm"
                      className="justify-start font-normal"
                      onClick={() => setRange(preset.getRange())}
                    >
                      {preset.label}
                    </Button>
                  ))}
                </div>
                <Calendar
                  mode="range"
                  selected={range}
                  onSelect={setRange}
                  numberOfMonths={2}
                  locale={ptBR}
                  disabled={{ after: new Date() }}
                />
              </div>
            </PopoverContent>
          </Popover>

          <Select value={metric} onValueChange={(v) => setMetric(v as ChartMetric)}>
            <SelectTrigger className="w-[190px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {metricOptions.map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={grouping} onValueChange={(v) => handleGroupingChange(v as GroupingLevel)}>
            <SelectTrigger className="w-[140px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {groupingOptions.map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="rounded-lg border bg-background p-4">
        <ChartContainer config={chartConfig} className="h-[220px] w-full">
          <AreaChart data={chartRows} margin={{ left: 12, right: 12, top: 16 }}>
            <CartesianGrid vertical={false} />
            <XAxis dataKey="label" tickLine={false} axisLine={false} tickMargin={8} minTickGap={32} />
            <YAxis tickLine={false} axisLine={false} tickMargin={8} width={48} domain={["auto", "auto"]} />
            <ChartTooltip content={<ChartTooltipContent />} />
            {seasonBlocks.map((block) => (
              <ReferenceArea
                key={`${block.season}-${block.x1}`}
                x1={block.x1}
                x2={block.x2}
                fill={seasonColor[block.season]}
                fillOpacity={0.08}
                strokeOpacity={0}
                ifOverflow="extendDomain"
                label={{
                  value: seasonLabel[block.season],
                  position: "insideTop",
                  fontSize: 11,
                  fill: seasonColor[block.season],
                }}
              />
            ))}
            <Area
              dataKey={metric}
              type="monotone"
              fill={`var(--color-${metric})`}
              fillOpacity={0.2}
              stroke={`var(--color-${metric})`}
              connectNulls
            />
          </AreaChart>
        </ChartContainer>
        <SeasonLegend />
      </div>

      <div className="overflow-x-auto rounded-lg border bg-background">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Período</TableHead>
              <TableHead className="text-right">Temp. ambiente</TableHead>
              <TableHead className="text-right">Umidade</TableHead>
              <TableHead className="text-right">Irradiância</TableHead>
              <TableHead className="text-right">Pressão</TableHead>
              <TableHead className="text-right">Partículas</TableHead>
              <TableHead className="text-right">Leituras</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {pageRows.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="h-24 text-center text-sm text-muted-foreground">
                  Nenhum dado coletado no período selecionado.
                </TableCell>
              </TableRow>
            ) : (
              pageRows.map((row) => (
                <TableRow key={row.key}>
                  <TableCell className="font-medium">{row.label}</TableCell>
                  <TableCell className="text-right">{formatMetric(row.ambientTempC, " °C")}</TableCell>
                  <TableCell className="text-right">{formatMetric(row.ambientHumidityPct, "%")}</TableCell>
                  <TableCell className="text-right">{row.irradiance}%</TableCell>
                  <TableCell className="text-right">{formatMetric(row.pressureHpa, " hPa")}</TableCell>
                  <TableCell className="text-right">{formatMetric(row.particulatePct, "%")}</TableCell>
                  <TableCell className="text-right text-muted-foreground">{row.count}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {totalPages > 1 && (
        <Pagination>
          <PaginationContent>
            <PaginationItem>
              <PaginationPrevious
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className={currentPage === 1 ? "pointer-events-none opacity-50" : "cursor-pointer"}
              />
            </PaginationItem>
            <PaginationItem>
              <span className="px-3 text-sm text-muted-foreground">
                Página {currentPage} de {totalPages}
              </span>
            </PaginationItem>
            <PaginationItem>
              <PaginationNext
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                className={currentPage === totalPages ? "pointer-events-none opacity-50" : "cursor-pointer"}
              />
            </PaginationItem>
          </PaginationContent>
        </Pagination>
      )}
    </div>
  )
}
