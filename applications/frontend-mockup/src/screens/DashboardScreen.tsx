import { useEffect, useMemo, useState, type ComponentType } from "react"
import {
  ArrowLeft,
  Bolt,
  Brain,
  Droplets,
  Gauge,
  ImageIcon,
  Lock,
  MapPin,
  Pencil,
  Sun,
  Thermometer,
  WifiOff,
  Zap,
} from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  formatFreshness,
  makeLiveMetrics,
  makeMLMetrics,
  trainingDaysRemaining,
  trainingProgressPct,
} from "@/lib/mock"
import { generateAlertHistory, isRecentAlert } from "@/lib/alerts"
import {
  connectionIcon,
  connectionLabel,
  connectionVariant,
  getConnectionState,
  modelLabel,
  modelVariant,
} from "@/lib/systemStatus"
import type { CurrentUser, NewSystemInput, PVSystem, SystemStatus } from "@/types"
import { AlertsPanel } from "./AlertsPanel"
import { EditSystemDialog } from "./EditSystemDialog"
import { LastAlertCard } from "./LastAlertCard"
import { MetricsHistoryTable } from "./MetricsHistoryTable"
import { NotificationBell, type NotificationItem } from "./NotificationBell"
import { PerformanceStatus } from "./PerformanceStatus"
import { UserMenu } from "./UserMenu"

export function DashboardScreen({
  system,
  user,
  onChangeDemoStatus,
  onStartTraining,
  onBack,
  onLogout,
  onUpdateSystem,
  onSetDeviceOnline,
}: {
  system: PVSystem
  user: CurrentUser
  onChangeDemoStatus: (status: SystemStatus) => void
  onStartTraining: () => void
  onBack: () => void
  onLogout: () => void
  onUpdateSystem: (input: NewSystemInput) => void
  onSetDeviceOnline: (online: boolean) => void
}) {
  const [metrics, setMetrics] = useState(makeLiveMetrics())
  const [lastSeenAt, setLastSeenAt] = useState(() => new Date())
  const [, setTick] = useState(0)
  const [editOpen, setEditOpen] = useState(false)
  const mlMetrics = makeMLMetrics()
  const isOffline = !system.deviceOnline

  useEffect(() => {
    const dataInterval = setInterval(() => {
      if (isOffline) return
      setMetrics(makeLiveMetrics())
      setLastSeenAt(new Date())
    }, 4000)
    return () => clearInterval(dataInterval)
  }, [isOffline])

  useEffect(() => {
    const clockInterval = setInterval(() => setTick((t) => t + 1), 1000)
    return () => clearInterval(clockInterval)
  }, [])

  const secondsSinceLastReading = Math.floor((Date.now() - lastSeenAt.getTime()) / 1000)
  const connectionState = getConnectionState(system)
  const ConnectionIcon = connectionIcon[connectionState]

  const systemAlerts = useMemo(
    () => generateAlertHistory(system),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [system.id, system.trainingStartedAt],
  )
  const notifications: NotificationItem[] = systemAlerts.slice(0, 5).map((alert) => ({
    id: alert.id,
    timestamp: alert.timestamp,
    title: "Alerta de superaquecimento",
    description: `Painel atingiu ${alert.panelTempC}°C (limite: ${alert.thresholdC}°C)`,
  }))
  const recentNotificationsCount = systemAlerts.filter(isRecentAlert).length

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
            <Select value={system.status} onValueChange={(v) => onChangeDemoStatus(v as SystemStatus)}>
              <SelectTrigger className="w-[180px] text-xs">
                <SelectValue placeholder="Demo: mudar estado" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="online_untrained">Demo: sem modelo</SelectItem>
                <SelectItem value="training">Demo: treinando</SelectItem>
                <SelectItem value="model_active">Demo: modelo ativo</SelectItem>
              </SelectContent>
            </Select>
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
          onSave={(input) => {
            onUpdateSystem(input)
            setEditOpen(false)
          }}
        />

        {system.status === "online_untrained" && (
          <Card className="border-dashed">
            <CardContent className="flex flex-col items-center gap-4 py-8 text-center sm:flex-row sm:justify-between sm:text-left">
              <div>
                <p className="font-medium">Sistema novo — nenhum modelo treinado ainda</p>
                <p className="text-sm text-muted-foreground">
                  As métricas de coleta já estão disponíveis. Inicie o treinamento para começar a acumular
                  dados até o modelo ficar pronto (~1 ano de coleta).
                </p>
              </div>
              <Button onClick={onStartTraining}>Iniciar treinamento do modelo</Button>
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

        <div>
          <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold">
            <Brain className="size-4" /> Métricas do modelo de ML
          </h2>
          {system.status === "model_active" ? (
            <div className="space-y-4 rounded-xl border-2 border-primary/20 bg-primary/5 p-4">
              <PerformanceStatus system={system} />
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                <MetricCard
                  icon={Gauge}
                  label="Eficiência prevista"
                  value={`${mlMetrics.predictedEfficiencyPct}%`}
                  featured
                />
                <MetricCard
                  icon={Zap}
                  label="Geração prevista (próx. 24h)"
                  value={`${mlMetrics.predictedGenerationKwhNextDay} kWh`}
                  featured
                />
                <MetricCard icon={Brain} label="Modelo" value={mlMetrics.modelVersion} featured />
              </div>
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

        <div>
          <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
            <h2 className="text-sm font-medium text-muted-foreground">Métricas coletadas em tempo real</h2>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1.5 text-xs">
                <span
                  className={`size-2 rounded-full ${isOffline ? "bg-destructive" : "bg-emerald-500"}`}
                  aria-hidden
                />
                {isOffline ? (
                  <span className="flex items-center gap-1 text-destructive">
                    <WifiOff className="size-3.5" /> Dispositivo offline — sem dados há{" "}
                    {formatFreshness(secondsSinceLastReading)}
                  </span>
                ) : (
                  <span className="text-muted-foreground">
                    Última leitura há {formatFreshness(secondsSinceLastReading)}
                  </span>
                )}
              </div>
              <Button
                variant="outline"
                size="sm"
                className="h-7 text-xs"
                onClick={() => {
                  const goingOnline = isOffline
                  onSetDeviceOnline(goingOnline)
                  if (goingOnline) {
                    setMetrics(makeLiveMetrics())
                    setLastSeenAt(new Date())
                  }
                }}
              >
                {isOffline ? "Reconectar dispositivo" : "Demo: simular desconexão"}
              </Button>
            </div>
          </div>
          <div className={`grid grid-cols-2 gap-4 sm:grid-cols-4 ${isOffline ? "opacity-50" : ""}`}>
            <MetricCard icon={Zap} label="Potência estimada" value={`${metrics.powerW} W`} />
            <MetricCard icon={Thermometer} label="Temp. do painel" value={`${metrics.panelTempC} °C`} />
            <MetricCard icon={Droplets} label="Umidade ambiente" value={`${metrics.ambientHumidityPct}%`} />
            <MetricCard icon={Sun} label="Irradiância (proxy)" value={`${metrics.irradiance}%`} />
          </div>
        </div>

        <LastAlertCard system={system} />

        <MetricsHistoryTable system={system} />

        <AlertsPanel system={system} />
      </main>
    </div>
  )
}

function MetricCard({
  icon: Icon,
  label,
  value,
  featured = false,
}: {
  icon: ComponentType<{ className?: string }>
  label: string
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
          <p className="text-xs text-muted-foreground">{label}</p>
          <p className={`leading-tight font-semibold ${featured ? "text-lg" : "text-base"}`}>{value}</p>
        </div>
      </CardContent>
    </Card>
  )
}
