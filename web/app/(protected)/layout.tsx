"use client"

import type React from "react"
import { useEffect, useState } from "react"
import { useRouter, usePathname } from "next/navigation"
import Link from "next/link"
import { useAuth } from "@/lib/auth-context"
import { LoadingSpinner } from "@/components/loading-spinner"
import { Button } from "@/components/ui/button"
import {
  Home,
  Lightbulb,
  Settings2,
  Brain,
  SunDim,
  Sun,
  Calendar,
  LogOut,
  Menu,
  X,
  Shield,
  Activity,
  Radio,
  BarChart3,
  Cpu,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { useIsAdmin } from "@/hooks/use-is-admin"

/** Navigation principale (utilisateur ou admin : les 3 premiers liens pointent vers la version admin si connecté en admin). */
const navItems = [
  { href: "/dashboard", label: "Tableau de bord", icon: Home },
  { href: "/devices", label: "Appareils", icon: Lightbulb },
  { href: "/rules", label: "Règles", icon: Settings2 },
  { href: "/ai", label: "Intelligence IA", icon: Brain },
  { href: "/smart-dimming", label: "Smart Dimming", icon: SunDim },
  { href: "/events", label: "Événements", icon: Calendar },
]

/** Pages réservées aux admins (sans doublon avec la nav principale : Appareils / Règles / IA y sont déjà). */
const adminNavItems = [
  { href: "/admin", label: "Accueil Administration", icon: Shield },
  { href: "/admin/monitoring", label: "Monitoring", icon: BarChart3 },
  { href: "/admin/raspberry-pis", label: "Raspberry Pi", icon: Cpu },
  { href: "/admin/zwave-sensors", label: "Capteurs Z-Wave", icon: Radio },
  { href: "/admin/presence", label: "Présence (mouvement)", icon: Activity },
  { href: "/admin/light-readings", label: "Luminosité", icon: Sun },
]

/** Pour un admin, les entrées "Appareils", "Règles", "Intelligence IA" pointent vers les pages admin. */
const adminHrefMap: Record<string, string> = {
  "/devices": "/admin/devices",
  "/rules": "/admin/rules",
  "/ai": "/admin/ai",
}

/** True si cette entrée admin doit être considérée comme active pour le pathname actuel. */
function isAdminItemActive(href: string, pathname: string): boolean {
  if (href === "/admin") return pathname === "/admin"
  return pathname === href || pathname.startsWith(href + "/")
}

export default function ProtectedLayout({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading, user, logout, checkAuth } = useAuth()
  const isAdmin = useIsAdmin()
  const router = useRouter()
  const pathname = usePathname()
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/login")
    }
  }, [isLoading, isAuthenticated, router])

  useEffect(() => {
    // Verify auth on mount
    checkAuth()
  }, [checkAuth])

  useEffect(() => {
    // Close sidebar on route change (mobile)
    setIsSidebarOpen(false)
  }, [pathname])

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" text="Chargement..." />
      </div>
    )
  }

  if (!isAuthenticated) {
    return null
  }

  const handleLogout = () => {
    logout()
    router.push("/login")
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Mobile Header */}
      <header className="lg:hidden fixed top-0 left-0 right-0 z-50 h-16 bg-card border-b border-border flex items-center px-4">
        <Button variant="ghost" size="icon" onClick={() => setIsSidebarOpen(!isSidebarOpen)} aria-label="Toggle menu">
          {isSidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </Button>
        <div className="ml-3 flex items-center gap-2">
          <Home className="h-5 w-5 text-primary" />
          <span className="font-semibold">SmartHome</span>
        </div>
      </header>

      {/* Sidebar Overlay (Mobile) */}
      {isSidebarOpen && (
        <div
          className="lg:hidden fixed inset-0 z-40 bg-foreground/20 backdrop-blur-sm"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed top-0 left-0 z-50 h-full w-64 bg-card border-r border-border transition-transform duration-300 lg:translate-x-0",
          isSidebarOpen ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="h-16 flex items-center px-4 border-b border-border">
            <Home className="h-6 w-6 text-primary" />
            <span className="ml-2 text-lg font-semibold">SmartHome Lite</span>
          </div>

          {/* Navigation - Règles visible uniquement pour les admins */}
          <nav className="flex-1 overflow-y-auto p-4 space-y-1">
            {navItems.filter((item) => isAdmin || item.href !== "/rules").map((item) => {
              const Icon = item.icon
              const href = (isAdmin && adminHrefMap[item.href]) ? adminHrefMap[item.href] : item.href
              const isActive = pathname === href
              return (
                <Link
                  key={item.href}
                  href={href}
                  className={cn(
                    "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                    isActive
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:bg-muted hover:text-foreground",
                  )}
                >
                  <Icon className="h-5 w-5" />
                  {item.label}
                </Link>
              )
            })}
            
            {isAdmin && (
              <>
                <div className="my-2 h-px bg-border" />
                <div className="px-3 py-1.5 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Administration
                </div>
                {adminNavItems.map((item) => {
                  const Icon = item.icon
                  const isActive = isAdminItemActive(item.href, pathname)
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={cn(
                        "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                        isActive
                          ? "bg-primary text-primary-foreground"
                          : "text-muted-foreground hover:bg-muted hover:text-foreground",
                      )}
                    >
                      <Icon className="h-5 w-5" />
                      {item.label}
                    </Link>
                  )
                })}
              </>
            )}
          </nav>

          {/* User Section */}
          <div className="p-4 border-t border-border">
            <div className="flex items-center gap-3 px-3 py-2">
              <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                <span className="text-sm font-medium text-primary">{user?.username?.[0]?.toUpperCase() || "U"}</span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{user?.username}</p>
                {user?.email && <p className="text-xs text-muted-foreground truncate">{user.email}</p>}
              </div>
            </div>
            <Button
              variant="ghost"
              className="w-full mt-2 justify-start text-muted-foreground hover:bg-destructive hover:text-white"
              onClick={handleLogout}
            >
              <LogOut className="h-4 w-4 mr-2" />
              Déconnexion
            </Button>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="lg:ml-64 pt-16 lg:pt-0 min-h-screen">
        <div className="p-4 lg:p-6 max-w-7xl mx-auto">{children}</div>
      </main>
    </div>
  )
}
