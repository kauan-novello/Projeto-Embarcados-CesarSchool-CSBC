import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { AuthLayout } from "./AuthLayout"

export function LoginScreen({
  onLogin,
  onGoToSignup,
}: {
  onLogin: (email: string, password: string) => Promise<void>
  onGoToSignup: () => void
}) {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await onLogin(email, password)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível entrar")
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthLayout title="Entrar" description="Acesse o painel do seu sistema fotovoltaico">
      <form className="space-y-4" onSubmit={handleSubmit}>
        <div className="space-y-2">
          <Label htmlFor="email">E-mail</Label>
          <Input
            id="email"
            type="email"
            placeholder="voce@email.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="password">Senha</Label>
          <Input
            id="password"
            type="password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        {error && <p className="text-sm text-destructive">{error}</p>}
        <Button type="submit" className="w-full" disabled={submitting}>
          {submitting ? "Entrando..." : "Entrar"}
        </Button>
      </form>
      <p className="mt-4 text-center text-sm text-muted-foreground">
        Não tem conta?{" "}
        <button type="button" onClick={onGoToSignup} className="text-foreground underline underline-offset-4">
          Cadastre-se
        </button>
      </p>
    </AuthLayout>
  )
}
