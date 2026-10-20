import { apiFetch } from "./api"
import type { NewSystemInput, PVSystem } from "@/types"

interface PVSystemResponse {
  id: string
  name: string
  location: string
  installed_power_kw: number
  inverter_type: PVSystem["inverterType"]
  status: PVSystem["status"]
  training_started_at: string
  photo_url: string | null
  device_id: string | null
  weather_station_id: string | null
  last_reading_at: string | null
}

function toPVSystem(response: PVSystemResponse): PVSystem {
  return {
    id: response.id,
    name: response.name,
    location: response.location,
    installedPowerKw: response.installed_power_kw,
    inverterType: response.inverter_type,
    status: response.status,
    trainingStartedAt: response.training_started_at,
    photoUrl: response.photo_url ?? undefined,
    deviceId: response.device_id,
    weatherStationId: response.weather_station_id,
    lastReadingAt: response.last_reading_at,
  }
}

function toRequestBody(input: NewSystemInput) {
  return {
    name: input.name,
    location: input.location,
    installed_power_kw: input.installedPowerKw,
    inverter_type: input.inverterType,
    photo_url: input.photoUrl ?? null,
  }
}

export async function listSystems(): Promise<PVSystem[]> {
  const response = await apiFetch<PVSystemResponse[]>("/systems")
  return response.map(toPVSystem)
}

export async function getSystem(id: string): Promise<PVSystem> {
  const response = await apiFetch<PVSystemResponse>(`/systems/${id}`)
  return toPVSystem(response)
}

export async function createSystem(input: NewSystemInput): Promise<PVSystem> {
  const response = await apiFetch<PVSystemResponse>("/systems", {
    method: "POST",
    body: JSON.stringify(toRequestBody(input)),
  })
  return toPVSystem(response)
}

export async function updateSystem(id: string, input: NewSystemInput): Promise<PVSystem> {
  const response = await apiFetch<PVSystemResponse>(`/systems/${id}`, {
    method: "PATCH",
    body: JSON.stringify(toRequestBody(input)),
  })
  return toPVSystem(response)
}

export async function deleteSystem(id: string): Promise<void> {
  await apiFetch<void>(`/systems/${id}`, { method: "DELETE" })
}

export async function linkDevice(systemId: string, deviceId: string): Promise<PVSystem> {
  const response = await apiFetch<PVSystemResponse>(`/systems/${systemId}/device`, {
    method: "PUT",
    body: JSON.stringify({ device_id: deviceId }),
  })
  return toPVSystem(response)
}

export async function unlinkDevice(systemId: string): Promise<PVSystem> {
  const response = await apiFetch<PVSystemResponse>(`/systems/${systemId}/device`, { method: "DELETE" })
  return toPVSystem(response)
}

export async function startTraining(id: string): Promise<PVSystem> {
  const response = await apiFetch<PVSystemResponse>(`/systems/${id}/start-training`, { method: "POST" })
  return toPVSystem(response)
}
