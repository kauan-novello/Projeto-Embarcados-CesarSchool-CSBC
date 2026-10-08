import { format } from "date-fns"
import { ptBR } from "date-fns/locale"
import { Flame } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { getLastAlert, isRecentAlert } from "@/lib/alerts"
import type { PVSystem } from "@/types"

export function LastAlertCard({ system }: { system: PVSystem }) {
  const alert = getLastAlert(system)
  const isRecent = alert !== null && isRecentAlert(alert)

  return (
    <Card className={isRecent ? "border-destructive/30" : undefined}>
      <CardContent className="flex items-center gap-3 py-4">
        <div
          className={`flex size-9 shrink-0 items-center justify-center rounded-lg ${isRecent ? "bg-destructive/10" : "bg-muted"}`}
        >
          <Flame className={`size-4 ${isRecent ? "text-destructive" : "text-muted-foreground"}`} />
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Último alerta</p>
          {alert ? (
            <p className={`text-sm font-medium ${isRecent ? "" : "text-muted-foreground"}`}>
              Painel atingiu {alert.panelTempC}°C em{" "}
              {format(alert.timestamp, "dd/MM/yyyy 'às' HH:mm", { locale: ptBR })}
            </p>
          ) : (
            <p className="text-sm font-medium text-muted-foreground">Nenhum alerta registrado</p>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
