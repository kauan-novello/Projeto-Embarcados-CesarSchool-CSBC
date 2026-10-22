import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { AuthLayout } from "./AuthLayout"

export function SignupScreen({
  onSignup,
  onGoToLogin,
}: {
  onSignup: (name: string, email: string, password: string) => Promise<void>
  onGoToLogin: () => void
}) {
  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await onSignup(name, email, password)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível criar a conta")
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthLayout title="Criar conta" description="Cadastre seu perfil para monitorar seu sistema fotovoltaico">
      <form className="space-y-4" onSubmit={handleSubmit}>
        <div className="space-y-2">
          <Label htmlFor="name">Nome completo</Label>
          <Input id="name" placeholder="Seu nome" value={name} onChange={(e) => setName(e.target.value)} required />
        </div>
        <div className="space-y-2">
          <Label htmlFor="signup-email">E-mail</Label>
          <Input
            id="signup-email"
            type="email"
            placeholder="voce@email.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="signup-password">Senha</Label>
          <Input
            id="signup-password"
            type="password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        {error && <p className="text-sm text-destructive">{error}</p>}
        <Button type="submit" className="w-full" disabled={submitting}>
          {submitting ? "Criando conta..." : "Criar conta"}
        </Button>
      </form>
      <p className="mt-4 text-center text-sm text-muted-foreground">
        Já tem conta?{" "}
        <button type="button" onClick={onGoToLogin} className="text-foreground underline underline-offset-4">
          Entrar
        </button>
      </p>
    </AuthLayout>
  )
}
