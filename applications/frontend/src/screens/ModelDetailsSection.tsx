import { useState } from "react"
import { ChevronDown, ChevronRight } from "lucide-react"
import { ExpectedVsRealSection } from "./ExpectedVsRealSection"
import { ForecastSection } from "./ForecastSection"
import { ModelPanelSection } from "./ModelPanelSection"

const OPEN_KEY = "solarsense:model-details-open"

function readOpen(): boolean {
  try {
    return localStorage.getItem(OPEN_KEY) === "1"
  } catch {
    return false
  }
}

export function ModelDetailsSection({ systemId }: { systemId: string }) {
  const [open, setOpen] = useState(readOpen)

  function toggle() {
    const next = !open
    setOpen(next)
    try {
      localStorage.setItem(OPEN_KEY, next ? "1" : "0")
    } catch {
    }
  }

  const Chevron = open ? ChevronDown : ChevronRight
  return (
    <div className="space-y-4">
      <button
        type="button"
        onClick={toggle}
        aria-expanded={open}
        className="flex w-full items-center gap-2 rounded-lg border bg-background px-4 py-3 text-left hover:bg-muted/50"
      >
        <Chevron className="size-4 shrink-0" />
        <span className="text-sm font-medium">Como calculamos isso</span>
        <span className="text-xs text-muted-foreground">o modelo de previsão, sua precisão e a comparação hora a hora</span>
      </button>
      {open && (
        <>
          <ExpectedVsRealSection systemId={systemId} />
          <ForecastSection systemId={systemId} />
          <ModelPanelSection systemId={systemId} />
        </>
      )}
    </div>
  )
}
