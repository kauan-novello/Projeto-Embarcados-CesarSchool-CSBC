import { useMemo, useState } from "react"
import { endOfDay, format, startOfDay } from "date-fns"
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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import {
  formatNumber,
  groupPlantHours,
  plantGroupingOptions,
  type PlantGrouping,
  type PlantRow,
} from "@/lib/plantHourly"
import { seasonColor, seasonLabel, toSeasonBlocks } from "@/lib/seasons"
import type { PlantHour } from "@/types"
import { SeasonLegend } from "./SeasonLegend"

const PAGE_SIZE = 10

type ChartMetric = "energyKwh" | "radiationWhM2" | "airTempC" | "humidityPct" | "pressureHpa" | "windSpeedMS"

const metricOptions: { value: ChartMetric; label: string }[] = [
  { value: "energyKwh", label: "Energia gerada (kWh)" },
  { value: "radiationWhM2", label: "Irradiação (Wh/m²)" },
  { value: "airTempC", label: "Temp. ambiente (°C)" },
  { value: "humidityPct", label: "Umidade (%)" },
  { value: "pressureHpa", label: "Pressão (hPa)" },
  { value: "windSpeedMS", label: "Vento (m/s)" },
]

function fullRange(hours: PlantHour[]): DateRange | undefined {
  if (hours.length === 0) return undefined
  return { from: hours[0].hourStart, to: hours[hours.length - 1].hourStart }
}

export function PlantHistoryTable({ hours }: { hours: PlantHour[] }) {
  const dataRange = useMemo(() => fullRange(hours), [hours])
  const [pickedRange, setPickedRange] = useState<DateRange | undefined>()
  const range = pickedRange ?? dataRange
  const [grouping, setGrouping] = useState<PlantGrouping>("hour")
  const [metric, setMetric] = useState<ChartMetric>("energyKwh")
  const [page, setPage] = useState(1)

  const changeRange = (value: DateRange | undefined) => {
    setPickedRange(value)
    setPage(1)
  }
  const changeGrouping = (value: PlantGrouping) => {
    setGrouping(value)
    setPage(1)
  }

  const rows = useMemo((): PlantRow[] => {
    if (!range?.from || !range?.to) return []
    const start = startOfDay(range.from).getTime()
    const end = endOfDay(range.to).getTime()
    const inRange = hours.filter((h) => h.hourStart.getTime() >= start && h.hourStart.getTime() <= end)
    return groupPlantHours(inRange, grouping)
  }, [hours, range, grouping])

  const chartRows = useMemo(() => [...rows].reverse(), [rows])
  const seasonBlocks = useMemo(() => toSeasonBlocks(chartRows), [chartRows])
  const chartConfig = useMemo(
    (): ChartConfig => ({
      [metric]: { label: metricOptions.find((opt) => opt.value === metric)?.label, color: "var(--chart-1)" },
    }),
    [metric],
  )

  const totalPages = Math.max(1, Math.ceil(rows.length / PAGE_SIZE))
  const currentPage = Math.min(page, totalPages)
  const pageRows = rows.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE)

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
              <div className="flex flex-col">
                <Button
                  variant="ghost"
                  size="sm"
                  className="m-2 justify-start font-normal"
                  onClick={() => changeRange(undefined)}
                >
                  Desde o início
                </Button>
                <Calendar
                  mode="range"
                  selected={range}
                  onSelect={changeRange}
                  numberOfMonths={2}
                  locale={ptBR}
                  defaultMonth={range?.to}
                  disabled={dataRange?.from && dataRange?.to ? { before: dataRange.from, after: dataRange.to } : undefined}
                />
              </div>
            </PopoverContent>
          </Popover>

          <Select value={metric} onValueChange={(v) => setMetric(v as ChartMetric)}>
            <SelectTrigger className="w-[200px]">
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

          <Select value={grouping} onValueChange={(v) => changeGrouping(v as PlantGrouping)}>
            <SelectTrigger className="w-[140px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {plantGroupingOptions.map((opt) => (
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
              isAnimationActive={false}
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
              <TableHead className="text-right">Energia</TableHead>
              <TableHead className="text-right">Irradiação</TableHead>
              <TableHead className="text-right">Temp. ambiente</TableHead>
              <TableHead className="text-right">Umidade</TableHead>
              <TableHead className="text-right">Pressão</TableHead>
              <TableHead className="text-right">Vento</TableHead>
              <TableHead className="text-right">Leituras</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {pageRows.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} className="h-24 text-center text-sm text-muted-foreground">
                  Nenhum dado coletado no período selecionado.
                </TableCell>
              </TableRow>
            ) : (
              pageRows.map((row) => (
                <TableRow key={row.key}>
                  <TableCell className="font-medium">{row.label}</TableCell>
                  <TableCell className="text-right">{formatNumber(row.energyKwh, " kWh")}</TableCell>
                  <TableCell className="text-right">{formatNumber(row.radiationWhM2, " Wh/m²")}</TableCell>
                  <TableCell className="text-right">{formatNumber(row.airTempC, " °C")}</TableCell>
                  <TableCell className="text-right">{formatNumber(row.humidityPct, "%")}</TableCell>
                  <TableCell className="text-right">{formatNumber(row.pressureHpa, " hPa")}</TableCell>
                  <TableCell className="text-right">{formatNumber(row.windSpeedMS, " m/s")}</TableCell>
                  <TableCell className="text-right text-muted-foreground">{row.hours}</TableCell>
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
