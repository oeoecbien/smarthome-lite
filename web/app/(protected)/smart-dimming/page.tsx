"use client"

import { useEffect, useState, useCallback } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Switch } from "@/components/ui/switch"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { LoadingSpinner } from "@/components/loading-spinner"
import { ScenarioChip } from "@/components/scenario-chip"
import { smartDimmingService } from "@/lib/services/smart-dimming-service"
import { deviceService } from "@/lib/services/device-service"
import { formatRelativeTime } from "@/lib/formatters"
import type { SmartDimmingStatus, SmartDimmingAdjustment, Device } from "@/lib/types"
import { SunDim, RefreshCw, AlertCircle, Pause, ArrowRight, Lightbulb, Filter } from "lucide-react"
import { cn } from "@/lib/utils"

export default function SmartDimmingPage() {
  const [status, setStatus] = useState<SmartDimmingStatus | null>(null)
  const [adjustments, setAdjustments] = useState<SmartDimmingAdjustment[]>([])
  const [devices, setDevices] = useState<Device[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isToggling, setIsToggling] = useState(false)
  const [pausingDevice, setPausingDevice] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Filters
  const [filterDeviceId, setFilterDeviceId] = useState<string>("all")
  const [filterLimit, setFilterLimit] = useState<number>(50)

  const fetchData = useCallback(async () => {
    try {
      const [statusData, adjustmentsData, devicesData] = await Promise.all([
        smartDimmingService.getStatus(),
        smartDimmingService.getAdjustments(
          filterDeviceId !== "all" ? Number.parseInt(filterDeviceId) : undefined,
          filterLimit,
        ),
        deviceService.getDevices(),
      ])
      setStatus(statusData)
      setAdjustments(adjustmentsData)
      setDevices(devicesData)
      setError(null)
    } catch {
      setError("Erreur lors du chargement des données")
    } finally {
      setIsLoading(false)
    }
  }, [filterDeviceId, filterLimit])

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 10000)
    return () => clearInterval(interval)
  }, [fetchData])

  const handleToggle = async () => {
    if (!status) return
    setIsToggling(true)
    try {
      await smartDimmingService.enable(!status.enabled)
      fetchData()
    } catch (err) {
      console.error("Failed to toggle smart dimming:", err)
    } finally {
      setIsToggling(false)
    }
  }

  const handlePause = async (deviceId: number) => {
    setPausingDevice(deviceId)
    try {
      await smartDimmingService.pauseDevice(deviceId)
      fetchData()
    } catch (err) {
      console.error("Failed to pause device:", err)
    } finally {
      setPausingDevice(null)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <LoadingSpinner size="lg" text="Chargement du smart dimming..." />
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-balance">Smart Dimming</h1>
          <p className="text-muted-foreground">Ajustement automatique de l&apos;intensité lumineuse</p>
        </div>
        <Button variant="outline" size="sm" onClick={fetchData}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Actualiser
        </Button>
      </div>

      {/* Status Cards */}
      <div className="grid sm:grid-cols-3 gap-4">
        <Card className={cn(status?.enabled ? "ring-2 ring-secondary/50" : "")}>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={cn("p-3 rounded-xl", status?.enabled ? "bg-secondary/20" : "bg-muted")}>
                  <SunDim className={cn("h-6 w-6", status?.enabled ? "text-secondary" : "text-muted-foreground")} />
                </div>
                <div>
                  <p className="font-medium">{status?.enabled ? "Activé" : "Désactivé"}</p>
                  <p className="text-sm text-muted-foreground">Smart Dimming</p>
                </div>
              </div>
              <Switch checked={status?.enabled ?? false} onCheckedChange={handleToggle} disabled={isToggling} />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-3 rounded-xl bg-primary/10">
                <ArrowRight className="h-6 w-6 text-primary" />
              </div>
              <div>
                <p className="text-2xl font-bold">{status?.adjustments_today ?? 0}</p>
                <p className="text-sm text-muted-foreground">Ajustements aujourd&apos;hui</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-3 rounded-xl bg-warning/10">
                <Lightbulb className="h-6 w-6 text-warning" />
              </div>
              <div>
                <p className="text-2xl font-bold">{status?.active_devices?.length ?? 0}</p>
                <p className="text-sm text-muted-foreground">Appareils actifs</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Active Devices with Pause */}
      {status?.active_devices && status.active_devices.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Appareils sous contrôle</CardTitle>
            <CardDescription>Appareils actuellement gérés par le smart dimming</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {status.active_devices.map((deviceId) => {
                const device = devices.find((d) => d.id === deviceId)
                return (
                  <div
                    key={deviceId}
                    className="flex items-center justify-between p-3 bg-muted/50 rounded-lg hover:bg-muted transition-colors"
                  >
                    <div className="flex items-center gap-2">
                      <Lightbulb className="h-4 w-4 text-warning" />
                      <span className="text-sm font-medium">{device?.name || `Appareil #${deviceId}`}</span>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handlePause(deviceId)}
                      disabled={pausingDevice === deviceId}
                      className="text-muted-foreground hover:bg-muted hover:text-white"
                    >
                      <Pause className="h-4 w-4 mr-1" />
                      {pausingDevice === deviceId ? "..." : "30 min"}
                    </Button>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Adjustments History */}
      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <CardTitle className="text-lg">Historique des ajustements</CardTitle>
              <CardDescription>Dernières modifications automatiques d&apos;intensité</CardDescription>
            </div>
            <div className="flex gap-2">
              <Select value={filterDeviceId} onValueChange={setFilterDeviceId}>
                <SelectTrigger className="w-[160px]">
                  <Filter className="h-4 w-4 mr-2" />
                  <SelectValue placeholder="Appareil" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tous les appareils</SelectItem>
                  {devices.map((device) => (
                    <SelectItem key={device.id} value={String(device.id)}>
                      {device.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={String(filterLimit)} onValueChange={(v) => setFilterLimit(Number.parseInt(v))}>
                <SelectTrigger className="w-[100px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="20">20</SelectItem>
                  <SelectItem value="50">50</SelectItem>
                  <SelectItem value="100">100</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {adjustments.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">Aucun ajustement récent</p>
          ) : (
            <div className="space-y-3">
              {adjustments.map((adj) => (
                <div key={adj.id} className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2 text-sm">
                      <span className="font-medium text-muted-foreground">{adj.brightness_before}%</span>
                      <ArrowRight className="h-4 w-4 text-primary" />
                      <span className="font-bold">{adj.brightness_after}%</span>
                    </div>
                    <div className="hidden sm:block">
                      <ScenarioChip scenario={adj.scenario} className="text-xs" />
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium">{adj.device_name || `Appareil #${adj.device_id}`}</p>
                    <p className="text-xs text-muted-foreground">{formatRelativeTime(adj.timestamp)}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
