import { useState } from "react"
import { differenceInSeconds } from "date-fns"
import { Bolt, ImageIcon, MapPin, Pencil, Plus, Trash2 } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import {
  connectionIcon,
  connectionLabel,
  connectionVariant,
  getConnectionState,
  modelLabel,
  modelVariant,
} from "@/lib/systemStatus"
import type { CurrentUser, NewSystemInput, PVSystem } from "@/types"
import { EditSystemDialog } from "./EditSystemDialog"
import { UserMenu } from "./UserMenu"

export function SystemsListScreen({
  systems,
  user,
  onSelectSystem,
  onAddSystem,
  onEditSystem,
  onUnlinkDevice,
  onDeleteSystem,
  onLogout,
}: {
  systems: PVSystem[]
  user: CurrentUser
  onSelectSystem: (id: string) => void
  onAddSystem: () => void
  onEditSystem: (id: string, input: NewSystemInput) => Promise<void>
  onUnlinkDevice: (id: string) => Promise<void>
  onDeleteSystem: (id: string) => Promise<void>
  onLogout: () => void
}) {
  const [editingSystem, setEditingSystem] = useState<PVSystem | null>(null)

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
          <UserMenu user={user} onLogout={onLogout} />
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
              const secondsSinceLastReading = system.lastReadingAt
                ? differenceInSeconds(new Date(), new Date(system.lastReadingAt))
                : null
              const connectionState = getConnectionState(system, secondsSinceLastReading)
              const ConnectionIcon = connectionIcon[connectionState]
              return (
                <Card key={system.id}>
                  <CardContent className="flex items-center justify-between py-4">
                    <div
                      className="flex flex-1 cursor-pointer items-center gap-4"
                      onClick={() => onSelectSystem(system.id)}
                    >
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
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-1 text-muted-foreground">
                      <Button variant="ghost" size="icon" onClick={() => setEditingSystem(system)}>
                        <Pencil className="size-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => {
                          if (confirm(`Remover "${system.name}"? Essa ação não pode ser desfeita.`)) {
                            onDeleteSystem(system.id)
                          }
                        }}
                      >
                        <Trash2 className="size-4" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        )}
      </main>

      {editingSystem && (
        <EditSystemDialog
          system={editingSystem}
          open={editingSystem !== null}
          onOpenChange={(open) => !open && setEditingSystem(null)}
          onSave={async (input) => {
            await onEditSystem(editingSystem.id, input)
            setEditingSystem(null)
          }}
          onUnlinkDevice={async () => {
            await onUnlinkDevice(editingSystem.id)
            setEditingSystem(null)
          }}
        />
      )}
    </div>
  )
}
