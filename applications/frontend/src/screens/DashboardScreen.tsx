import { useEffect, useState, type ComponentType } from "react"
import {
  Activity,
  ArrowLeft,
  Bolt,
  Brain,
  Cable,
  CalendarDays,
  Droplets,
  Gauge,
  ImageIcon,
  Info,
  Lock,
  MapPin,
  Pencil,
  Sun,
  Thermometer,
  TrendingUp,
  Wind,
  Zap,
} from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { isRecentAlert } from "@/lib/alerts"
import { formatMetric } from "@/lib/format"
import {
  formatEnergy,
  formatInverterAge,
  formatPower,
  getInverterStatus,
  getLatestInverterReading,
  inverterStatusLabel,
  isInverterReadingStale,
} from "@/lib/inverter"
import { getLatestReading, getMlMetrics, listAlerts } from "@/lib/readings"
import {
  connectionIcon,
  connectionLabel,
  connectionVariant,
  getConnectionState,
  modelLabel,
  modelVariant,
} from "@/lib/systemStatus"
import { formatHourRange, formatNumber, listPlantHours } from "@/lib/plantHourly"
import { formatFreshness, trainingDaysRemaining, trainingProgressPct } from "@/lib/training"
import type {
  CurrentUser,
  InverterMetrics,
  LiveMetrics,
  MLMetrics,
  NewSystemInput,
  OverheatAlert,
  PlantHour,
  PVSystem,
} from "@/types"
import { AlertsPanel } from "./AlertsPanel"
import { EditSystemDialog } from "./EditSystemDialog"
import { LastAlertCard } from "./LastAlertCard"
import { MetricsHistoryTable } from "./MetricsHistoryTable"
import { ModelDetailsSection } from "./ModelDetailsSection"
import { PlantOverviewSection } from "./PlantOverviewSection"
import { PlantHistoryTable } from "./PlantHistoryTable"
import { NotificationBell, type NotificationItem } from "./NotificationBell"
import { UserMenu } from "./UserMenu"

const POLL_INTERVAL_MS = 2000
const INVERTER_POLL_INTERVAL_MS = 30_000

type DashboardTab = "predictions" | "monitoring"

const dashboardTabs: { value: DashboardTab; label: string }[] = [
  { value: "predictions", label: "Predições" },
  { value: "monitoring", label: "Monitoramento" },
]

