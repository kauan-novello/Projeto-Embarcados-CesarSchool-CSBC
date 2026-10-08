import { Wifi, WifiOff, type LucideIcon } from "lucide-react"
import type { PVSystem, SystemStatus } from "@/types"

type BadgeVariant = "default" | "secondary" | "outline" | "destructive"

export type ConnectionState = "never_connected" | "disconnected" | "connected"

/** Nunca pareado, pareado mas sem dado chegando, ou online recebendo dado. */
export function getConnectionState(system: PVSystem): ConnectionState {
  if (system.status === "awaiting_pairing") return "never_connected"
  if (!system.deviceOnline) return "disconnected"
  return "connected"
}

export const connectionLabel: Record<ConnectionState, string> = {
  never_connected: "Nunca conectado",
  disconnected: "Sem sinal",
  connected: "Online",
}

export const connectionVariant: Record<ConnectionState, BadgeVariant> = {
  never_connected: "secondary",
  disconnected: "destructive",
  connected: "outline",
}

export const connectionIcon: Record<ConnectionState, LucideIcon> = {
  never_connected: WifiOff,
  disconnected: WifiOff,
  connected: Wifi,
}

export const modelLabel: Record<SystemStatus, string> = {
  awaiting_pairing: "Não treinado",
  online_untrained: "Não treinado",
  training: "Treinando",
  model_active: "Treinado",
}

export const modelVariant: Record<SystemStatus, BadgeVariant> = {
  awaiting_pairing: "secondary",
  online_untrained: "secondary",
  training: "outline",
  model_active: "default",
}
