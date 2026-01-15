"use client"

import type React from "react"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/lib/auth-context"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { AlertCircle, Home, Loader2 } from "lucide-react"

type AuthMode = "login" | "register"

interface FormErrors {
  username?: string
  email?: string
  password?: string
  general?: string
}

function validatePassword(password: string): string | undefined {
  if (password.length < 8) {
    return "Le mot de passe doit contenir au moins 8 caractères"
  }
  if (!/[A-Z]/.test(password)) {
    return "Le mot de passe doit contenir au moins une majuscule"
  }
  if (!/[0-9]/.test(password)) {
    return "Le mot de passe doit contenir au moins un chiffre"
  }
  return undefined
}

export default function LoginPage() {
  const [mode, setMode] = useState<AuthMode>("login")
  const [username, setUsername] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [errors, setErrors] = useState<FormErrors>({})
  const [isLoading, setIsLoading] = useState(false)

  const { login, register } = useAuth()
  const router = useRouter()

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {}

    if (!username.trim()) {
      newErrors.username = "Le nom d'utilisateur est requis"
    }

    if (mode === "register") {
      const passwordError = validatePassword(password)
      if (passwordError) {
        newErrors.password = passwordError
      }
    } else if (!password) {
      newErrors.password = "Le mot de passe est requis"
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validateForm()) return

    setIsLoading(true)
    setErrors({})

    try {
      let result: { success: boolean; error?: string }

      if (mode === "login") {
        result = await login(username, password)
      } else {
        result = await register({ username, email: email || undefined, password })
      }

      if (result.success) {
        router.push("/dashboard")
      } else {
        setErrors({ general: result.error || "Une erreur est survenue" })
      }
    } catch {
      setErrors({ general: "Erreur de connexion au serveur" })
    } finally {
      setIsLoading(false)
    }
  }

  const switchMode = () => {
    setMode(mode === "login" ? "register" : "login")
    setErrors({})
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <Card className="w-full max-w-md shadow-lg">
        <CardHeader className="text-center space-y-4">
          <div className="mx-auto w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
            <Home className="w-8 h-8 text-primary" />
          </div>
          <CardTitle className="text-2xl font-semibold">SmartHome Lite</CardTitle>
          <CardDescription>
            {mode === "login" ? "Connectez-vous à votre système domotique" : "Créez votre compte SmartHome"}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {errors.general && (
              <div className="flex items-center gap-2 p-3 rounded-lg bg-destructive/10 text-destructive text-sm">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{errors.general}</span>
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="username">Nom d&apos;utilisateur</Label>
              <Input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Entrez votre nom d'utilisateur"
                disabled={isLoading}
                className={errors.username ? "border-destructive" : ""}
              />
              {errors.username && <p className="text-sm text-destructive">{errors.username}</p>}
            </div>

            {mode === "register" && (
              <div className="space-y-2">
                <Label htmlFor="email">
                  Email <span className="text-muted-foreground">(optionnel)</span>
                </Label>
                <Input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Entrez votre email"
                  disabled={isLoading}
                />
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="password">Mot de passe</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Entrez votre mot de passe"
                disabled={isLoading}
                className={errors.password ? "border-destructive" : ""}
              />
              {errors.password && <p className="text-sm text-destructive">{errors.password}</p>}
              {mode === "register" && !errors.password && (
                <p className="text-xs text-muted-foreground">Min. 8 caractères, 1 majuscule, 1 chiffre</p>
              )}
            </div>

            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  {mode === "login" ? "Connexion..." : "Inscription..."}
                </>
              ) : mode === "login" ? (
                "Se connecter"
              ) : (
                "S'inscrire"
              )}
            </Button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-muted-foreground">
              {mode === "login" ? "Pas encore de compte ?" : "Déjà un compte ?"}
              <button
                type="button"
                onClick={switchMode}
                className="ml-1 text-primary hover:underline font-medium"
                disabled={isLoading}
              >
                {mode === "login" ? "S'inscrire" : "Se connecter"}
              </button>
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
