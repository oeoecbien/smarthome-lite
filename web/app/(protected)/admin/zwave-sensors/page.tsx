"use client"

import { useEffect, useState, useCallback, useRef } from "react"
import Link from "next/link"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { LoadingSpinner } from "@/components/loading-spinner"
import { useIsAdmin } from "@/hooks/use-is-admin"
import { useRouter } from "next/navigation"
import { raspberryPiService, zwaveService } from "@/lib/services/raspberry-pi-service"
import { deviceService } from "@/lib/services/device-service"
import type { RaspberryPi } from "@/lib/services/raspberry-pi-service"
import type { Device, ZwaveSensorData, ZwaveKnownDevice } from "@/lib/types"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Radio,
  RefreshCw,
  Cpu,
  AlertCircle,
  Circle,
  Plus,
  ExternalLink,
} from "lucide-react"
import { toast } from "@/hooks/use-toast"

function useSensorStream(
  enabled: boolean,
  rpiId: number | null,
  nodeId: number | null,
  onData: (data: ZwaveSensorData | null, error: string | null) => void
) {
  const abortRef = useRef<(() => void) | null>(null)
  useEffect(() => {
    if (!enabled || !rpiId || nodeId == null || nodeId < 1 || nodeId > 255) {
      if (abortRef.current) {
        abortRef.current()
        abortRef.current = null
      }
      return
    }
    abortRef.current = raspberryPiService.subscribeNodeSensorStream(
      rpiId,
      nodeId,
      (event) => {
        if (event.error || (event as { success?: boolean }).success === false) {
          const msg = event.error ?? (event as { error?: string }).error ?? "Erreur flux"
          onData(null, typeof msg === "string" ? msg : "Erreur flux")
        } else {
          onData(event as ZwaveSensorData, null)
        }
      },
      (err) => {
        onData(null, err.message)
      }
    ).abort
    return () => {
      if (abortRef.current) {
        abortRef.current()
        abortRef.current = null
      }
    }
  }, [enabled, rpiId, nodeId, onData])
}

function formatLastUpdate(ms: number | null): string {
  if (ms == null) return "—"
  const sec = Math.floor((Date.now() - ms) / 1000)
  if (sec < 5) return "À l'instant"
  if (sec < 60) return `Il y a ${sec} s`
  const min = Math.floor(sec / 60)
  return `Il y a ${min} min`
}

