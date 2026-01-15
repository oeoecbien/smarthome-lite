"use client"

import { useEffect, useState, useCallback } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { LoadingSpinner } from "@/components/loading-spinner"
import { PresenceChart } from "@/components/presence-chart"
import { presenceService } from "@/lib/services/presence-service"
import { formatRelativeTime, formatDate } from "@/lib/formatters"
import type { PresenceRecord } from "@/lib/types"
import { RefreshCw, AlertCircle, Filter, UserCheck, Clock } from "lucide-react"
import { cn } from "@/lib/utils"

export default function PresencePage() {
  const [records, setRecords] = useState<PresenceRecord[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Filters
  const [filterRpiId, setFilterRpiId] = useState<string>("")
  const [filterLimit, setFilterLimit] = useState<number>(100)

  const fetchData = useCallback(async () => {
    try {
      const data = await presenceService.getPresenceHistory(
        filterRpiId ? Number.parseInt(filterRpiId) : undefined,
        filterLimit,
      )
      setRecords(data)
      setError(null)
    } catch {
      setError("Erreur lors du chargement de l'historique")
    } finally {
      setIsLoading(false)
    }
  }, [filterRpiId, filterLimit])

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [fetchData])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <LoadingSpinner size="lg" text="Chargement de l'historique..." />
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
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const detectionsToday = records.filter((r) => r.detected && new Date(r.timestamp) >= today).length
  const lastDetection = records.find((r) => r.detected)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-balance">Historique de présence</h1>
          <p className="text-muted-foreground">Détections de présence par les capteurs</p>
        </div>
        <Button variant="outline" size="sm" onClick={fetchData}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Actualiser
        </Button>
      </div>

      {/* Stats */}
      <div className="grid sm:grid-cols-2 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-3 rounded-xl bg-primary/10">
                <UserCheck className="h-6 w-6 text-primary" />
              </div>
              <div>
                <p className="text-2xl font-bold">{detectionsToday}</p>
                <p className="text-sm text-muted-foreground">Détections aujourd&apos;hui</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-3 rounded-xl bg-secondary/10">
                <Clock className="h-6 w-6 text-secondary" />
              </div>
              <div>
                <p className="text-lg font-medium">
                  {lastDetection ? formatRelativeTime(lastDetection.timestamp) : "Aucune"}
                </p>
                <p className="text-sm text-muted-foreground">Dernière détection</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Chart */}
      <PresenceChart data={records} />

      {/* Filters and History */}
      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <CardTitle className="text-lg">Historique détaillé</CardTitle>
              <CardDescription>{records.length} enregistrement(s)</CardDescription>
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
          {records.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">Aucun enregistrement</p>
          ) : (
            <div className="space-y-2 max-h-[400px] overflow-y-auto">
              {records.map((record) => (
                <div
                  key={record.id}
                  className={cn(
                    "flex items-center justify-between p-3 rounded-lg",
                    record.detected ? "bg-secondary/10" : "bg-muted/50",
                  )}
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={cn("w-2 h-2 rounded-full", record.detected ? "bg-secondary" : "bg-muted-foreground")}
                    />
                    <span className="text-sm font-medium">{record.detected ? "Présence" : "Absence"}</span>
                    <span className="text-xs text-muted-foreground">RPi #{record.raspberry_pi_id}</span>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-muted-foreground">{formatRelativeTime(record.timestamp)}</p>
                    <p className="text-xs text-muted-foreground/60">{formatDate(record.timestamp)}</p>
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
