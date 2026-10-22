import type { LucideIcon } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"

export function StatCard({
  icon: Icon,
  label,
  value,
  hint,
  tone,
}: {
  icon: LucideIcon
  label: string
  value: string
  hint?: string
  tone?: "warn"
}) {
  return (
    <Card className="border-primary/30 bg-background shadow-sm">
      <CardContent className="flex items-center gap-3 py-4">
        <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-primary/10">
          <Icon className="size-4 text-primary" />
        </div>
        <div className="min-w-0">
          <p className="text-xs text-muted-foreground">{label}</p>
          <p className={`text-lg leading-tight font-semibold ${tone === "warn" ? "text-destructive" : ""}`}>{value}</p>
          {hint && <p className="text-xs text-muted-foreground">{hint}</p>}
        </div>
      </CardContent>
    </Card>
  )
}
