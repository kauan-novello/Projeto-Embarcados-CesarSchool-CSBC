import { useMemo, useState } from "react"
import { ArrowLeft, Loader2, Wifi, WifiOff } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"

export function PairingScreen({
  systemName,
  onConnected,
  onBack,
}: {
  systemName: string
  onConnected: () => void
  onBack: () => void
}) {
  const [connecting, setConnecting] = useState(false)
  const [connected, setConnected] = useState(false)

  const pairingCode = useMemo(() => {
    const chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    const random = Array.from({ length: 4 }, () => chars[Math.floor(Math.random() * chars.length)]).join("")
    return `SLR-${random}`
  }, [])

  function handleSimulateConnection() {
    setConnecting(true)
    setTimeout(() => {
      setConnecting(false)
      setConnected(true)
    }, 1600)
  }

  return (
    <div className="flex min-h-svh items-center justify-center bg-muted/30 p-6">
      <Card className="w-full max-w-lg">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={onBack}
              aria-label="Voltar para meus sistemas"
              className="-ml-2 size-8"
            >
              <ArrowLeft />
            </Button>
            <CardTitle>Conecte o dispositivo SolarSense</CardTitle>
          </div>
          <CardDescription>
            Pareando dispositivo para <span className="font-medium text-foreground">{systemName}</span>. Ligue o
            ESP32 e insira o código de pareamento exibido no dispositivo.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between rounded-lg border p-4">
            <div>
              <p className="text-sm text-muted-foreground">Código de pareamento</p>
              <p className="font-mono text-2xl font-semibold tracking-widest">{pairingCode}</p>
            </div>
            <Badge variant={connected ? "default" : "secondary"} className="gap-1.5">
              {connected ? <Wifi className="size-3.5" /> : <WifiOff className="size-3.5" />}
              {connected ? "Online" : "Aguardando conexão"}
            </Badge>
          </div>

          <Separator />

          <div className="space-y-3 text-sm text-muted-foreground">
            <p>1. Conecte o ESP32 à energia e à rede Wi-Fi configurada.</p>
            <p>2. O dispositivo publicará este código automaticamente ao se conectar ao broker MQTT.</p>
            <p>3. Assim que o Backend confirmar o primeiro heartbeat, o status muda para "Online".</p>
          </div>

          {!connected ? (
            <Button onClick={handleSimulateConnection} disabled={connecting} className="w-full">
              {connecting ? (
                <>
                  <Loader2 className="animate-spin" /> Procurando dispositivo...
                </>
              ) : (
                "Simular conexão (demo)"
              )}
            </Button>
          ) : (
            <Button onClick={onConnected} className="w-full">
              Continuar para o painel
            </Button>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
