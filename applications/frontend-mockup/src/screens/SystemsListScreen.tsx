import { useEffect, useMemo, useState, type ComponentType } from "react"
import { format } from "date-fns"
import { Bolt, Brain, ChevronRight, Flame, Gauge, ImageIcon, MapPin, Plus, Zap } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { generateAlertHistory, getLastAlert, isRecentAlert } from "@/lib/alerts"
import { makeLiveMetrics } from "@/lib/mock"
import {
  connectionIcon,
  connectionLabel,
  connectionVariant,
  getConnectionState,
  modelLabel,
  modelVariant,
} from "@/lib/systemStatus"
import type { CurrentUser, PVSystem } from "@/types"
import { NotificationBell, type NotificationItem } from "./NotificationBell"
import { UserMenu } from "./UserMenu"

export function SystemsListScreen({
  systems,
  user,
  onSelectSystem,
  onAddSystem,
  onLogout,
}: {
  systems: PVSystem[]
  user: CurrentUser
  onSelectSystem: (id: string) => void
  onAddSystem: () => void
  onLogout: () => void
}) {
  const [tick, setTick] = useState(0)

  useEffect(() => {
    const interval = setInterval(() => setTick((t) => t + 1), 5000)
    return () => clearInterval(interval)
  }, [])

  const summary = useMemo(() => {
    const connected = systems.filter((s) => getConnectionState(s) === "connected")
    const currentPowerW = connected.reduce((sum) => sum + makeLiveMetrics().powerW, 0)

    return {
      totalSystems: systems.length,
      totalInstalledKw: Math.round(systems.reduce((sum, s) => sum + s.installedPowerKw, 0) * 10) / 10,
      modelsActive: systems.filter((s) => s.status === "model_active").length,
      currentPowerKw: Math.round((currentPowerW / 1000) * 10) / 10,
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [systems, tick])

  const allAlerts = useMemo(
    () =>
      systems
        .flatMap((system) => generateAlertHistory(system).map((alert) => ({ system, alert })))
        .sort((a, b) => b.alert.timestamp.getTime() - a.alert.timestamp.getTime()),
    [systems],
  )
  const notifications: NotificationItem[] = allAlerts.slice(0, 5).map(({ system, alert }) => ({
    id: alert.id,
    timestamp: alert.timestamp,
    title: `Alerta — ${system.name}`,
    description: `Painel atingiu ${alert.panelTempC}°C (limite: ${alert.thresholdC}°C)`,
  }))
  const recentNotificationsCount = allAlerts.filter(({ alert }) => isRecentAlert(alert)).length

  return (
    <div className="min-h-svh bg-muted/30">
      <header className="border-b bg-background">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground text-sm font-semibold">
              S
            </div>
            <span className="text-sm font-semibold">SolarSense</span>
          </div>
          <div className="flex items-center gap-1">
            <NotificationBell items={notifications} recentCount={recentNotificationsCount} />
            <UserMenu user={user} onLogout={onLogout} />
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-3xl space-y-6 px-6 py-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-semibold">Meus sistemas</h1>
            <p className="text-sm text-muted-foreground">
              {systems.length === 0
                ? "Você ainda não tem nenhum sistema cadastrado."
                : `${systems.length} sistema(s) fotovoltaico(s) cadastrado(s).`}
            </p>
          </div>
          <Button onClick={onAddSystem}>
            <Plus /> Adicionar sistema
          </Button>
        </div>

        {systems.length > 0 && (
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <SummaryCard icon={Bolt} label="Potência instalada" value={`${summary.totalInstalledKw} kWp`} />
            <SummaryCard icon={Zap} label="Geração agora (estimada)" value={`${summary.currentPowerKw} kW`} />
            <SummaryCard icon={Brain} label="Modelos ativos" value={`${summary.modelsActive}`} />
            <SummaryCard icon={Gauge} label="Sistemas cadastrados" value={`${summary.totalSystems}`} />
          </div>
        )}

        {systems.length === 0 ? (
          <Card className="border-dashed">
            <CardContent className="flex flex-col items-center gap-3 py-12 text-center">
              <p className="text-sm text-muted-foreground">
                Cadastre seu primeiro sistema fotovoltaico para começar a monitorar.
              </p>
              <Button onClick={onAddSystem}>
                <Plus /> Cadastrar meu primeiro sistema
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-3">
            {systems.map((system) => {
              const lastAlert = getLastAlert(system)
              const connectionState = getConnectionState(system)
              const ConnectionIcon = connectionIcon[connectionState]
              return (
                <Card
                  key={system.id}
                  className="cursor-pointer transition-colors hover:bg-accent/50"
                  onClick={() => onSelectSystem(system.id)}
                >
                  <CardContent className="flex items-center justify-between py-4">
                    <div className="flex items-center gap-4">
                      <div className="flex size-14 shrink-0 items-center justify-center overflow-hidden rounded-lg bg-muted">
                        {system.photoUrl ? (
                          <img src={system.photoUrl} alt="" className="size-full object-cover" />
                        ) : (
                          <ImageIcon className="size-5 text-muted-foreground" />
                        )}
                      </div>
                      <div className="space-y-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <p className="font-medium">{system.name}</p>
                          <Badge variant={connectionVariant[connectionState]} className="gap-1">
                            <ConnectionIcon className="size-3" />
                            {connectionLabel[connectionState]}
                          </Badge>
                          <Badge variant={modelVariant[system.status]}>{modelLabel[system.status]}</Badge>
                        </div>
                        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
                          <span className="flex items-center gap-1">
                            <MapPin className="size-3.5" /> {system.location}
                          </span>
                          <span className="flex items-center gap-1">
                            <Bolt className="size-3.5" /> {system.installedPowerKw} kWp
                          </span>
                          {lastAlert && (
                            <span
                              className={`flex items-center gap-1 ${isRecentAlert(lastAlert) ? "text-destructive" : ""}`}
                            >
                              <Flame className="size-3.5" /> Último alerta:{" "}
                              {format(lastAlert.timestamp, "dd/MM/yyyy")}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <ChevronRight className="size-4" />
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        )}
      </main>
    </div>
  )
}

function SummaryCard({
  icon: Icon,
  label,
  value,
}: {
  icon: ComponentType<{ className?: string }>
  label: string
  value: string
}) {
  return (
    <Card>
      <CardContent className="flex items-center gap-3 py-4">
        <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-muted">
          <Icon className="size-4 text-muted-foreground" />
        </div>
        <div>
          <p className="text-xs text-muted-foreground">{label}</p>
          <p className="text-base font-semibold leading-tight">{value}</p>
        </div>
      </CardContent>
    </Card>
  )
}
