import { useMemo } from "react"
import { format } from "date-fns"
import { ptBR } from "date-fns/locale"
import { Flame, Mail } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { generateAlertHistory } from "@/lib/alerts"
import type { PVSystem } from "@/types"

export function AlertsPanel({ system }: { system: PVSystem }) {
  const alerts = useMemo(() => generateAlertHistory(system), [system.id, system.trainingStartedAt])

  return (
    <div>
      <h2 className="mb-3 flex items-center gap-2 text-sm font-medium text-muted-foreground">
        <Flame className="size-4" /> Histórico de alertas
      </h2>
      {alerts.length === 0 ? (
        <Card className="border-dashed">
          <CardContent className="py-6 text-sm text-muted-foreground">
            Nenhum alerta disparado até o momento.
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="divide-y p-0">
            {alerts.map((alert) => (
              <div key={alert.id} className="flex items-center justify-between gap-4 px-4 py-3">
                <div className="flex items-center gap-3">
                  <div className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-destructive/10">
                    <Flame className="size-4 text-destructive" />
                  </div>
                  <div>
                    <p className="text-sm font-medium">
                      Painel atingiu {alert.panelTempC}°C (limite: {alert.thresholdC}°C)
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {format(alert.timestamp, "dd/MM/yyyy 'às' HH:mm", { locale: ptBR })}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-1 text-xs text-muted-foreground">
                  <Mail className="size-3.5" />
                  {alert.emailTo}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