export default function AdminZwaveSensorsPage() {
  const isAdmin = useIsAdmin()
  const router = useRouter()
  const [raspberryPis, setRaspberryPis] = useState<RaspberryPi[]>([])
  const [knownDevices, setKnownDevices] = useState<ZwaveKnownDevice[]>([])
  const [selectedRpiId, setSelectedRpiId] = useState<string>("")
  const [nodeId, setNodeId] = useState<string>("")
  const [sensorData, setSensorData] = useState<ZwaveSensorData | null>(null)
  const [sensorError, setSensorError] = useState<string | null>(null)
  const [lastUpdateMs, setLastUpdateMs] = useState<number | null>(null)
  const [liveEnabled, setLiveEnabled] = useState(true)
  const [isLoadingRpis, setIsLoadingRpis] = useState(true)
  const [isLoadingDevices, setIsLoadingDevices] = useState(true)
  const [isManualRefresh, setIsManualRefresh] = useState(false)
  const [, setTick] = useState(0)
  const [sensorDevices, setSensorDevices] = useState<Device[]>([])
  const [isLoadingSensors, setIsLoadingSensors] = useState(true)
  const [registerDialogOpen, setRegisterDialogOpen] = useState(false)
  const [registerName, setRegisterName] = useState("")
  const [isRegistering, setIsRegistering] = useState(false)
  const [registerError, setRegisterError] = useState<string | null>(null)
  useEffect(() => {
    if (!lastUpdateMs) return
    const id = setInterval(() => setTick((t) => t + 1), 1000)
    return () => clearInterval(id)
  }, [lastUpdateMs])

  const handleStreamData = useCallback((data: ZwaveSensorData | null, error: string | null) => {
    if (error) {
      setSensorError(error)
    } else if (data) {
      setSensorData(data)
      setSensorError(null)
      setLastUpdateMs(Date.now())
    }
  }, [])

  useSensorStream(
    liveEnabled,
    selectedRpiId ? Number(selectedRpiId) : null,
    nodeId ? Number(nodeId) : null,
    handleStreamData
  )

  useEffect(() => {
    if (!isAdmin) {
      router.push("/dashboard")
    }
  }, [isAdmin, router])

  const fetchRaspberryPis = useCallback(async () => {
    try {
      const data = await raspberryPiService.getRaspberryPis()
      setRaspberryPis(data)
      if (data.length > 0 && !selectedRpiId) {
        setSelectedRpiId(String(data[0].id))
      }
    } catch {
      toast({ variant: "destructive", title: "Erreur", description: "Impossible de charger les Raspberry Pi" })
    } finally {
      setIsLoadingRpis(false)
    }
  }, [selectedRpiId])

  const fetchKnownDevices = useCallback(async () => {
    try {
      const data = await zwaveService.getKnownDevices()
      setKnownDevices(data)
    } catch {
      toast({ variant: "destructive", title: "Erreur", description: "Impossible de charger les appareils Z-Wave connus" })
    } finally {
      setIsLoadingDevices(false)
    }
  }, [])

  const fetchSensorDevices = useCallback(async () => {
    try {
      const data = await deviceService.getDevices(undefined, "sensor")
      setSensorDevices(data)
    } catch {
      setSensorDevices([])
    } finally {
      setIsLoadingSensors(false)
    }
  }, [])

  useEffect(() => {
    if (isAdmin) {
      fetchRaspberryPis()
      fetchKnownDevices()
      fetchSensorDevices()
    }
  }, [isAdmin, fetchRaspberryPis, fetchKnownDevices, fetchSensorDevices])

  const rpiIdNum = selectedRpiId ? Number(selectedRpiId) : 0
  const nodeIdNum = nodeId ? Number(nodeId) : 0
  const canRefresh = rpiIdNum >= 1 && nodeIdNum >= 1 && nodeIdNum <= 255

  const selectedRpi = raspberryPis.find((r) => String(r.id) === selectedRpiId)
  const existingSensorDevice = sensorDevices.find(
    (d) => d.raspberry_pi_id === rpiIdNum && d.gpio_pin === nodeIdNum
  )

  const openRegisterDialog = useCallback(() => {
    const defaultName =
      sensorData?.device_name ||
      (selectedRpi?.location ? `Capteur Z-Wave - ${selectedRpi.location}` : null) ||
      `Capteur Z-Wave (node ${nodeId})`
    setRegisterName(defaultName)
    setRegisterError(null)
    setRegisterDialogOpen(true)
  }, [sensorData?.device_name, selectedRpi?.location, nodeId])

  const submitRegisterSensor = async () => {
    if (!rpiIdNum || nodeIdNum < 1 || nodeIdNum > 255 || !registerName.trim()) {
      setRegisterError("Nom requis et node ID entre 1 et 255.")
      return
    }
    setRegisterError(null)
    setIsRegistering(true)
    try {
      await deviceService.createDevice({
        name: registerName.trim(),
        type: "sensor",
        raspberry_pi_id: rpiIdNum,
        gpio_pin: nodeIdNum,
      })
      toast({ title: "Capteur enregistré", description: "Le capteur apparaît dans la liste des appareils." })
      setRegisterDialogOpen(false)
      fetchSensorDevices()
    } catch (err) {
      const message = err instanceof Error ? err.message : "Impossible d'enregistrer le capteur"
      setRegisterError(message)
      toast({ variant: "destructive", title: "Erreur", description: message })
    } finally {
      setIsRegistering(false)
    }
  }

  const fetchSensorDataManual = async () => {
    const rpiId = selectedRpiId ? Number(selectedRpiId) : 0
    const nid = nodeId ? Number(nodeId) : 0
    if (!rpiId || nid < 1 || nid > 255) {
      toast({
        variant: "destructive",
        title: "Paramètres invalides",
        description: "Sélectionnez un RPi et un node ID entre 1 et 255.",
      })
      return
    }
    setSensorError(null)
    setIsManualRefresh(true)
    try {
      const data = await raspberryPiService.getNodeSensor(rpiId, nid)
      setSensorData(data)
      setLastUpdateMs(Date.now())
      toast({ title: "Capteur", description: "Données mises à jour." })
    } catch (err) {
      setSensorError(err instanceof Error ? err.message : "Capteur indisponible")
      toast({
        variant: "destructive",
        title: "Erreur capteur",
        description: err instanceof Error ? err.message : "Impossible de lire le capteur",
      })
    } finally {
      setIsManualRefresh(false)
    }
  }

  if (!isAdmin) {
    return null
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-balance flex items-center gap-2">
          <Radio className="h-6 w-6 text-primary" />
          Capteurs Z-Wave
        </h1>
        <p className="text-muted-foreground">
          Données des capteurs Z-Wave (ex. Aeotec MultiSensor 7) via le Raspberry Pi. Activez « Valeurs en direct » pour un flux toutes les 5 s, ou cliquez sur « Rafraîchir ». Enregistrez le capteur puis associez des lampes pour le pilotage par mouvement et luminosité.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Lecture capteur</CardTitle>
            <CardDescription>
              Choisissez le RPi et le node ID Z-Wave. Valeurs en direct (flux 5 s) ou « Rafraîchir maintenant » pour une lecture immédiate.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Raspberry Pi</Label>
              <Select value={selectedRpiId} onValueChange={setSelectedRpiId} disabled={isLoadingRpis}>
                <SelectTrigger>
                  <SelectValue placeholder="Sélectionner un RPi" />
                </SelectTrigger>
                <SelectContent>
                  {raspberryPis.map((rpi) => (
                    <SelectItem key={rpi.id} value={String(rpi.id)}>
                      {rpi.name} {rpi.location ? `(${rpi.location})` : ""} {!rpi.is_online && "— hors ligne"}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Capteur enregistré (optionnel)</Label>
              <Select
                value={
                  selectedRpiId && nodeId && sensorDevices.some(
                    (d) => d.raspberry_pi_id === Number(selectedRpiId) && d.gpio_pin === Number(nodeId)
                  )
                    ? `rpi-${selectedRpiId}-node-${nodeId}`
                    : "__manual__"
                }
                onValueChange={(value) => {
                  if (value === "__manual__") {
                    setNodeId("")
                    return
                  }
                  const match = value.match(/^rpi-(\d+)-node-(\d+)$/)
                  if (match) {
                    setSelectedRpiId(match[1])
                    setNodeId(match[2])
                  }
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Saisie manuelle du node ID" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="__manual__">Saisie manuelle du node ID</SelectItem>
                  {sensorDevices.map((d) => (
                    <SelectItem key={d.id} value={`rpi-${d.raspberry_pi_id}-node-${d.gpio_pin}`}>
                      {d.name} (RPi #{d.raspberry_pi_id}, node {d.gpio_pin})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="node-id">Node ID Z-Wave (1–255)</Label>
              <Input
                id="node-id"
                type="number"
                min={1}
                max={255}
                value={nodeId}
                onChange={(e) => setNodeId(e.target.value)}
                placeholder="ex. 5"
              />
            </div>

            <div className="flex flex-wrap items-center gap-4">
              <div className="flex items-center gap-2">
                <Switch
                  id="live"
                  checked={liveEnabled}
                  onCheckedChange={setLiveEnabled}
                  disabled={!canRefresh}
                />
                <Label htmlFor="live" className="cursor-pointer">
                  Valeurs en direct (flux 5 s)
                </Label>
              </div>
              {liveEnabled && canRefresh && (
                <span className="flex items-center gap-1.5 text-sm text-muted-foreground">
                  <Circle className="h-2 w-2 fill-green-500 text-green-500 animate-pulse" />
                  En direct
                </span>
              )}
              <span className="text-sm text-muted-foreground">
                Dernière mise à jour : {formatLastUpdate(lastUpdateMs)}
              </span>
            </div>

            <Button
              onClick={fetchSensorDataManual}
              disabled={isManualRefresh || isLoadingRpis || raspberryPis.length === 0 || !canRefresh}
              variant="secondary"
            >
              {isManualRefresh ? (
                <LoadingSpinner size="sm" className="mr-2" />
              ) : (
                <RefreshCw className="h-4 w-4 mr-2" />
              )}
              Rafraîchir maintenant
            </Button>

            {sensorError && (
              <div className="flex items-center gap-2 rounded-lg border border-destructive/50 bg-destructive/10 px-3 py-2 text-sm text-destructive">
                <AlertCircle className="h-4 w-4 shrink-0" />
                {sensorError}
              </div>
            )}

            {sensorData && (
              <div className="rounded-lg border bg-muted/30 p-4 space-y-4">
                {/* En-tête device (type Z-Wave JS UI) */}
                <div className="flex flex-wrap items-center gap-2">
                  {(sensorData.device_name || sensorData.device_model) && (
                    <p className="text-sm font-medium text-muted-foreground">
                      {sensorData.device_name ?? ""} {sensorData.device_model ? `(${sensorData.device_model})` : ""}
                    </p>
                  )}
                  {sensorData.cached && (
                    <span className="rounded-md bg-amber-500/15 px-2 py-0.5 text-xs text-amber-700 dark:text-amber-400">
                      Cache
                    </span>
                  )}
                  {sensorData.unknown && (
                    <span className="rounded-md bg-destructive/15 px-2 py-0.5 text-xs text-destructive">
                      Données non disponibles
                    </span>
                  )}
                </div>

                {/* Binary Sensor v2 — Motion (CC 48) */}
                <div className="space-y-1">
                  <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Binary Sensor v2</p>
                  <div className="flex flex-wrap items-baseline gap-2 text-sm">
                    <span className="text-muted-foreground font-mono">
                      [{sensorData.node_id}-48-0-Motion]
                    </span>
                    <span className="text-muted-foreground">Sensor state (Motion)</span>
                    <span className={sensorData.motion ? "text-green-600 font-medium" : "text-muted-foreground"}>
                      {String(sensorData.motion)}
                    </span>
                  </div>
                </div>

                {/* Multilevel Sensor v11 — température, luminosité, humidité, UV (CC 49) */}
                <div className="space-y-2">
                  <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Multilevel Sensor v11</p>
                  <ul className="space-y-1.5 text-sm">
                    {sensorData.temperature_c != null && (
                      <li className="flex flex-wrap items-baseline gap-2">
                        <span className="text-muted-foreground font-mono">[{sensorData.node_id}-49-0-Air temperature]</span>
                        <span className="text-muted-foreground">Air temperature</span>
                        <span>{sensorData.temperature_c} °C</span>
                      </li>
                    )}
                    {sensorData.illuminance_lux != null && (
                      <li className="flex flex-wrap items-baseline gap-2">
                        <span className="text-muted-foreground font-mono">[{sensorData.node_id}-49-0-Illuminance]</span>
                        <span className="text-muted-foreground">Illuminance</span>
                        <span>{sensorData.illuminance_lux} Lux</span>
                      </li>
                    )}
                    {sensorData.humidity != null && (
                      <li className="flex flex-wrap items-baseline gap-2">
                        <span className="text-muted-foreground font-mono">[{sensorData.node_id}-49-0-Humidity]</span>
                        <span className="text-muted-foreground">Humidity</span>
                        <span>{sensorData.humidity} %</span>
                      </li>
                    )}
                    {sensorData.ultraviolet != null && (
                      <li className="flex flex-wrap items-baseline gap-2">
                        <span className="text-muted-foreground font-mono">[{sensorData.node_id}-49-0-Ultraviolet]</span>
                        <span className="text-muted-foreground">Ultraviolet</span>
                        <span>{sensorData.ultraviolet}</span>
                      </li>
                    )}
                  </ul>
                </div>

                {/* Batterie (CC 128) */}
                {sensorData.battery_percent != null && (
                  <div className="space-y-1 text-sm">
                    <span className="text-muted-foreground font-mono">[{sensorData.node_id}-128-0-level]</span>
                    <span className="text-muted-foreground">Battery</span>
                    <span>{sensorData.battery_percent} %</span>
                  </div>
                )}
              </div>
            )}

            {!sensorData && !sensorError && canRefresh && liveEnabled && (
              <p className="text-sm text-muted-foreground">Connexion au flux en cours…</p>
            )}
            {!sensorData && !sensorError && canRefresh && !liveEnabled && (
              <p className="text-sm text-muted-foreground">Cliquez sur « Rafraîchir maintenant » ou activez « Valeurs en direct ».</p>
            )}

            {/* Enregistrer ce capteur comme appareil (type sensor) */}
            {canRefresh && (
              <div className="pt-4 border-t border-border space-y-2">
                <p className="text-sm font-medium text-muted-foreground">Appareils</p>
                {isLoadingSensors ? (
                  <p className="text-sm text-muted-foreground">Chargement…</p>
                ) : existingSensorDevice ? (
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-sm">
                      Ce capteur est enregistré : <strong>{existingSensorDevice.name}</strong>
                    </span>
                    <Button variant="outline" size="sm" asChild>
                      <Link href="/admin/devices">
                        Voir / Modifier l&apos;appareil <ExternalLink className="h-3 w-3 ml-1" />
                      </Link>
                    </Button>
                    <span className="text-xs text-muted-foreground">
                      Lier une lampe à ce capteur (mouvement, luminosité) depuis la fiche appareil.
                    </span>
                  </div>
                ) : (
                  <div className="flex flex-wrap items-center gap-2">
                    <Button
                      type="button"
                      variant="secondary"
                      size="sm"
                      onClick={openRegisterDialog}
                    >
                      <Plus className="h-4 w-4 mr-2" />
                      Enregistrer ce capteur dans les appareils
                    </Button>
                    <span className="text-xs text-muted-foreground">
                      Pour le pilotage des lampes par mouvement / luminosité
                    </span>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        <Dialog open={registerDialogOpen} onOpenChange={setRegisterDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Enregistrer le capteur</DialogTitle>
              <DialogDescription>
                Crée un appareil de type « Capteur Z-Wave » dans la liste des appareils. Vous pourrez ensuite
                associer des lampes à ce capteur (mouvement, luminosité).
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-2">
              <Label htmlFor="register-name">Nom de l&apos;appareil</Label>
              <Input
                id="register-name"
                value={registerName}
                onChange={(e) => setRegisterName(e.target.value)}
                placeholder="ex. MultiSensor 7 Salon"
                maxLength={100}
              />
              {registerError && (
                <p className="text-sm text-destructive">{registerError}</p>
              )}
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setRegisterDialogOpen(false)} disabled={isRegistering}>
                Annuler
              </Button>
              <Button onClick={submitRegisterSensor} disabled={isRegistering || !registerName.trim()}>
                {isRegistering ? <LoadingSpinner size="sm" className="mr-2" /> : null}
                Enregistrer
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Appareils Z-Wave connus */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Cpu className="h-5 w-5" />
              Appareils Z-Wave connus
            </CardTitle>
            <CardDescription>
              Registre des appareils reconnus par le backend (manufacturerId, productType, productId).
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoadingDevices ? (
              <div className="justify-center py-8 flex">
                <LoadingSpinner size="md" />
              </div>
            ) : knownDevices.length === 0 ? (
              <p className="text-sm text-muted-foreground">Aucun appareil enregistré.</p>
            ) : (
              <ul className="space-y-3">
                {knownDevices.map((dev) => (
                  <li
                    key={`${dev.manufacturer_id}-${dev.product_type}-${dev.product_id}`}
                    className="rounded-lg border p-3"
                  >
                    <p className="font-medium">{dev.full_name}</p>
                    <p className="text-xs text-muted-foreground">
                      {dev.manufacturer_name} · Type {dev.product_type} / ID {dev.product_id} · {dev.model}
                    </p>
                    {dev.sensor_capabilities.length > 0 && (
                      <p className="text-xs text-muted-foreground mt-1">
                        Capteurs : {dev.sensor_capabilities.join(", ")}
                      </p>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
