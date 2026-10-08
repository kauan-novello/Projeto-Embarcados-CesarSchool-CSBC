import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { AuthLayout } from "./AuthLayout"

export function LoginScreen({
  onLogin,
  onGoToSignup,
}: {
  onLogin: () => void
  onGoToSignup: () => void
}) {
  return (
    <AuthLayout title="Entrar" description="Acesse o painel do seu sistema fotovoltaico">
      <form
        className="space-y-4"
        onSubmit={(e) => {
          e.preventDefault()
          onLogin()
        }}
      >
        <div className="space-y-2">
          <Label htmlFor="email">E-mail</Label>
          <Input id="email" type="email" placeholder="voce@email.com" defaultValue="cliente@demo.com" />
        </div>
        <div className="space-y-2">
          <Label htmlFor="password">Senha</Label>
          <Input id="password" type="password" placeholder="••••••••" defaultValue="demo1234" />
        </div>
        <Button type="submit" className="w-full">
          Entrar
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
