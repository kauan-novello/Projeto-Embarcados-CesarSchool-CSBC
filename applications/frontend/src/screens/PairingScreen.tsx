import { useEffect, useState } from "react"
import { formatDistanceToNowStrict } from "date-fns"
import { ptBR } from "date-fns/locale"
import { ArrowLeft, Cpu, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { ApiError } from "@/lib/api"
import { listPairableDevices } from "@/lib/devices"
import { linkDevice } from "@/lib/systems"
import type { PairableDevice, PVSystem } from "@/types"

const POLL_INTERVAL_MS = 3000

export function PairingScreen({
  system,
  onConnected,
  onBack,
}: {
  system: PVSystem
  onConnected: (system: PVSystem) => void
  onBack: () => void
}) {
  const [devices, setDevices] = useState<PairableDevice[]>([])
  const [linkingId, setLinkingId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    const refresh = () =>
      listPairableDevices().then((found) => {
        if (!cancelled) setDevices(found)
      })
    void refresh()
    const interval = setInterval(() => void refresh(), POLL_INTERVAL_MS)
    return () => {
      cancelled = true
      clearInterval(interval)
    }
  }, [])

  async function handleLink(device: PairableDevice) {
    setLinkingId(device.id)
    setError(null)
    try {
      onConnected(await linkDevice(system.id, device.id))
    } catch (err) {
      setError(
        err instanceof ApiError && err.status === 404
          ? "Esse dispositivo saiu do modo pareamento. Segure o botão BOOT por 3 s e salve o portal de novo."
          : "Não foi possível vincular o dispositivo. Tente de novo.",
      )
    } finally {
      setLinkingId(null)
    }
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
            Vinculando um ESP32 a <span className="font-medium text-foreground">{system.name}</span>.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <ol className="list-decimal space-y-3 pl-5 text-sm text-muted-foreground">
            <li>
              Ligue o ESP32 na energia. Na primeira vez ele cria uma rede Wi-Fi própria; se ele já foi configurado
              antes, segure o botão BOOT por 3 segundos.
            </li>
            <li>
              No celular, conecte na rede <code>SolarSense-XXXX</code> com a senha <code>solarsense</code>. A página
              de configuração abre sozinha (se não abrir, acesse <code>192.168.4.1</code>).
            </li>
            <li>Escolha o Wi-Fi da instalação, digite a senha e salve. O servidor já vem preenchido.</li>
            <li>
              Em até um minuto o dispositivo aparece abaixo. Confira se o nome é o mesmo da rede que você usou e
              toque em Vincular (ele fica disponível por 10 minutos).
            </li>
          </ol>

          <Separator />

          <div className="space-y-3">
            <p className="text-sm font-medium">Dispositivos encontrados</p>
            {devices.length === 0 ? (
              <div className="flex items-center gap-2 rounded-lg border border-dashed p-4 text-sm text-muted-foreground">
                <Loader2 className="size-4 animate-spin" />
                Procurando dispositivos em modo pareamento...
              </div>
            ) : (
              devices.map((device) => (
                <div key={device.id} className="flex items-center justify-between gap-3 rounded-lg border p-4">
                  <div className="flex items-center gap-3">
                    <Cpu className="size-5 text-muted-foreground" />
                    <div>
                      <p className="font-mono font-semibold">{device.label}</p>
                      <p className="text-xs text-muted-foreground">
                        Visto há {formatDistanceToNowStrict(new Date(device.lastSeenAt), { locale: ptBR })}
                      </p>
                    </div>
                  </div>
                  <Button onClick={() => handleLink(device)} disabled={linkingId !== null}>
                    {linkingId === device.id ? "Vinculando..." : "Vincular"}
                  </Button>
                </div>
              ))
            )}
            {error && <p className="text-sm text-destructive">{error}</p>}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
