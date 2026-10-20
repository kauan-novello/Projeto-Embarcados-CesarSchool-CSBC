import { Wifi, WifiOff, type LucideIcon } from "lucide-react"
import type { PVSystem, SystemStatus } from "@/types"

type BadgeVariant = "default" | "secondary" | "outline" | "destructive" | "success"

export type ConnectionState = "no_device" | "disconnected" | "connected"

export const OFFLINE_THRESHOLD_SECONDS = 60
export const HOURLY_OFFLINE_THRESHOLD_SECONDS = 2.5 * 3600

export function getConnectionState(
  system: PVSystem,
  secondsSinceLastReading: number | null,
): ConnectionState {
  if (system.deviceId === null) return "no_device"
  const threshold = system.weatherStationId === null ? OFFLINE_THRESHOLD_SECONDS : HOURLY_OFFLINE_THRESHOLD_SECONDS
  if (secondsSinceLastReading === null || secondsSinceLastReading > threshold) {
    return "disconnected"
  }
  return "connected"
}

export const connectionLabel: Record<ConnectionState, string> = {
  no_device: "Sem dispositivo",
  disconnected: "Sem sinal",
  connected: "Online",
}

export const connectionVariant: Record<ConnectionState, BadgeVariant> = {
  no_device: "secondary",
  disconnected: "destructive",
  connected: "success",
}

export const connectionIcon: Record<ConnectionState, LucideIcon> = {
  no_device: WifiOff,
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
