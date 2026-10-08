import { useRef } from "react"
import { ImagePlus } from "lucide-react"
import { Label } from "@/components/ui/label"

export function PhotoUploadField({
  value,
  onChange,
}: {
  value?: string
  onChange: (dataUrl: string) => void
}) {
  const inputRef = useRef<HTMLInputElement>(null)

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = () => {
      if (typeof reader.result === "string") onChange(reader.result)
    }
    reader.readAsDataURL(file)
  }

  return (
    <div className="space-y-2">
      <Label>Foto do sistema</Label>
      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        className="flex h-32 w-full items-center justify-center overflow-hidden rounded-lg border border-dashed bg-muted/40 transition-colors hover:bg-muted/70"
      >
        {value ? (
          <img src={value} alt="Foto do sistema" className="size-full object-cover" />
        ) : (
          <div className="flex flex-col items-center gap-1 text-muted-foreground">
            <ImagePlus className="size-6" />
            <span className="text-xs">Clique para enviar uma foto</span>
          </div>
        )}
      </button>
      <input ref={inputRef} type="file" accept="image/*" className="hidden" onChange={handleFileChange} />
    </div>
  )
}
