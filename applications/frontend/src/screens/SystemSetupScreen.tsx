import { useState } from "react"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import type { NewSystemInput } from "@/types"
import { PhotoUploadField } from "./PhotoUploadField"

export function SystemSetupScreen({
  onContinue,
  onCancel,
}: {
  onContinue: (system: NewSystemInput) => void
  onCancel?: () => void
}) {
  const [name, setName] = useState("")
  const [location, setLocation] = useState("")
  const [power, setPower] = useState("4.5")
  const [inverterType, setInverterType] = useState<NewSystemInput["inverterType"]>("on_grid")
  const [photoUrl, setPhotoUrl] = useState<string | undefined>(undefined)

  return (
    <div className="flex min-h-svh items-center justify-center bg-muted/30 p-6">
      <Card className="w-full max-w-lg">
        <CardHeader>
          <CardTitle>Cadastre seu sistema fotovoltaico</CardTitle>
          <CardDescription>
            Essas informações ajudam a contextualizar as leituras coletadas pelo SolarSense.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form
            className="space-y-4"
            onSubmit={(e) => {
              e.preventDefault()
              onContinue({
                name: name || "Novo sistema fotovoltaico",
                location: location || "Não informado",
                installedPowerKw: Number(power) || 0,
                inverterType,
                photoUrl,
              })
            }}
          >
            <PhotoUploadField value={photoUrl} onChange={setPhotoUrl} />
            <div className="space-y-2">
              <Label htmlFor="system-name">Nome do sistema</Label>
              <Input
                id="system-name"
                placeholder="Ex.: Instalação Residencial"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="location">Localização</Label>
              <Input
                id="location"
                placeholder="Cidade, Estado"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="power">Potência instalada (kWp)</Label>
                <Input
                  id="power"
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
            <div className="flex gap-2">
              {onCancel && (
                <Button type="button" variant="outline" className="flex-1" onClick={onCancel}>
                  Cancelar
                </Button>
              )}
              <Button type="submit" className="flex-1">
                Cadastrar sistema
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
