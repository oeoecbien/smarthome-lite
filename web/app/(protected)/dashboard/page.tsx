"use client"

import { useEffect, useState, useCallback } from "react"
import Link from "next/link"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { LoadingSpinner } from "@/components/loading-spinner"
import { ScenarioChip } from "@/components/scenario-chip"
import { deviceService } from "@/lib/services/device-service"
import { ruleService } from "@/lib/services/rule-service"
import { aiService } from "@/lib/services/ai-service"
import { smartDimmingService } from "@/lib/services/smart-dimming-service"
import { eventService } from "@/lib/services/event-service"
import { formatRelativeTime } from "@/lib/formatters"
import type { Device, Rule, CurrentScenario, SmartDimmingStatus, SystemEvent } from "@/lib/types"
import {
  Lightbulb,
  Settings2,
  Brain,
  SunDim,
  Activity,
  RefreshCw,
  Power,
  ChevronRight,
  AlertCircle,
} from "lucide-react"
import { cn } from "@/lib/utils"

interface DashboardData {
  devices: Device[]
  rules: Rule[]
  scenario: CurrentScenario | null
  smartDimming: SmartDimmingStatus | null
  events: SystemEvent[]
}

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData>({
    devices: [],
    rules: [],
    scenario: null,
    smartDimming: null,
    events: [],
  })
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    try {
      const [devices, rules, scenario, smartDimming, events] = await Promise.all([
        deviceService.getDevices().catch(() => []),
        ruleService.getRules().catch(() => []),
        aiService.getCurrentScenario().catch(() => null),
        smartDimmingService.getStatus().catch(() => null),
        eventService.getEvents(undefined, undefined, undefined, 10).catch(() => []),
      ])

      setData({
        devices: devices.slice(0, 6),
        rules,
        scenario,
        smartDimming,
        events,
      })
      setError(null)
    } catch {
      setError("Erreur lors du chargement des données")
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 5000)
    return () => clearInterval(interval)
  }, [fetchData])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <LoadingSpinner size="lg" text="Chargement du tableau de bord..." />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
        <AlertCircle className="h-12 w-12 text-destructive" />
        <p className="text-muted-foreground">{error}</p>
        <Button onClick={fetchData}>Réessayer</Button>
      </div>
    )
  }

  const activeRules = data.rules.filter((r) => r.enabled).length
  const onlineDevices = data.devices.filter((d) => d.state === "ON").length

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-balance">Tableau de bord</h1>
          <p className="text-muted-foreground">Vue d&apos;ensemble de votre système domotique</p>
        </div>
        <Button variant="outline" size="sm" onClick={fetchData}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Actualiser
        </Button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-full bg-primary/10">
                <Lightbulb className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-2xl font-semibold">{data.devices.length}</p>
                <p className="text-sm text-muted-foreground">Appareils</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-full bg-secondary/10">
                <Settings2 className="h-5 w-5 text-secondary" />
              </div>
              <div>
                <p className="text-2xl font-semibold">
                  {activeRules}/{data.rules.length}
                </p>
                <p className="text-sm text-muted-foreground">Règles actives</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-full bg-info/10">
                <Brain className="h-5 w-5 text-info" />
              </div>
              <div>
                {data.scenario ? (
                  <ScenarioChip scenario={data.scenario.scenario} confidence={data.scenario.confidence} />
                ) : (
                  <p className="text-sm text-muted-foreground">Non disponible</p>
                )}
                <p className="text-sm text-muted-foreground mt-1">Scénario IA</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-full bg-warning/10">
                <SunDim className="h-5 w-5 text-warning" />
              </div>
              <div>
                <p className="text-2xl font-semibold">{data.smartDimming?.adjustments_today ?? 0}</p>
                <p className="text-sm text-muted-foreground">
                  Ajustements ({data.smartDimming?.enabled ? "Actif" : "Inactif"})
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Devices Section */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-lg font-medium">Appareils</CardTitle>
            <Link href="/devices">
              <Button variant="ghost" size="sm">
                Voir tout
                <ChevronRight className="h-4 w-4 ml-1" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent>
            {data.devices.length === 0 ? (
              <p className="text-center text-muted-foreground py-8">Aucun appareil configuré</p>
            ) : (
              <div className="space-y-3">
                {data.devices.map((device) => (
                  <div
                    key={device.id}
                    className="flex items-center justify-between p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className={cn(
                          "p-2 rounded-full",
                          device.state === "ON" ? "bg-secondary/20 text-secondary" : "bg-muted-foreground/20",
                        )}
                      >
                        <Power className="h-4 w-4" />
                      </div>
                      <div>
                        <p className="font-medium text-sm">{device.name}</p>
                        <p className="text-xs text-muted-foreground">{device.location || device.type}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {device.brightness !== null && (
                        <span className="text-xs text-muted-foreground">{device.brightness}%</span>
                      )}
                      <span
                        className={cn(
                          "px-2 py-0.5 rounded-full text-xs font-medium",
                          device.state === "ON"
                            ? "bg-secondary/20 text-secondary"
                            : "bg-muted-foreground/20 text-muted-foreground",
                        )}
                      >
                        {device.state}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Events Section */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-lg font-medium">Événements récents</CardTitle>
            <Link href="/events">
              <Button variant="ghost" size="sm">
                Voir tout
                <ChevronRight className="h-4 w-4 ml-1" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent>
            {data.events.length === 0 ? (
              <p className="text-center text-muted-foreground py-8">Aucun événement récent</p>
            ) : (
              <div className="space-y-3">
                {data.events.map((event) => (
                  <div
                    key={event.id}
                    className="flex items-center justify-between p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className="p-2 rounded-full bg-primary/10">
                        <Activity className="h-4 w-4 text-primary" />
                      </div>
                      <div>
                        <p className="font-medium text-sm">{event.event_type}</p>
                        <p className="text-xs text-muted-foreground">
                          {event.device_name || event.source} {event.value && `• ${event.value}`}
                        </p>
                      </div>
                    </div>
                    <span className="text-xs text-muted-foreground">{formatRelativeTime(event.timestamp)}</span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-primary/5 border-primary/20">
          <CardContent className="pt-4 pb-4">
            <div className="text-center">
              <p className="text-3xl font-bold text-primary">{onlineDevices}</p>
              <p className="text-sm text-muted-foreground">Appareils allumés</p>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-secondary/5 border-secondary/20">
          <CardContent className="pt-4 pb-4">
            <div className="text-center">
              <p className="text-3xl font-bold text-secondary">{activeRules}</p>
              <p className="text-sm text-muted-foreground">Règles actives</p>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-warning/5 border-warning/20">
          <CardContent className="pt-4 pb-4">
            <div className="text-center">
              <p className="text-3xl font-bold text-warning">{data.smartDimming?.active_devices?.length ?? 0}</p>
              <p className="text-sm text-muted-foreground">Smart dimming actifs</p>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-info/5 border-info/20">
          <CardContent className="pt-4 pb-4">
            <div className="text-center">
              <p className="text-3xl font-bold text-info">{data.events.length}</p>
              <p className="text-sm text-muted-foreground">Événements récents</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
