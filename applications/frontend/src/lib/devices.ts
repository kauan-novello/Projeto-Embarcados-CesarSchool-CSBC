import { apiFetch } from "./api"
import type { PairableDevice } from "@/types"

interface PairableDeviceResponse {
  id: string
  label: string
  last_seen_at: string
}

export async function listPairableDevices(): Promise<PairableDevice[]> {
  const response = await apiFetch<PairableDeviceResponse[]>("/devices/pairable")
  return response.map((device) => ({ id: device.id, label: device.label, lastSeenAt: device.last_seen_at }))
}
