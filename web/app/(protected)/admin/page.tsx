"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import Link from "next/link"
import { AdminOnly } from "@/components/admin-only"
import { useIsAdmin } from "@/hooks/use-is-admin"
import { useRouter } from "next/navigation"
import { useEffect } from "react"
import {
  Shield,
  Cpu,
  Lightbulb,
  Settings2,
  Brain,
  SunDim,
  ArrowRight,
  Server,
  Radio,
} from "lucide-react"

const adminSections = [
  {
    title: "Gestion Raspberry Pi",
    description: "Gérer les Raspberry Pi connectés, leurs API Keys et leur état",
    href: "/admin/raspberry-pis",
    icon: Cpu,
    color: "text-blue-500",
  },
  {
    title: "Capteurs Z-Wave",
    description: "Données des capteurs Z-Wave (Aeotec MultiSensor 7, mouvement, température, etc.)",
    href: "/admin/zwave-sensors",
    icon: Radio,
    color: "text-cyan-500",
  },
  {
    title: "Gestion Appareils",
    description: "CRUD complet des appareils avec détails techniques (GPIO, RPi ID)",
    href: "/admin/devices",
    icon: Lightbulb,
    color: "text-yellow-500",
  },
  {
    title: "Gestion Règles Avancée",
    description: "Édition JSON, test de règles et métriques d'exécution",
    href: "/admin/rules",
    icon: Settings2,
    color: "text-purple-500",
  },
  {
    title: "Configuration IA",
    description: "Métriques des modèles, classification/prédiction manuelle",
    href: "/admin/ai",
    icon: Brain,
    color: "text-green-500",
  },
]

export default function AdminPage() {
  const isAdmin = useIsAdmin()
  const router = useRouter()

  useEffect(() => {
    if (!isAdmin) {
      router.push("/dashboard")
    }
  }, [isAdmin, router])

  if (!isAdmin) {
    return null
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold text-balance flex items-center gap-2">
          <Shield className="h-6 w-6 text-primary" />
          Administration
        </h1>
        <p className="text-muted-foreground">Gestion technique et configuration avancée du système</p>
      </div>

      {/* Admin Sections Grid */}
      <div className="grid sm:grid-cols-2 gap-4">
        {adminSections.map((section) => {
          const Icon = section.icon
          return (
            <Link key={section.href} href={section.href}>
              <Card className="hover:shadow-lg transition-shadow cursor-pointer h-full">
                <CardHeader>
                  <div className="flex items-center gap-3">
                    <div className={`p-3 rounded-xl bg-muted ${section.color}`}>
                      <Icon className="h-6 w-6" />
                    </div>
                    <div className="flex-1">
                      <CardTitle className="text-lg">{section.title}</CardTitle>
                    </div>
                    <ArrowRight className="h-5 w-5 text-muted-foreground" />
                  </div>
                  <CardDescription>{section.description}</CardDescription>
                </CardHeader>
              </Card>
            </Link>
          )
        })}
      </div>

      {/* Info Card */}
      <Card className="bg-primary/5 border-primary/20">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Server className="h-5 w-5 text-primary" />
            Zone d'administration
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Cette section est réservée aux administrateurs. Vous avez accès à toutes les fonctionnalités techniques
            et de configuration avancée du système SmartHome Lite.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
