"use client"

import { useEffect, useState, useCallback } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { LoadingSpinner } from "@/components/loading-spinner"
import { eventService } from "@/lib/services/event-service"
import { deviceService } from "@/lib/services/device-service"
import { formatRelativeTime, formatDate } from "@/lib/formatters"
import type { SystemEvent, Device } from "@/lib/types"
import { Calendar, RefreshCw, AlertCircle, Filter, Activity } from "lucide-react"

// Valeurs alignées avec le backend (EventFilterParams)
const EVENT_TYPES = [
  { value: "state_changed", label: "Changement d'état" },
  { value: "brightness_changed", label: "Changement d'intensité" },
  { value: "rule_triggered", label: "Règle déclenchée" },
  { value: "smart_dimming_applied", label: "Smart Dimming" },
  { value: "presence_detected", label: "Présence détectée" },
  { value: "scenario_changed", label: "Changement de scénario" },
  { value: "system", label: "Système" },
]

const SOURCE_TYPES = [
  { value: "manual", label: "Utilisateur" },
  { value: "rule", label: "Règle" },
  { value: "smart_dimming", label: "Smart Dimming" },
  { value: "ai", label: "IA" },
  { value: "automatic", label: "Automatique" },
]

export default function EventsPage() {
  const [events, setEvents] = useState<SystemEvent[]>([])
  const [devices, setDevices] = useState<Device[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Filters
  const [filterDeviceId, setFilterDeviceId] = useState<string>("all")
  const [filterEventType, setFilterEventType] = useState<string>("all")
  const [filterSource, setFilterSource] = useState<string>("all")
  const [filterLimit, setFilterLimit] = useState<number>(100)

  const fetchData = useCallback(async () => {
    try {
      const [eventsData, devicesData] = await Promise.all([
        eventService.getEvents(
          filterDeviceId !== "all" ? Number.parseInt(filterDeviceId) : undefined,
          filterEventType !== "all" ? filterEventType : undefined,
          filterSource !== "all" ? filterSource : undefined,
          filterLimit,
        ),
        deviceService.getDevices(),
      ])
      setEvents(eventsData)
      setDevices(devicesData)
      setError(null)
    } catch {
      setError("Erreur lors du chargement des événements")
    } finally {
      setIsLoading(false)
    }
  }, [filterDeviceId, filterEventType, filterSource, filterLimit])

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 10000)
    return () => clearInterval(interval)
  }, [fetchData])

  const getEventTypeLabel = (type: string) => {
    return EVENT_TYPES.find((t) => t.value === type)?.label || type
  }

  const getSourceLabel = (source: string) => {
    return SOURCE_TYPES.find((s) => s.value === source)?.label || source
  }

  const getEventTypeColor = (type: string) => {
    switch (type) {
      case "state_changed":
        return "bg-primary/10 text-primary"
      case "brightness_changed":
        return "bg-warning/10 text-warning"
      case "rule_triggered":
        return "bg-secondary/10 text-secondary"
      case "smart_dimming_applied":
      case "smart_dimming":
        return "bg-info/10 text-info"
      case "presence_detected":
        return "bg-accent/10 text-accent"
      case "scenario_changed":
      case "system":
      default:
        return "bg-muted text-muted-foreground"
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <LoadingSpinner size="lg" text="Chargement des événements..." />
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
      {/* Header + Filtres sur une seule ligne compacte */}
      <div className="flex flex-col gap-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold text-balance">Journal des événements</h1>
            <p className="text-muted-foreground">Historique des changements (état, intensité, règles, présence, IA). Filtrez par type ou source.</p>
          </div>
          <Button variant="outline" size="sm" onClick={fetchData}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Actualiser
          </Button>
        </div>

        {/* Barre de filtres compacte */}
        <div className="flex flex-wrap items-center gap-3 rounded-lg border bg-muted/30 px-4 py-3">
          <span className="flex items-center gap-2 text-sm font-medium text-muted-foreground shrink-0">
            <Filter className="h-4 w-4" />
            Filtres
          </span>
          <Select value={filterDeviceId} onValueChange={setFilterDeviceId}>
            <SelectTrigger className="w-[180px] h-9">
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
          <Select value={filterEventType} onValueChange={setFilterEventType}>
            <SelectTrigger className="w-[200px] h-9">
              <SelectValue placeholder="Type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Tous les types</SelectItem>
              {EVENT_TYPES.map((type) => (
                <SelectItem key={type.value} value={type.value}>
                  {type.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={filterSource} onValueChange={setFilterSource}>
            <SelectTrigger className="w-[160px] h-9">
              <SelectValue placeholder="Source" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Toutes les sources</SelectItem>
              {SOURCE_TYPES.map((source) => (
                <SelectItem key={source.value} value={source.value}>
                  {source.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={String(filterLimit)} onValueChange={(v) => setFilterLimit(Number.parseInt(v))}>
            <SelectTrigger className="w-[150px] h-9">
              <SelectValue placeholder="Limite" />
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

      {/* Liste des événements */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Calendar className="h-5 w-5 text-primary" />
            Événements
          </CardTitle>
          <CardDescription>{events.length} événement(s)</CardDescription>
        </CardHeader>
        <CardContent>
          {events.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Activity className="h-12 w-12 text-muted-foreground mb-4" />
              <p className="text-muted-foreground">Aucun événement correspondant aux filtres</p>
            </div>
          ) : (
            <div className="space-y-3 max-h-[600px] overflow-y-auto">
              {events.map((event) => (
                <div key={event.id} className="flex items-start justify-between p-4 bg-muted/50 rounded-lg gap-4">
                  <div className="flex items-start gap-3 min-w-0">
                    <div className="p-2 rounded-lg bg-primary/10 shrink-0">
                      <Activity className="h-4 w-4 text-primary" />
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 flex-wrap mb-1">
                        <Badge variant="secondary" className={getEventTypeColor(event.event_type)}>
                          {getEventTypeLabel(event.event_type)}
                        </Badge>
                        <span className="text-xs text-muted-foreground">{getSourceLabel(event.source)}</span>
                      </div>
                      <p className="text-sm">
                        {event.device_name && <span className="font-medium">{event.device_name}</span>}
                        {event.value && (
                          <span className="text-muted-foreground">
                            {event.device_name ? " • " : ""}
                            {event.value}
                          </span>
                        )}
                      </p>
                    </div>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="text-sm text-muted-foreground">{formatRelativeTime(event.timestamp)}</p>
                    <p className="text-xs text-muted-foreground/60">{formatDate(event.timestamp)}</p>
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
