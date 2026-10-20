import { apiFetch } from "./api"
import type { CurrentUser } from "@/types"

interface UserResponse {
  name: string
  email: string
}

function toCurrentUser(response: UserResponse): CurrentUser {
  return { name: response.name, email: response.email }
}

export async function signup(name: string, email: string, password: string): Promise<CurrentUser> {
  const response = await apiFetch<UserResponse>("/auth/signup", {
    method: "POST",
    body: JSON.stringify({ name, email, password }),
  })
  return toCurrentUser(response)
}

export async function login(email: string, password: string): Promise<CurrentUser> {
  const response = await apiFetch<UserResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  })
  return toCurrentUser(response)
}

export async function logout(): Promise<void> {
  await apiFetch<void>("/auth/logout", { method: "POST" })
}

export async function fetchCurrentUser(): Promise<CurrentUser | null> {
  try {
    const response = await apiFetch<UserResponse>("/auth/me")
    return toCurrentUser(response)
  } catch {
    return null
  }
}
