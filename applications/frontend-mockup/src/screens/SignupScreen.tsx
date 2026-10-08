import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { AuthLayout } from "./AuthLayout"

export function SignupScreen({
  onSignup,
  onGoToLogin,
}: {
  onSignup: () => void
  onGoToLogin: () => void
}) {
  return (
    <AuthLayout title="Criar conta" description="Cadastre seu perfil para monitorar seu sistema fotovoltaico">
      <form
        className="space-y-4"
        onSubmit={(e) => {
          e.preventDefault()
          onSignup()
        }}
      >
        <div className="space-y-2">
          <Label htmlFor="name">Nome completo</Label>
          <Input id="name" placeholder="Seu nome" defaultValue="Cliente Demo" />
        </div>
        <div className="space-y-2">
          <Label htmlFor="signup-email">E-mail</Label>
          <Input id="signup-email" type="email" placeholder="voce@email.com" defaultValue="cliente@demo.com" />
        </div>
        <div className="space-y-2">
          <Label htmlFor="signup-password">Senha</Label>
          <Input id="signup-password" type="password" placeholder="••••••••" defaultValue="demo1234" />
        </div>
        <Button type="submit" className="w-full">
          Criar conta
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
