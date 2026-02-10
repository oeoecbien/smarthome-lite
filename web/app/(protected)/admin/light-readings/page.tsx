"use client"

import { useEffect, useState, useCallback } from "react"
import { useRouter } from "next/navigation"
import { useIsAdmin } from "@/hooks/use-is-admin"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { LoadingSpinner } from "@/components/loading-spinner"
import { LightChart } from "@/components/light-chart"
import { lightReadingService } from "@/lib/services/light-reading-service"
import { raspberryPiService } from "@/lib/services/raspberry-pi-service"
import { formatRelativeTime, formatDate, formatNumber } from "@/lib/formatters"
import { toast } from "@/hooks/use-toast"
import type { LightReading } from "@/lib/types"
import type { RaspberryPi } from "@/lib/services/raspberry-pi-service"
import { Sun, RefreshCw, AlertCircle, Filter, Gauge, Save } from "lucide-react"

function readingToPercent(lux: number): number {
  return Math.min(100, Math.round((lux / 65535) * 100))
}

export default function LightReadingsPage() {
  const isAdmin = useIsAdmin()
  const router = useRouter()
  const [readings, setReadings] = useState<LightReading[]>([])
  const [raspberryPis, setRaspberryPis] = useState<RaspberryPi[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filterRpiId, setFilterRpiId] = useState<string>("")
  const [filterLimit, setFilterLimit] = useState<number>(100)
  const [manualRpiId, setManualRpiId] = useState<string>("")
  const [manualLux, setManualLux] = useState<string>("")
  const [manualSensorType, setManualSensorType] = useState<string>("BH1750")
  const [isSaving, setIsSaving] = useState(false)

  const fetchData = useCallback(async () => {
    try {
      const data = await lightReadingService.getLightReadings(
        filterRpiId ? Number(filterRpiId) : undefined,
        filterLimit,
      )
      setReadings(data)
      setError(null)
    } catch {
      setError("Erreur lors du chargement des mesures")
    } finally {
      setIsLoading(false)
    }
  }, [filterRpiId, filterLimit])

  const fetchRaspberryPis = useCallback(async () => {
    try {
      const data = await raspberryPiService.getRaspberryPis()
      setRaspberryPis(data)
    } catch {
      setRaspberryPis([])
    }
  }, [])

  const handleSaveManual = async () => {
    const rpiId = manualRpiId ? Number(manualRpiId) : 0
    const lux = Number(manualLux)
    if (!rpiId || Number.isNaN(lux) || lux < 0) {
      toast({
        variant: "destructive",
        title: "Champs invalides",
        description: "Sélectionnez un Raspberry Pi et une valeur lux ≥ 0.",
      })
      return
    }
    setIsSaving(true)
    try {
      await lightReadingService.createLightReadingManual({
        raspberry_pi_id: rpiId,
        lux_value: lux,
        sensor_type: manualSensorType,
      })
      toast({ title: "Mesure enregistrée", description: `${lux} lux enregistrés pour le RPi sélectionné.` })
      setManualLux("")
      fetchData()
    } catch (e) {
      toast({
        variant: "destructive",
        title: "Erreur",
        description: e instanceof Error ? e.message : "Impossible d'enregistrer la mesure.",
      })
    } finally {
      setIsSaving(false)
    }
  }

  useEffect(() => {
    if (!isAdmin) {
      router.push("/dashboard")
    }
  }, [isAdmin, router])

  useEffect(() => {
    if (!isAdmin) return
    fetchRaspberryPis()
  }, [isAdmin, fetchRaspberryPis])

  useEffect(() => {
    if (!isAdmin) return
    fetchData()
    const interval = setInterval(fetchData, 10000)
    return () => clearInterval(interval)
  }, [isAdmin, fetchData])

  if (!isAdmin) {
    return null
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <LoadingSpinner size="lg" text="Chargement des mesures..." />
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

  const lastReading = readings[0]
  const avgLux = readings.length > 0 ? readings.reduce((sum, r) => sum + r.lux_value, 0) / readings.length : 0
  const avgPercent =
    readings.length > 0
      ? readings.reduce((sum, r) => sum + readingToPercent(r.lux_value), 0) / readings.length
      : 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-balance">Historique de luminosité</h1>
          <p className="text-muted-foreground">Mesures des capteurs de luminosité</p>
        </div>
        <Button variant="outline" size="sm" onClick={fetchData}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Actualiser
        </Button>
      </div>

      {/* Stats */}
      <div className="grid sm:grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-3 rounded-xl bg-warning/10">
                <Sun className="h-6 w-6 text-warning" />
              </div>
              <div>
                <p className="text-2xl font-bold">{lastReading ? formatNumber(lastReading.lux_value) : "-"}</p>
                <p className="text-sm text-muted-foreground">Dernière mesure (lux)</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-3 rounded-xl bg-primary/10">
                <Gauge className="h-6 w-6 text-primary" />
              </div>
              <div>
                <p className="text-2xl font-bold">{formatNumber(avgLux, 1)}</p>
                <p className="text-sm text-muted-foreground">Moyenne lux ({readings.length} mesures)</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-3 rounded-xl bg-secondary/10">
                <Gauge className="h-6 w-6 text-secondary" />
              </div>
              <div>
                <p className="text-2xl font-bold">{formatNumber(avgPercent, 1)}%</p>
                <p className="text-sm text-muted-foreground">Moyenne pourcentage</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Sauvegarde manuelle */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Save className="h-5 w-5" />
            Ajouter une mesure
          </CardTitle>
          <CardDescription>
            Enregistrer manuellement une valeur de luminosité (lux) pour un Raspberry Pi. Déclenche le Smart Dimming si activé.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap items-end gap-4">
          <div className="flex flex-col gap-2">
            <Label htmlFor="manual-rpi">Raspberry Pi</Label>
            <Select value={manualRpiId || "__none__"} onValueChange={(v) => setManualRpiId(v === "__none__" ? "" : v)}>
              <SelectTrigger id="manual-rpi" className="w-[220px]">
                <SelectValue placeholder="Choisir un RPi" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__none__">Choisir un RPi</SelectItem>
                {raspberryPis.map((rpi) => (
                  <SelectItem key={rpi.id} value={String(rpi.id)}>
                    {rpi.name} {rpi.location ? `(${rpi.location})` : ""}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="manual-lux">Lux</Label>
            <Input
              id="manual-lux"
              type="number"
              min={0}
              step={0.1}
              placeholder="ex. 250"
              value={manualLux}
              onChange={(e) => setManualLux(e.target.value)}
              className="w-[120px]"
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="manual-sensor">Type capteur</Label>
            <Select value={manualSensorType} onValueChange={setManualSensorType}>
              <SelectTrigger id="manual-sensor" className="w-[120px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="BH1750">BH1750</SelectItem>
                <SelectItem value="LDR">LDR</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <Button onClick={handleSaveManual} disabled={isSaving}>
            {isSaving ? <LoadingSpinner size="sm" className="mr-2" /> : <Save className="h-4 w-4 mr-2" />}
            Sauvegarder
          </Button>
        </CardContent>
      </Card>

      {/* Chart */}
      <LightChart data={readings} />

      {/* Filters and History */}
      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <CardTitle className="text-lg">Historique détaillé</CardTitle>
              <CardDescription>{readings.length} mesure(s)</CardDescription>
            </div>
            <div className="flex flex-wrap items-center gap-4">
              <div className="flex items-center gap-2">
                <Label htmlFor="filter-rpi" className="text-sm text-muted-foreground whitespace-nowrap">
                  Raspberry Pi
                </Label>
                <Select value={filterRpiId || "__all__"} onValueChange={(v) => setFilterRpiId(v === "__all__" ? "" : v)}>
                  <SelectTrigger id="filter-rpi" className="w-[200px]">
                    <Filter className="h-4 w-4 mr-2 shrink-0" />
                    <SelectValue placeholder="Tous" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__all__">Tous les RPi</SelectItem>
                    {raspberryPis.map((rpi) => (
                      <SelectItem key={rpi.id} value={String(rpi.id)}>
                        {rpi.name} {rpi.location ? `(${rpi.location})` : ""}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="flex items-center gap-2">
                <Label htmlFor="filter-limit" className="text-sm text-muted-foreground whitespace-nowrap">
                  Nombre
                </Label>
                <Select value={String(filterLimit)} onValueChange={(v) => setFilterLimit(Number(v))}>
                  <SelectTrigger id="filter-limit" className="w-[100px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="50">50</SelectItem>
                    <SelectItem value="100">100</SelectItem>
                    <SelectItem value="200">200</SelectItem>
                    <SelectItem value="500">500</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {readings.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">Aucune mesure. Les RPi envoient les données via POST /api/light-readings.</p>
          ) : (
            <div className="space-y-2 max-h-[400px] overflow-y-auto">
              {readings.map((reading) => (
                <div key={reading.id} className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                      <Sun className="h-4 w-4 text-warning shrink-0" />
                      <span className="font-medium">{formatNumber(reading.lux_value)} lux</span>
                    </div>
                    <span className="text-sm text-muted-foreground">{readingToPercent(reading.lux_value)} %</span>
                    <span className="text-xs text-muted-foreground">
                      {reading.raspberry_pi_name ?? `RPi #${reading.raspberry_pi_id}`}
                      {reading.sensor_type ? ` · ${reading.sensor_type}` : ""}
                    </span>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-muted-foreground">{formatRelativeTime(reading.measured_at)}</p>
                    <p className="text-xs text-muted-foreground/60">{formatDate(reading.measured_at)}</p>
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
