"use client"

import type React from "react"
import { useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { authService } from "@/lib/services/auth-service"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { AlertCircle, ArrowLeft, CheckCircle2, Loader2, Eye, EyeOff } from "lucide-react"

type Step = "request" | "reset"

interface FormErrors {
  usernameOrEmail?: string
  token?: string
  newPassword?: string
  confirmPassword?: string
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

export default function ForgotPasswordPage() {
  const [step, setStep] = useState<Step>("request")
  const [usernameOrEmail, setUsernameOrEmail] = useState("")
  const [token, setToken] = useState("")
  const [newPassword, setNewPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [errors, setErrors] = useState<FormErrors>({})
  const [isLoading, setIsLoading] = useState(false)
  const [successMessage, setSuccessMessage] = useState("")
  const router = useRouter()

  const handleRequestToken = async (e: React.FormEvent) => {
    e.preventDefault()

    const newErrors: FormErrors = {}
    if (!usernameOrEmail.trim()) {
      newErrors.usernameOrEmail = "Le nom d'utilisateur ou l'email est requis"
    }

    setErrors(newErrors)
    if (Object.keys(newErrors).length > 0) return

    setIsLoading(true)
    setErrors({})
    setSuccessMessage("")

    try {
      const response = await authService.forgotPassword(usernameOrEmail)
      setSuccessMessage(response.message)
      // Extraire le token du message (pour le développement)
      const tokenMatch = response.message.match(/Token: ([^\s]+)/)
      if (tokenMatch) {
        setToken(tokenMatch[1])
        setStep("reset")
      } else {
        // Si pas de token dans le message, on reste sur la page de demande
        // et on affiche un message indiquant de vérifier l'email
        setSuccessMessage("Si un compte existe avec ces identifiants, un token de réinitialisation a été généré.")
      }
    } catch (error) {
      setErrors({
        general: error instanceof Error ? error.message : "Une erreur est survenue",
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault()

    const newErrors: FormErrors = {}

    if (!token.trim()) {
      newErrors.token = "Le token est requis"
    }

    const passwordError = validatePassword(newPassword)
    if (passwordError) {
      newErrors.newPassword = passwordError
    }

    if (newPassword !== confirmPassword) {
      newErrors.confirmPassword = "Les mots de passe ne correspondent pas"
    }

    setErrors(newErrors)
    if (Object.keys(newErrors).length > 0) return

    setIsLoading(true)
    setErrors({})
    setSuccessMessage("")

    try {
      await authService.resetPassword(token, newPassword)
      setSuccessMessage("Mot de passe réinitialisé avec succès ! Redirection...")
      setTimeout(() => {
        router.push("/login")
      }, 2000)
    } catch (error) {
      setErrors({
        general: error instanceof Error ? error.message : "Une erreur est survenue",
      })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <Card className="w-full max-w-md shadow-lg">
        <CardHeader className="text-center space-y-4">
          <CardTitle className="text-2xl font-semibold">Mot de passe oublié</CardTitle>
          <CardDescription>
            {step === "request"
              ? "Entrez votre nom d'utilisateur ou email pour recevoir un token de réinitialisation"
              : "Entrez le token reçu et votre nouveau mot de passe"}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {step === "request" ? (
            <form onSubmit={handleRequestToken} className="space-y-4">
              {errors.general && (
                <div className="flex items-center gap-2 p-3 rounded-lg bg-destructive/10 text-destructive text-sm">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{errors.general}</span>
                </div>
              )}

              {successMessage && (
                <div className="flex items-center gap-2 p-3 rounded-lg bg-green-500/10 text-green-600 dark:text-green-400 text-sm">
                  <CheckCircle2 className="w-4 h-4 shrink-0" />
                  <span>{successMessage}</span>
                </div>
              )}

              <div className="space-y-2">
                <Label htmlFor="usernameOrEmail">Nom d&apos;utilisateur ou Email</Label>
                <Input
                  id="usernameOrEmail"
                  type="text"
                  value={usernameOrEmail}
                  onChange={(e) => setUsernameOrEmail(e.target.value)}
                  placeholder="Entrez votre nom d'utilisateur ou email"
                  disabled={isLoading}
                  className={errors.usernameOrEmail ? "border-destructive" : ""}
                />
                {errors.usernameOrEmail && (
                  <p className="text-sm text-destructive">{errors.usernameOrEmail}</p>
                )}
              </div>

              <Button type="submit" className="w-full" disabled={isLoading}>
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Envoi en cours...
                  </>
                ) : (
                  "Demander un token"
                )}
              </Button>
            </form>
          ) : (
            <form onSubmit={handleResetPassword} className="space-y-4">
              {errors.general && (
                <div className="flex items-center gap-2 p-3 rounded-lg bg-destructive/10 text-destructive text-sm">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{errors.general}</span>
                </div>
              )}

              {successMessage && (
                <div className="flex items-center gap-2 p-3 rounded-lg bg-green-500/10 text-green-600 dark:text-green-400 text-sm">
                  <CheckCircle2 className="w-4 h-4 shrink-0" />
                  <span>{successMessage}</span>
                </div>
              )}

              <div className="space-y-2">
                <Label htmlFor="token">Token de réinitialisation</Label>
                <Input
                  id="token"
                  type="text"
                  value={token}
                  onChange={(e) => setToken(e.target.value)}
                  placeholder="Entrez le token reçu"
                  disabled={isLoading}
                  className={errors.token ? "border-destructive" : ""}
                />
                {errors.token && <p className="text-sm text-destructive">{errors.token}</p>}
              </div>

              <div className="space-y-2">
                <Label htmlFor="newPassword">Nouveau mot de passe</Label>
                <div className="relative">
                  <Input
                    id="newPassword"
                    type={showPassword ? "text" : "password"}
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="Entrez votre nouveau mot de passe"
                    disabled={isLoading}
                    className={errors.newPassword ? "border-destructive pr-10" : "pr-10"}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                    disabled={isLoading}
                    aria-label={showPassword ? "Masquer le mot de passe" : "Afficher le mot de passe"}
                  >
                    {showPassword ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </button>
                </div>
                {errors.newPassword && (
                  <p className="text-sm text-destructive">{errors.newPassword}</p>
                )}
                {!errors.newPassword && (
                  <p className="text-xs text-muted-foreground">Min. 8 caractères, 1 majuscule, 1 chiffre</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="confirmPassword">Confirmer le mot de passe</Label>
                <div className="relative">
                  <Input
                    id="confirmPassword"
                    type={showConfirmPassword ? "text" : "password"}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Confirmez votre nouveau mot de passe"
                    disabled={isLoading}
                    className={errors.confirmPassword ? "border-destructive pr-10" : "pr-10"}
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                    disabled={isLoading}
                    aria-label={showConfirmPassword ? "Masquer le mot de passe" : "Afficher le mot de passe"}
                  >
                    {showConfirmPassword ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </button>
                </div>
                {errors.confirmPassword && (
                  <p className="text-sm text-destructive">{errors.confirmPassword}</p>
                )}
              </div>

              <Button type="submit" className="w-full" disabled={isLoading}>
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Réinitialisation...
                  </>
                ) : (
                  "Réinitialiser le mot de passe"
                )}
              </Button>
            </form>
          )}

          <div className="mt-6 text-center">
            <Link
              href="/login"
              className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              Retour à la connexion
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
