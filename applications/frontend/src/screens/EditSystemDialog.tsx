import { useState } from "react"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import type { NewSystemInput, PVSystem } from "@/types"
import { PhotoUploadField } from "./PhotoUploadField"

export function EditSystemDialog({
  system,
  open,
  onOpenChange,
  onSave,
  onUnlinkDevice,
}: {
  system: PVSystem
  open: boolean
  onOpenChange: (open: boolean) => void
  onSave: (input: NewSystemInput) => void
  onUnlinkDevice: () => void
}) {
  const [name, setName] = useState(system.name)
  const [location, setLocation] = useState(system.location)
  const [power, setPower] = useState(String(system.installedPowerKw))
  const [inverterType, setInverterType] = useState(system.inverterType)
  const [photoUrl, setPhotoUrl] = useState(system.photoUrl)

  function handleOpenChange(next: boolean) {
    if (next) {
      setName(system.name)
      setLocation(system.location)
      setPower(String(system.installedPowerKw))
      setInverterType(system.inverterType)
      setPhotoUrl(system.photoUrl)
    }
    onOpenChange(next)
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Editar sistema</DialogTitle>
          <DialogDescription>Atualize as informações cadastrais deste sistema fotovoltaico.</DialogDescription>
        </DialogHeader>
        <form
          className="space-y-4"
          onSubmit={(e) => {
            e.preventDefault()
            onSave({
              name: name || system.name,
              location: location || system.location,
              installedPowerKw: Number(power) || system.installedPowerKw,
              inverterType,
              photoUrl,
            })
          }}
        >
          <PhotoUploadField value={photoUrl} onChange={setPhotoUrl} />
          <div className="space-y-2">
            <Label htmlFor="edit-name">Nome do sistema</Label>
            <Input id="edit-name" value={name} onChange={(e) => setName(e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="edit-location">Localização</Label>
            <Input id="edit-location" value={location} onChange={(e) => setLocation(e.target.value)} />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="edit-power">Potência instalada (kWp)</Label>
              <Input
                id="edit-power"
                type="number"
                step="0.1"
                value={power}
                onChange={(e) => setPower(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label>Tipo de instalação</Label>
              <Select
                value={inverterType}
                onValueChange={(v) => setInverterType(v as NewSystemInput["inverterType"])}
              >
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="on_grid">On-grid (com inversor)</SelectItem>
                  <SelectItem value="off_grid">Off-grid (com bateria)</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          {system.deviceId && (
            <div className="flex items-center justify-between gap-3 rounded-lg border p-3">
              <div className="text-sm">
                <p className="font-medium">Dispositivo SolarSense-{system.deviceId.slice(-4)}</p>
                <p className="text-xs text-muted-foreground">
                  Desvincule para trocar o ESP32. As leituras antigas continuam no sistema.
                </p>
              </div>
              <Button type="button" variant="outline" size="sm" onClick={onUnlinkDevice}>
                Desvincular
              </Button>
            </div>
          )}
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => handleOpenChange(false)}>
              Cancelar
            </Button>
            <Button type="submit">Salvar alterações</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
