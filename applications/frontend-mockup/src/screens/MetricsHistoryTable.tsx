import { useMemo, useState } from "react"
import {
  endOfMonth,
  endOfQuarter,
  endOfWeek,
  endOfYear,
  format,
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
import {
  filterReadingsByRange,
  generateHistoricalReadings,
  groupReadings,
  type GroupingLevel,
} from "@/lib/history"
import { daysSince } from "@/lib/mock"
import { seasonColor, seasonLabel, type Season } from "@/lib/seasons"
import type { PVSystem } from "@/types"

const PAGE_SIZE = 10
const MAX_HISTORY_DAYS = 400

const groupingOptions: { value: GroupingLevel; label: string }[] = [
  { value: "hour", label: "Por hora" },
  { value: "day", label: "Por dia" },
  { value: "week", label: "Por semana" },
  { value: "month", label: "Por mês" },
]

const chartConfig = {
  powerW: {
    label: "Potência média (W)",
    color: "var(--chart-1)",
  },
  predictedPowerW: {
    label: "Previsto pelo modelo (W)",
    color: "var(--chart-3)",
  },
} satisfies ChartConfig

export function MetricsHistoryTable({ system }: { system: PVSystem }) {
  const historyDays = Math.min(MAX_HISTORY_DAYS, Math.max(1, daysSince(system.trainingStartedAt)))

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
      { label: "Todo o período", getRange: () => ({ from: subDays(today, historyDays), to: today }) },
    ]
  }, [historyDays])
  const allReadings = useMemo(
    () => generateHistoricalReadings(system, historyDays),
    [system.id, historyDays],
  )

  const [range, setRange] = useState<DateRange | undefined>({
    from: subMonths(new Date(), 12),
    to: new Date(),
  })
  const [grouping, setGrouping] = useState<GroupingLevel>("day")
  const [page, setPage] = useState(1)

  const rows = useMemo(() => {
    if (!range?.from || !range?.to) return []
    const filtered = filterReadingsByRange(allReadings, range.from, range.to)
    return groupReadings(filtered, grouping)
  }, [allReadings, range, grouping])

  const totalPages = Math.max(1, Math.ceil(rows.length / PAGE_SIZE))
  const currentPage = Math.min(page, totalPages)
  const pageRows = rows.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE)
  const chartRows = useMemo(() => [...rows].reverse(), [rows])

  const seasonBlocks = useMemo(() => {
    const blocks: { season: Season; x1: string; x2: string }[] = []
    for (const row of chartRows) {
      const last = blocks[blocks.length - 1]
      if (last && last.season === row.season) {
        last.x2 = row.label
      } else {
        blocks.push({ season: row.season, x1: row.label, x2: row.label })
      }
    }
    return blocks
  }, [chartRows])

  function handleRangeChange(next: DateRange | undefined) {
    setRange(next)
    setPage(1)
  }

  function handleGroupingChange(next: GroupingLevel) {
    setGrouping(next)
    setPage(1)
  }

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
                      onClick={() => handleRangeChange(preset.getRange())}
                    >
                      {preset.label}
                    </Button>
                  ))}
                </div>
                <Calendar
                  mode="range"
                  selected={range}
                  onSelect={handleRangeChange}
                  numberOfMonths={2}
                  locale={ptBR}
                  disabled={{ after: new Date() }}
                />
              </div>
            </PopoverContent>
          </Popover>

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
            <YAxis tickLine={false} axisLine={false} tickMargin={8} width={40} />
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
              dataKey="powerW"
              type="monotone"
              fill="var(--color-powerW)"
              fillOpacity={0.2}
              stroke="var(--color-powerW)"
            />
            {system.status === "model_active" && (
              <Area
                dataKey="predictedPowerW"
                type="monotone"
                fill="none"
                stroke="var(--color-predictedPowerW)"
                strokeDasharray="4 4"
                dot={false}
              />
            )}
          </AreaChart>
        </ChartContainer>
        <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1">
          {(Object.keys(seasonLabel) as Season[]).map((season) => (
            <div key={season} className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <span
                className="size-2 rounded-full"
                style={{ backgroundColor: seasonColor[season] }}
                aria-hidden
              />
              {seasonLabel[season]}
            </div>
          ))}
          {system.status === "model_active" && (
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <span
                className="h-0 w-3 border-t-2 border-dashed"
                style={{ borderColor: "var(--chart-3)" }}
                aria-hidden
              />
              Previsto pelo modelo
            </div>
          )}
        </div>
      </div>

      <div className="overflow-x-auto rounded-lg border bg-background">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Período</TableHead>
              <TableHead className="text-right">Potência média</TableHead>
              <TableHead className="text-right">Temp. painel</TableHead>
              <TableHead className="text-right">Temp. ambiente</TableHead>
              <TableHead className="text-right">Umidade</TableHead>
              <TableHead className="text-right">Irradiância</TableHead>
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
                  <TableCell className="text-right">{row.powerW} W</TableCell>
                  <TableCell className="text-right">{row.panelTempC} °C</TableCell>
                  <TableCell className="text-right">{row.ambientTempC} °C</TableCell>
                  <TableCell className="text-right">{row.ambientHumidityPct}%</TableCell>
                  <TableCell className="text-right">{row.irradiance}%</TableCell>
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
