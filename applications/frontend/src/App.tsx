import { useEffect, useState } from "react"
import { fetchCurrentUser, login, logout, signup } from "@/lib/auth"
import { createSystem, deleteSystem, listSystems, startTraining, unlinkDevice, updateSystem } from "@/lib/systems"
import { DashboardScreen } from "@/screens/DashboardScreen"
import { LoginScreen } from "@/screens/LoginScreen"
import { PairingScreen } from "@/screens/PairingScreen"
import { SignupScreen } from "@/screens/SignupScreen"
import { SystemSetupScreen } from "@/screens/SystemSetupScreen"
import { SystemsListScreen } from "@/screens/SystemsListScreen"
import type { CurrentUser, NewSystemInput, PVSystem } from "@/types"

type Screen = "loading" | "login" | "signup" | "systems-list" | "system-setup" | "pairing" | "dashboard"

const LIST_REFRESH_MS = 10_000

export default function App() {
  const [screen, setScreen] = useState<Screen>("loading")
  const [user, setUser] = useState<CurrentUser | null>(null)
  const [systems, setSystems] = useState<PVSystem[]>([])
  const [activeSystemId, setActiveSystemId] = useState<string | null>(null)

  const activeSystem = systems.find((s) => s.id === activeSystemId) ?? null

  useEffect(() => {
    fetchCurrentUser().then((currentUser) => {
      if (currentUser) {
        setUser(currentUser)
        listSystems().then(setSystems)
        setScreen("systems-list")
      } else {
        setScreen("login")
      }
    })
  }, [])

  useEffect(() => {
    if (screen !== "systems-list") return
    const interval = setInterval(() => listSystems().then(setSystems), LIST_REFRESH_MS)
    return () => clearInterval(interval)
  }, [screen])

  async function handleLogin(email: string, password: string) {
    const currentUser = await login(email, password)
    setUser(currentUser)
    setSystems(await listSystems())
    setScreen("systems-list")
  }

  async function handleSignup(name: string, email: string, password: string) {
    const currentUser = await signup(name, email, password)
    setUser(currentUser)
    setSystems(await listSystems())
    setScreen("systems-list")
  }

  async function handleLogout() {
    await logout()
    setUser(null)
    setSystems([])
    setActiveSystemId(null)
    setScreen("login")
  }

  async function handleAddSystem(input: NewSystemInput) {
    const newSystem = await createSystem(input)
    setSystems((prev) => [...prev, newSystem])
    setActiveSystemId(newSystem.id)
    setScreen("pairing")
  }

  async function handleEditSystem(id: string, input: NewSystemInput) {
    const updated = await updateSystem(id, input)
    setSystems((prev) => prev.map((s) => (s.id === id ? updated : s)))
  }

  async function handleUnlinkDevice(id: string) {
    const updated = await unlinkDevice(id)
    setSystems((prev) => prev.map((s) => (s.id === id ? updated : s)))
    if (screen === "dashboard") setScreen("pairing")
  }

  async function handleDeleteSystem(id: string) {
    await deleteSystem(id)
    setSystems((prev) => prev.filter((s) => s.id !== id))
  }

  function handleSelectSystem(id: string) {
    const target = systems.find((s) => s.id === id)
    setActiveSystemId(id)
    const needsPairing = target?.deviceId === null
    setScreen(needsPairing ? "pairing" : "dashboard")
  }

  async function handleStartTraining() {
    if (!activeSystemId) return
    const updated = await startTraining(activeSystemId)
    setSystems((prev) => prev.map((s) => (s.id === updated.id ? updated : s)))
  }

  switch (screen) {
    case "loading":
      return null
    case "login":
      return <LoginScreen onLogin={handleLogin} onGoToSignup={() => setScreen("signup")} />
    case "signup":
      return <SignupScreen onSignup={handleSignup} onGoToLogin={() => setScreen("login")} />
    case "system-setup":
      return <SystemSetupScreen onContinue={handleAddSystem} onCancel={() => setScreen("systems-list")} />
    case "systems-list":
      if (!user) {
        setScreen("login")
        return null
      }
      return (
        <SystemsListScreen
          systems={systems}
          user={user}
          onSelectSystem={handleSelectSystem}
          onAddSystem={() => setScreen("system-setup")}
          onEditSystem={handleEditSystem}
          onUnlinkDevice={handleUnlinkDevice}
          onDeleteSystem={handleDeleteSystem}
          onLogout={handleLogout}
        />
      )
    case "pairing":
      if (!activeSystem) {
        setScreen("systems-list")
        return null
      }
      return (
        <PairingScreen
          system={activeSystem}
          onConnected={(updated) => {
            setSystems((prev) => prev.map((s) => (s.id === updated.id ? updated : s)))
            setScreen("dashboard")
          }}
          onBack={() => setScreen("systems-list")}
        />
      )
    case "dashboard":
      if (!user || !activeSystem) {
        setScreen("systems-list")
        return null
      }
      return (
        <DashboardScreen
          system={activeSystem}
          user={user}
          onBack={() => setScreen("systems-list")}
          onLogout={handleLogout}
          onUpdateSystem={(input) => handleEditSystem(activeSystem.id, input)}
          onUnlinkDevice={() => handleUnlinkDevice(activeSystem.id)}
          onStartTraining={handleStartTraining}
        />
      )
  }
}
