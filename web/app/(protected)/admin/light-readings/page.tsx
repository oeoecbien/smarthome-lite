"use client"

import { useEffect, useState, useCallback } from "react"
import { useRouter } from "next/navigation"
import { useIsAdmin } from "@/hooks/use-is-admin"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { LoadingSpinner } from "@/components/loading-spinner"
import { LightChart } from "@/components/light-chart"
import { lightReadingService } from "@/lib/services/light-reading-service"
import { formatRelativeTime, formatDate, formatNumber } from "@/lib/formatters"
import type { LightReading } from "@/lib/types"
import { Sun, RefreshCw, AlertCircle, Filter, Gauge } from "lucide-react"

export default function LightReadingsPage() {
  const isAdmin = useIsAdmin()
  const router = useRouter()
  const [readings, setReadings] = useState<LightReading[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filterRpiId, setFilterRpiId] = useState<string>("")
  const [filterLimit, setFilterLimit] = useState<number>(100)

  const fetchData = useCallback(async () => {
    try {
      const data = await lightReadingService.getLightReadings(
        filterRpiId ? Number.parseInt(filterRpiId) : undefined,
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

  useEffect(() => {
    if (!isAdmin) {
      router.push("/dashboard")
    }
  }, [isAdmin, router])

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

  // Calculate stats
  const lastReading = readings[0]
  const avgLux = readings.length > 0 ? readings.reduce((sum, r) => sum + r.lux, 0) / readings.length : 0
  const avgPercent = readings.length > 0 ? readings.reduce((sum, r) => sum + r.percentage, 0) / readings.length : 0

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
                <p className="text-2xl font-bold">{lastReading ? formatNumber(lastReading.lux) : "-"}</p>
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
            <div className="flex gap-2">
              <Input
                placeholder="RPi ID"
                value={filterRpiId}
                onChange={(e) => setFilterRpiId(e.target.value)}
                className="w-[100px]"
                type="number"
                min="1"
              />
              <Select value={String(filterLimit)} onValueChange={(v) => setFilterLimit(Number.parseInt(v))}>
                <SelectTrigger className="w-[100px]">
                  <Filter className="h-4 w-4 mr-2" />
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="50">50</SelectItem>
                  <SelectItem value="100">100</SelectItem>
                  <SelectItem value="200">200</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {readings.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">Aucune mesure</p>
          ) : (
            <div className="space-y-2 max-h-[400px] overflow-y-auto">
              {readings.map((reading) => (
                <div key={reading.id} className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                      <Sun className="h-4 w-4 text-warning" />
                      <span className="font-medium">{formatNumber(reading.lux)} lux</span>
                    </div>
                    <span className="text-sm text-muted-foreground">{reading.percentage}%</span>
                    <span className="text-xs text-muted-foreground">RPi #{reading.raspberry_pi_id}</span>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-muted-foreground">{formatRelativeTime(reading.timestamp)}</p>
                    <p className="text-xs text-muted-foreground/60">{formatDate(reading.timestamp)}</p>
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
