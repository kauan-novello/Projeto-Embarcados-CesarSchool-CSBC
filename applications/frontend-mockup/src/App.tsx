import { useState } from "react"
import { DashboardScreen } from "@/screens/DashboardScreen"
import { LoginScreen } from "@/screens/LoginScreen"
import { PairingScreen } from "@/screens/PairingScreen"
import { SignupScreen } from "@/screens/SignupScreen"
import { SystemSetupScreen } from "@/screens/SystemSetupScreen"
import { SystemsListScreen } from "@/screens/SystemsListScreen"
import { DEMO_USER, makeDemoSystems } from "@/lib/mock"
import type { NewSystemInput, PVSystem, SystemStatus } from "@/types"

type Screen = "login" | "signup" | "systems-list" | "system-setup" | "pairing" | "dashboard"

export default function App() {
  const [screen, setScreen] = useState<Screen>("login")
  const [systems, setSystems] = useState<PVSystem[]>(() => makeDemoSystems())
  const [activeSystemId, setActiveSystemId] = useState<string | null>(null)

  const activeSystem = systems.find((s) => s.id === activeSystemId) ?? null

  function handleSelectSystem(id: string) {
    const target = systems.find((s) => s.id === id)
    setActiveSystemId(id)
    setScreen(target?.status === "awaiting_pairing" ? "pairing" : "dashboard")
  }

  function handleAddSystem(input: NewSystemInput) {
    const newSystem: PVSystem = {
      id: crypto.randomUUID(),
      status: "awaiting_pairing",
      trainingStartedAt: new Date().toISOString(),
      deviceOnline: false,
      ...input,
    }
    setSystems((prev) => [...prev, newSystem])
    setActiveSystemId(newSystem.id)
    setScreen("pairing")
  }

  function handleUpdateSystem(input: NewSystemInput) {
    setSystems((prev) => prev.map((s) => (s.id === activeSystemId ? { ...s, ...input } : s)))
  }

  function handlePaired() {
    setSystems((prev) =>
      prev.map((s) =>
        s.id === activeSystemId ? { ...s, status: "online_untrained", deviceOnline: true } : s,
      ),
    )
    setScreen("dashboard")
  }

  function handleSetDeviceOnline(online: boolean) {
    setSystems((prev) => prev.map((s) => (s.id === activeSystemId ? { ...s, deviceOnline: online } : s)))
  }

  function handleChangeDemoStatus(status: SystemStatus) {
    setSystems((prev) => prev.map((s) => (s.id === activeSystemId ? { ...s, status } : s)))
  }

  function handleStartTraining() {
    setSystems((prev) =>
      prev.map((s) =>
        s.id === activeSystemId
          ? { ...s, status: "training", trainingStartedAt: new Date().toISOString() }
          : s,
      ),
    )
  }

  function handleLogout() {
    setActiveSystemId(null)
    setScreen("login")
  }

  switch (screen) {
    case "login":
      return <LoginScreen onLogin={() => setScreen("systems-list")} onGoToSignup={() => setScreen("signup")} />
    case "signup":
      return (
        <SignupScreen onSignup={() => setScreen("systems-list")} onGoToLogin={() => setScreen("login")} />
      )
    case "systems-list":
      return (
        <SystemsListScreen
          systems={systems}
          user={DEMO_USER}
          onSelectSystem={handleSelectSystem}
          onAddSystem={() => setScreen("system-setup")}
          onLogout={handleLogout}
        />
      )
    case "system-setup":
      return (
        <SystemSetupScreen onContinue={handleAddSystem} onCancel={() => setScreen("systems-list")} />
      )
    case "pairing":
      return (
        <PairingScreen
          systemName={activeSystem?.name ?? "novo sistema"}
          onConnected={handlePaired}
          onBack={() => setScreen("systems-list")}
        />
      )
    case "dashboard":
      if (!activeSystem) {
        setScreen("systems-list")
        return null
      }
      return (
        <DashboardScreen
          system={activeSystem}
          user={DEMO_USER}
          onChangeDemoStatus={handleChangeDemoStatus}
          onStartTraining={handleStartTraining}
          onBack={() => setScreen("systems-list")}
          onLogout={handleLogout}
          onUpdateSystem={handleUpdateSystem}
          onSetDeviceOnline={handleSetDeviceOnline}
        />
      )
  }
}
