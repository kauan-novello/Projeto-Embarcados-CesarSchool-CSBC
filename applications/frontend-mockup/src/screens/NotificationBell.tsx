import { format } from "date-fns"
import { ptBR } from "date-fns/locale"
import { Bell, Flame } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"

export interface NotificationItem {
  id: string
  timestamp: Date
  title: string
  description: string
}

export function NotificationBell({
  items,
  recentCount,
}: {
  items: NotificationItem[]
  recentCount: number
}) {
  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="ghost" size="icon" className="relative" aria-label="Notificações recentes">
          <Bell />
          {recentCount > 0 && (
            <span className="absolute -top-0.5 -right-0.5 flex size-4 items-center justify-center rounded-full bg-destructive text-[10px] font-medium text-white">
              {recentCount > 9 ? "9+" : recentCount}
            </span>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent align="end" className="w-80 p-0">
        <div className="border-b p-3">
          <p className="text-sm font-medium">Notificações</p>
        </div>
        <div className="max-h-80 overflow-y-auto">
          {items.length === 0 ? (
            <p className="p-4 text-center text-sm text-muted-foreground">Nenhuma notificação recente.</p>
          ) : (
            items.map((item) => (
              <div key={item.id} className="flex items-start gap-3 border-b p-3 last:border-b-0">
                <div className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-destructive/10">
                  <Flame className="size-4 text-destructive" />
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-medium">{item.title}</p>
                  <p className="text-xs text-muted-foreground">{item.description}</p>
                  <p className="mt-0.5 text-xs text-muted-foreground">
                    {format(item.timestamp, "dd/MM/yyyy 'às' HH:mm", { locale: ptBR })}
                  </p>
                </div>
              </div>
            ))
          )}
        </div>
      </PopoverContent>
    </Popover>
  )
}