export function DashboardScreen({
  system,
  user,
  onBack,
  onLogout,
  onUpdateSystem,
  onUnlinkDevice,
  onStartTraining,
}: {
  system: PVSystem
  user: CurrentUser
  onBack: () => void
  onLogout: () => void
  onUpdateSystem: (input: NewSystemInput) => Promise<void>
  onUnlinkDevice: () => Promise<void>
  onStartTraining: () => Promise<void>
}) {
  const [latestReading, setLatestReading] = useState<LiveMetrics | null>(null)
  const [inverterReading, setInverterReading] = useState<InverterMetrics | null>(null)
  const [plantHours, setPlantHours] = useState<PlantHour[]>([])
  const [mlMetrics, setMlMetrics] = useState<MLMetrics | null>(null)
  const [alerts, setAlerts] = useState<OverheatAlert[]>([])
  const [now, setNow] = useState(() => Date.now())
  const [editOpen, setEditOpen] = useState(false)
  const [startingTraining, setStartingTraining] = useState(false)
  const [tab, setTab] = useState<DashboardTab>("predictions")

  useEffect(() => {
    let cancelled = false
    function poll() {
      getLatestReading(system.id).then((reading) => {
        if (!cancelled) setLatestReading(reading)
      })
    }
    poll()
    const interval = setInterval(poll, POLL_INTERVAL_MS)
    return () => {
      cancelled = true
      clearInterval(interval)
    }
  }, [system.id])

  useEffect(() => {
    let cancelled = false
    function poll() {
      getLatestInverterReading(system.id).then((reading) => {
        if (!cancelled) setInverterReading(reading)
      })
    }
    poll()
    const interval = setInterval(poll, INVERTER_POLL_INTERVAL_MS)
    return () => {
      cancelled = true
      clearInterval(interval)
    }
  }, [system.id])

  useEffect(() => {
    if (system.weatherStationId !== null) listPlantHours(system.id).then(setPlantHours)
  }, [system.id, system.weatherStationId])

  useEffect(() => {
    getMlMetrics(system.id).then(setMlMetrics)
  }, [system.id])

  useEffect(() => {
    listAlerts(system.id).then(setAlerts)
  }, [system.id])

  useEffect(() => {
    const clockInterval = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(clockInterval)
  }, [])

  const secondsSinceLastReading = latestReading
    ? Math.floor((now - new Date(latestReading.recordedAt).getTime()) / 1000)
    : null
  const connectionState = getConnectionState(system, secondsSinceLastReading)
  const isStale = connectionState !== "connected"
  const ConnectionIcon = connectionIcon[connectionState]

  const nowDate = new Date(now)
  const isInverterStale = inverterReading ? isInverterReadingStale(inverterReading, nowDate) : false

  const notifications: NotificationItem[] = alerts.slice(0, 5).map((alert) => ({
    id: alert.id,
    timestamp: alert.timestamp,
    title: "Alerta de superaquecimento",
    description: `Painel atingiu ${alert.panelTempC}°C (limite: ${alert.thresholdC}°C)`,
  }))
  const recentNotificationsCount = alerts.filter(isRecentAlert).length

  async function handleStartTraining() {
    setStartingTraining(true)
    try {
      await onStartTraining()
    } finally {
      setStartingTraining(false)
    }
  }

  return (
    <div className="min-h-svh bg-muted/30">
      <header className="border-b bg-background">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="icon" onClick={onBack} aria-label="Voltar para meus sistemas">
              <ArrowLeft />
            </Button>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground text-sm font-semibold">
              S
            </div>
            <div>
              <p className="text-sm font-semibold leading-none">SolarSense</p>
              <p className="text-xs text-muted-foreground">{system.name}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5">
              <Badge variant={connectionVariant[connectionState]} className="gap-1">
                <ConnectionIcon className="size-3" />
                {connectionLabel[connectionState]}
              </Badge>
              <Badge variant={modelVariant[system.status]}>{modelLabel[system.status]}</Badge>
            </div>
            <NotificationBell items={notifications} recentCount={recentNotificationsCount} />
            <UserMenu user={user} onLogout={onLogout} />
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-5xl space-y-6 px-6 py-8">
        <Card>
          <CardContent className="flex items-center gap-4 py-4">
            <div className="flex size-16 shrink-0 items-center justify-center overflow-hidden rounded-lg bg-muted">
              {system.photoUrl ? (
                <img src={system.photoUrl} alt="" className="size-full object-cover" />
              ) : (
                <ImageIcon className="size-6 text-muted-foreground" />
              )}
            </div>
            <div className="min-w-0 flex-1">
              <p className="font-medium">{system.name}</p>
              <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
                <span className="flex items-center gap-1">
                  <MapPin className="size-3.5" /> {system.location}
                </span>
                <span className="flex items-center gap-1">
                  <Bolt className="size-3.5" /> {system.installedPowerKw} kWp
                </span>
                <span>{system.inverterType === "on_grid" ? "On-grid" : "Off-grid"}</span>
              </div>
            </div>
            <Button variant="outline" size="icon" onClick={() => setEditOpen(true)} aria-label="Editar sistema">
              <Pencil className="size-4" />
            </Button>
          </CardContent>
        </Card>

        <EditSystemDialog
          system={system}
          open={editOpen}
          onOpenChange={setEditOpen}
          onSave={async (input) => {
            await onUpdateSystem(input)
            setEditOpen(false)
          }}
          onUnlinkDevice={async () => {
            setEditOpen(false)
            await onUnlinkDevice()
          }}
        />

        {system.status === "online_untrained" && (
          <Card className="border-dashed">
            <CardContent className="flex flex-col items-center gap-4 py-8 text-center sm:flex-row sm:justify-between sm:text-left">
              <div>
                <p className="font-medium">Sistema conectado — nenhum modelo treinado ainda</p>
                <p className="text-sm text-muted-foreground">
                  As leituras já estão sendo coletadas. Inicie o treinamento para começar a acumular dados até o
                  modelo ficar pronto (~1 ano de coleta).
                </p>
              </div>
              <Button onClick={handleStartTraining} disabled={startingTraining}>
                {startingTraining ? "Iniciando..." : "Iniciar treinamento do modelo"}
              </Button>
            </CardContent>
          </Card>
        )}

        {system.status === "training" && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Progresso do treinamento</CardTitle>
              <CardDescription>
                Faltam {trainingDaysRemaining(system)} dias para o modelo ficar disponível.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Progress value={trainingProgressPct(system)} />
              <p className="mt-2 text-xs text-muted-foreground">
                {trainingProgressPct(system)}% do período mínimo de coleta (365 dias)
              </p>
            </CardContent>
          </Card>
        )}

        <div className="flex gap-1 border-b" role="tablist" aria-label="Áreas do sistema">
          {dashboardTabs.map((option) => (
            <button
              key={option.value}
              type="button"
              role="tab"
              aria-selected={option.value === tab}
              onClick={() => setTab(option.value)}
              className={`-mb-px border-b-2 px-4 py-2 text-sm font-medium transition-colors ${
                option.value === tab
                  ? "border-primary text-foreground"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>

        {tab === "predictions" && (
        <div>
          <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold">
            {system.status === "model_active" ? (
              <>
                <Gauge className="size-4" /> Desempenho da usina
              </>
            ) : (
              <>
                <Brain className="size-4" /> Métricas do modelo de ML
              </>
            )}
          </h2>
          {system.status === "model_active" ? (
            <div className="space-y-4">
              <PlantOverviewSection systemId={system.id} />
              <ModelDetailsSection systemId={system.id} />
            </div>
          ) : mlMetrics ? (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3 rounded-xl border-2 border-primary/20 bg-primary/5 p-4">
              <MetricCard
                icon={Gauge}
                label="Eficiência prevista"
                hint="Eficiência que o modelo de ML prevê para o sistema."
                value={`${mlMetrics.predictedEfficiencyPct}%`}
                featured
              />
              <MetricCard
                icon={Zap}
                label="Geração prevista"
                hint="Energia que o modelo de ML prevê que o sistema vai gerar nas próximas 24 horas."
                value={`${mlMetrics.predictedGenerationKwhNextDay} kWh`}
                featured
              />
              <MetricCard icon={Brain} label="Modelo"
                hint="Versão do modelo de ML usado nas previsões." value={mlMetrics.modelVersion} featured />
            </div>
          ) : (
            <Card className="border-dashed">
              <CardContent className="flex items-center gap-3 py-6 text-sm text-muted-foreground">
                <Lock className="size-4 shrink-0" />
                Disponível quando o treinamento do modelo for concluído.
              </CardContent>
            </Card>
          )}
        </div>
        )}

        {tab === "monitoring" && (
        <>
        <div>
          <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
            <h2 className="text-sm font-medium text-muted-foreground">Métricas do sistema</h2>
            {inverterReading && (
              <span className={`text-xs ${isInverterStale ? "text-destructive" : "text-muted-foreground"}`}>
                Última leitura do inversor há {formatInverterAge(inverterReading, nowDate)}
              </span>
            )}
          </div>
          {inverterReading ? (
            <div className={`grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5 ${isInverterStale ? "opacity-50" : ""}`}>
              <MetricCard icon={Zap} label="Potência AC"
                  hint="Potência que o inversor está entregando agora para a rede elétrica. É a geração real do sistema."
                  value={formatPower(inverterReading.powerW)} />
              <MetricCard icon={Cable} label="Potência DC"
                  hint="Potência que os painéis entregam ao inversor, antes da conversão. Fica um pouco acima da AC; a diferença é a perda do inversor."
                  value={formatPower(inverterReading.dcPowerW)} />
              <MetricCard icon={CalendarDays} label="Geração do dia"
                  hint="Energia gerada desde o início do dia. Volta a zero à meia-noite."
                  value={formatEnergy(inverterReading.dailyYieldWh)} />
              <MetricCard icon={TrendingUp} label="Geração total"
                  hint="Energia gerada desde a instalação do inversor. Só aumenta."
                  value={formatEnergy(inverterReading.totalYieldWh)} />
              <MetricCard icon={Activity} label="Status do inversor"
                  hint="Gerando quando o inversor entrega potência; sem geração quando ela é zero (por exemplo, à noite); sem dados recentes quando a última leitura tem mais de 15 minutos."
                  value={inverterStatusLabel[getInverterStatus(inverterReading, nowDate)]} />
            </div>
          ) : (
            <Card className="border-dashed">
              <CardContent className="py-6 text-sm text-muted-foreground">
                Nenhuma leitura do inversor recebida ainda.
              </CardContent>
            </Card>
          )}
        </div>

        {system.weatherStationId !== null ? (
          <EnvironmentSection lastHour={latestReading} />
        ) : (
          <div>
            <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
              <h2 className="text-sm font-medium text-muted-foreground">Métricas coletadas em tempo real</h2>
              {latestReading && (
                <span className={`text-xs ${isStale ? "text-destructive" : "text-muted-foreground"}`}>
                  Última leitura há {formatFreshness(secondsSinceLastReading ?? 0)}
                </span>
              )}
            </div>
            {latestReading ? (
              <div className={`grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5 ${isStale ? "opacity-50" : ""}`}>
                <MetricCard
                  icon={Thermometer}
                  label="Temp. ambiente"
                  hint="Temperatura do ar no local dos painéis. Painéis perdem eficiência quando esquentam."
                  value={formatMetric(latestReading.ambientTempC, " °C")}
                />
                <MetricCard
                  icon={Droplets}
                  label="Umidade ambiente"
                  hint="Umidade relativa do ar. Ajuda a identificar tempo nublado ou chuvoso."
                  value={formatMetric(latestReading.ambientHumidityPct, "%")}
                />
                <MetricCard icon={Sun} label="Irradiância"
                  hint="Estimativa de quanta luz do sol chega ao local, medida por um sensor de luz (LDR): 0% é escuro, 100% é sol pleno. É uma aproximação, não uma medida em W/m²." value={formatMetric(latestReading.irradiance, "%")} />
                <MetricCard icon={Gauge} label="Pressão"
                  hint="Pressão atmosférica. Quedas costumam indicar mudança de tempo, como chuva ou nuvens." value={formatMetric(latestReading.pressureHpa, " hPa")} />
                <MetricCard
                  icon={Wind}
                  label="Partículas"
                  hint="Quantidade de poeira fina no ar (PM2.5), em escala relativa (0–100%). A poeira se acumula nos painéis e reduz a geração."
                  value={formatMetric(latestReading.particulatePct, "%")}
                />
              </div>
            ) : (
              <Card className="border-dashed">
                <CardContent className="py-6 text-sm text-muted-foreground">
                  Nenhuma leitura recebida do dispositivo ainda.
                </CardContent>
              </Card>
            )}
          </div>
        )}

        <LastAlertCard alert={alerts[0] ?? null} />

        {system.weatherStationId !== null ? (
          <PlantHistoryTable hours={plantHours} />
        ) : (
          <MetricsHistoryTable system={system} />
        )}

        <AlertsPanel alerts={alerts} />
        </>
        )}
      </main>
    </div>
  )
}

function MetricCard({
  icon: Icon,
  label,
  hint,
  value,
  featured = false,
}: {
  icon: ComponentType<{ className?: string }>
  label: string
  hint: string
  value: string
  featured?: boolean
}) {
  return (
    <Card className={featured ? "border-primary/30 bg-background shadow-sm" : undefined}>
      <CardContent className="flex items-center gap-3 py-4">
        <div
          className={`flex size-9 shrink-0 items-center justify-center rounded-lg ${featured ? "bg-primary/10" : "bg-muted"}`}
        >
          <Icon className={`size-4 ${featured ? "text-primary" : "text-muted-foreground"}`} />
        </div>
        <div>
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <p>{label}</p>
            <Tooltip>
              <TooltipTrigger asChild>
                <button type="button" aria-label={`O que é ${label}?`} className="hover:text-foreground">
                  <Info className="size-3" />
                </button>
              </TooltipTrigger>
              <TooltipContent>{hint}</TooltipContent>
            </Tooltip>
          </div>
          <p className={`leading-tight font-semibold ${featured ? "text-lg" : "text-base"}`}>{value}</p>
        </div>
      </CardContent>
    </Card>
  )
}

function EnvironmentSection({ lastHour }: { lastHour: LiveMetrics | null }) {
  return (
    <div>
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-sm font-medium text-muted-foreground">Métricas coletadas em tempo real</h2>
        {lastHour && (
          <span className="text-xs text-muted-foreground">
            Última leitura: {formatHourRange(new Date(lastHour.recordedAt))}
          </span>
        )}
      </div>
      {lastHour ? (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          <MetricCard icon={Thermometer} label="Temp. ambiente"
              hint="Temperatura do ar no local dos painéis. Painéis perdem eficiência quando esquentam."
              value={formatMetric(lastHour.ambientTempC, " °C")} />
          <MetricCard icon={Droplets} label="Umidade ambiente"
              hint="Umidade relativa do ar. Ajuda a identificar tempo nublado ou chuvoso."
              value={formatMetric(lastHour.ambientHumidityPct, "%")} />
          <MetricCard icon={Sun} label="Irradiância"
              hint="Quanta energia do sol chega por m² ao local. É a variável que mais explica a geração."
              value={formatNumber(lastHour.irradiance, " W/m²")} />
          <MetricCard icon={Gauge} label="Pressão"
              hint="Pressão atmosférica. Quedas costumam indicar mudança de tempo, como chuva ou nuvens."
              value={formatMetric(lastHour.pressureHpa, " hPa")} />
        </div>
      ) : (
        <Card className="border-dashed">
          <CardContent className="py-6 text-sm text-muted-foreground">
            Nenhuma leitura recebida do dispositivo ainda.
          </CardContent>
        </Card>
      )}
    </div>
  )
}
