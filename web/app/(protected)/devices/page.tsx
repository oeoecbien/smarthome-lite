"use client"

import type React from "react"
import { Suspense } from "react"

import { useEffect, useState, useCallback } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { LoadingSpinner } from "@/components/loading-spinner"
import { DeviceCard } from "@/components/device-card"
import { DeviceCardUser } from "@/components/device-card-user"
import { AdminOnly } from "@/components/admin-only"
import { deviceService } from "@/lib/services/device-service"
import { raspberryPiService, type AvailableRaspberryPi } from "@/lib/services/raspberry-pi-service"
import { useIsAdmin } from "@/hooks/use-is-admin"
import type { Device, SensorRules } from "@/lib/types"
import { Plus, RefreshCw, Search, AlertCircle, Lightbulb, Filter, Pencil } from "lucide-react"

const DEVICE_TYPES_BASE = [
  { value: "light", label: "Lumière" },
  { value: "dimmer", label: "Variateur" },
  { value: "socket", label: "Prise" },
]
const DEVICE_TYPES_WITH_SENSOR = [...DEVICE_TYPES_BASE, { value: "sensor", label: "Capteur (Z-Wave)" }]

/** Normalise une chaîne pour la recherche : trim, minuscules, sans accents. */
function normalizeForSearch(s: string): string {
  return (s ?? "")
    .trim()
    .toLowerCase()
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
}

const TYPE_LABEL: Record<string, string> = Object.fromEntries(
  DEVICE_TYPES_WITH_SENSOR.map((t) => [t.value, t.label])
)

interface NewDeviceForm {
  name: string
  type: "light" | "dimmer" | "socket" | "sensor"
  raspberry_pi_id: number
  gpio_pin: number
  location: string
}

function DevicesContent() {
  const isAdmin = useIsAdmin()
  const router = useRouter()
  const [devices, setDevices] = useState<Device[]>([])
  const [filteredDevices, setFilteredDevices] = useState<Device[]>([])
  const [raspberryPis, setRaspberryPis] = useState<AvailableRaspberryPi[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [isCreating, setIsCreating] = useState(false)
  const [createError, setCreateError] = useState<string | null>(null)
  const [editingDevice, setEditingDevice] = useState<Device | null>(null)
  const [editForm, setEditForm] = useState<Partial<Device> & { sensor_rules?: SensorRules }>({})
  const [isSavingEdit, setIsSavingEdit] = useState(false)
  const [editError, setEditError] = useState<string | null>(null)

  // Admin : rediriger vers la page admin appareils
  useEffect(() => {
    if (isAdmin) {
      router.replace("/admin/devices")
    }
  }, [isAdmin, router])

  // Filters
  const [searchQuery, setSearchQuery] = useState("")
  const [filterLocation, setFilterLocation] = useState<string>("all")
  const [filterType, setFilterType] = useState<string>("all")

  // Form state
  const [formData, setFormData] = useState<NewDeviceForm>({
    name: "",
    type: "light",
    raspberry_pi_id: 1,
    gpio_pin: 17,
    location: "",
  })

  const fetchDevices = useCallback(async () => {
    try {
      const data = await deviceService.getDevices()
      setDevices((prev) => {
        if (prev.length === 0) return data
        const byId = new Map(data.map((d) => [d.id, d]))
        const keptOrder = prev.map((d) => byId.get(d.id) ?? d).filter((d) => byId.has(d.id))
        const added = data.filter((d) => !prev.some((p) => p.id === d.id))
        return [...keptOrder, ...added]
      })
      setError(null)
    } catch {
      setError("Erreur lors du chargement des appareils")
    } finally {
      setIsLoading(false)
    }
  }, [])

  const fetchRaspberryPis = useCallback(async () => {
    try {
      const data = await raspberryPiService.getAvailableRaspberryPis()
      setRaspberryPis(data)
      // Si des Raspberry Pi sont disponibles, sélectionner le premier par défaut
      if (data.length > 0) {
        setFormData(prev => {
          // Ne mettre à jour que si la valeur actuelle est invalide (1 par défaut)
          if (prev.raspberry_pi_id === 1 && !data.find(rpi => rpi.id === 1)) {
            return { ...prev, raspberry_pi_id: data[0].id }
          }
          return prev
        })
      }
    } catch (err) {
      console.error("Erreur lors du chargement des Raspberry Pi:", err)
    }
  }, [])

  useEffect(() => {
    fetchDevices()
    fetchRaspberryPis()
    const interval = setInterval(fetchDevices, 5000)
    return () => clearInterval(interval)
  }, [fetchDevices, fetchRaspberryPis])

  // Apply filters
  useEffect(() => {
    let result = [...devices]

    const q = normalizeForSearch(searchQuery)
    if (q) {
      result = result.filter((d) => {
        const nameNorm = normalizeForSearch(d.name)
        const locationNorm = d.location ? normalizeForSearch(d.location) : ""
        const typeLabelNorm = normalizeForSearch(TYPE_LABEL[d.type] ?? "")
        return nameNorm.includes(q) || locationNorm.includes(q) || typeLabelNorm.includes(q)
      })
    }

    if (filterLocation && filterLocation !== "all") {
      result = result.filter((d) => d.location === filterLocation)
    }

    if (filterType && filterType !== "all") {
      result = result.filter((d) => d.type === filterType)
    }

    setFilteredDevices(result)
  }, [devices, searchQuery, filterLocation, filterType])

  // Get unique locations for filter
  const locations = [...new Set(devices.map((d) => d.location).filter(Boolean))]

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsCreating(true)
    setCreateError(null)

    try {
      await deviceService.createDevice({
        name: formData.name,
        type: formData.type,
        raspberry_pi_id: formData.raspberry_pi_id,
        gpio_pin: formData.gpio_pin,
        location: formData.location || undefined,
      })
      setIsDialogOpen(false)
      setFormData({
        name: "",
        type: "light",
        raspberry_pi_id: 1,
        gpio_pin: 17,
        location: "",
      })
      fetchDevices()
    } catch (err) {
      setCreateError(err instanceof Error ? err.message : "Erreur lors de la création")
    } finally {
      setIsCreating(false)
    }
  }

  const handleDelete = async (id: number) => {
    try {
      await deviceService.deleteDevice(id)
      fetchDevices()
    } catch (err) {
      console.error("Failed to delete device:", err)
    }
  }

  const openEdit = (device: Device) => {
    setEditingDevice(device)
    setEditForm({
      name: device.name,
      type: device.type,
      gpio_pin: device.gpio_pin ?? undefined,
      controlled_by_sensor_id: device.controlled_by_sensor_id ?? undefined,
      sensor_rules: device.sensor_rules ?? undefined,
    })
    setEditError(null)
  }

  const handleSaveEdit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!editingDevice) return
    const maxPin = editForm.type === "sensor" ? 255 : 40
    const rawPin = editForm.gpio_pin ?? editingDevice.gpio_pin
    const gpioPin = typeof rawPin === "number" && rawPin >= 1 && rawPin <= maxPin ? rawPin : editingDevice.gpio_pin
    if (gpioPin == null || gpioPin < 1 || gpioPin > maxPin) {
      setEditError(
        editForm.type === "sensor"
          ? "Node ID invalide. Saisir un nombre entre 1 et 255 (node Z-Wave)."
          : "Broche invalide. Saisir un nombre entre 1 et 40."
      )
      return
    }
    setIsSavingEdit(true)
    setEditError(null)
    try {
      const updated = await deviceService.updateDevice(editingDevice.id, {
        name: editForm.name,
        type: editForm.type,
        gpio_pin: gpioPin,
        controlled_by_sensor_id: editForm.controlled_by_sensor_id ?? null,
        sensor_rules: editForm.sensor_rules ?? null,
      })
      setDevices((prev) => prev.map((d) => (d.id === updated.id ? { ...d, ...updated } : d)))
      setEditingDevice(null)
      fetchDevices()
    } catch (err) {
      setEditError(err instanceof Error ? err.message : "Erreur lors de la mise à jour")
    } finally {
      setIsSavingEdit(false)
    }
  }

  /** Mise à jour immédiate d'un appareil dans la liste (état/brillance) pour que l'UI réagisse sans attendre le refetch */
  const handleDeviceUpdated = (deviceId: number, patch: { state?: boolean; brightness?: number }) => {
    setDevices((prev) =>
      prev.map((d) => (d.id === deviceId ? { ...d, ...patch } : d))
    )
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <LoadingSpinner size="lg" text="Chargement des appareils..." />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
        <AlertCircle className="h-12 w-12 text-destructive" />
        <p className="text-muted-foreground">{error}</p>
        <Button onClick={fetchDevices}>Réessayer</Button>
      </div>
    )
  }

  if (isAdmin) {
    return (
      <div className="flex justify-center items-center min-h-[400px]">
        <LoadingSpinner size="lg" text="Redirection..." />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-balance">Appareils</h1>
          <p className="text-muted-foreground">{devices.length} appareil(s) configuré(s)</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={fetchDevices}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Actualiser
          </Button>
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <Button size="sm" onClick={() => setIsDialogOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Nouvel appareil
            </Button>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Ajouter un appareil</DialogTitle>
                <DialogDescription>Ajoutez un appareil (lumière, variateur ou prise) à votre domicile.</DialogDescription>
              </DialogHeader>
              <form onSubmit={handleCreate}>
                <div className="space-y-4 py-4">
                  {createError && (
                    <div className="p-3 rounded-lg bg-destructive/10 text-destructive text-sm">{createError}</div>
                  )}

                  <div className="space-y-2">
                    <Label htmlFor="name">Nom de l&apos;appareil</Label>
                    <Input
                      id="name"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      placeholder="Lampe du salon"
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="type">Type</Label>
                    <Select
                      value={formData.type}
                      onValueChange={(value: "light" | "dimmer" | "socket" | "sensor") =>
                        setFormData({ ...formData, type: value })
                      }
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {(isAdmin ? DEVICE_TYPES_WITH_SENSOR : DEVICE_TYPES_BASE).map((type) => (
                          <SelectItem key={type.value} value={type.value}>
                            {type.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="rpi">Contrôleur</Label>
                      {raspberryPis.length === 0 ? (
                        <div className="text-sm text-muted-foreground p-2 border rounded-md">
                          Aucun contrôleur disponible. Contactez l&apos;administrateur.
                        </div>
                      ) : (
                        <Select
                          value={String(formData.raspberry_pi_id)}
                          onValueChange={(value) => setFormData({ ...formData, raspberry_pi_id: Number.parseInt(value) })}
                        >
                          <SelectTrigger id="rpi">
                            <SelectValue placeholder="Choisir un contrôleur" />
                          </SelectTrigger>
                          <SelectContent>
                            {raspberryPis.map((rpi) => (
                              <SelectItem key={rpi.id} value={String(rpi.id)}>
                                {rpi.name} {rpi.location ? `(${rpi.location})` : ""}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      )}
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="gpio">Numéro d&apos;appareil</Label>
                      <Input
                        id="gpio"
                        type="number"
                        min="1"
                        max={formData.type === "sensor" ? 255 : 40}
                        value={formData.gpio_pin}
                        onChange={(e) => setFormData({ ...formData, gpio_pin: Number.parseInt(e.target.value) || 17 })}
                        required
                      />
                      <p className="text-xs text-muted-foreground">
                        {formData.type === "sensor"
                          ? "Node ID Z-Wave (1–255), ex. 5 pour MultiSensor 7."
                          : "Numéro indiqué sur le contrôleur pour cet appareil (souvent entre 1 et 40)."}
                      </p>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="location">Emplacement (optionnel)</Label>
                    <Input
                      id="location"
                      value={formData.location}
                      onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                      placeholder="Salon, Cuisine, Chambre..."
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)} disabled={isCreating}>
                    Annuler
                  </Button>
                  <Button type="submit" disabled={isCreating}>
                    {isCreating ? "Création..." : "Créer"}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Edit device dialog */}
      <Dialog open={!!editingDevice} onOpenChange={(open) => !open && setEditingDevice(null)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Modifier l&apos;appareil</DialogTitle>
            <DialogDescription>
              Nom, type, broche et pilotage par capteur (mouvement + luminosité).
            </DialogDescription>
          </DialogHeader>
          {editingDevice && (
            <form onSubmit={handleSaveEdit}>
              <div className="space-y-4 py-4">
                {editError && (
                  <div className="p-3 rounded-lg bg-destructive/10 text-destructive text-sm">{editError}</div>
                )}
                <div className="space-y-2">
                  <Label>Nom</Label>
                  <Input
                    value={editForm.name ?? ""}
                    onChange={(e) => setEditForm((f) => ({ ...f, name: e.target.value }))}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label>Type</Label>
                  <Select
                    value={editForm.type ?? "light"}
                    onValueChange={(v: Device["type"]) => setEditForm((f) => ({ ...f, type: v }))}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {DEVICE_TYPES_WITH_SENSOR.map((t) => (
                        <SelectItem key={t.value} value={t.value}>
                          {t.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Broche / Node ID</Label>
                  <Input
                    type="number"
                    min={1}
                    max={editForm.type === "sensor" ? 255 : 40}
                    value={editForm.gpio_pin ?? editingDevice?.gpio_pin ?? ""}
                    onChange={(e) => {
                      const v = e.target.value === "" ? undefined : Number(e.target.value)
                      setEditForm((f) => ({ ...f, gpio_pin: v }))
                    }}
                    placeholder={editForm.type === "sensor" ? "1–255 (node Z-Wave)" : "1–40"}
                  />
                </div>
                {(editForm.type === "light" || editForm.type === "dimmer") && (
                  <>
                    <div className="space-y-2">
                      <Label>Piloté par le capteur</Label>
                      <Select
                        value={editForm.controlled_by_sensor_id ? String(editForm.controlled_by_sensor_id) : "none"}
                        onValueChange={(v) =>
                          setEditForm((f) => ({
                            ...f,
                            controlled_by_sensor_id: v === "none" ? null : Number(v),
                          }))
                        }
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Aucun" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="none">Aucun</SelectItem>
                          {devices
                            .filter((d) => d.type === "sensor")
                            .map((d) => (
                              <SelectItem key={d.id} value={String(d.id)}>
                                {d.name}
                              </SelectItem>
                            ))}
                        </SelectContent>
                      </Select>
                    </div>
                    {editForm.controlled_by_sensor_id != null && editForm.controlled_by_sensor_id > 0 && (
                      <div className="rounded-lg border p-3 space-y-3 text-sm">
                        <Label>Règles capteur</Label>
                        <div className="grid grid-cols-2 gap-2">
                          <div>
                            <span className="text-muted-foreground">Mouvement : intensité</span>
                            <Input
                              type="number"
                              min={0}
                              max={100}
                              value={editForm.sensor_rules?.motion?.on_brightness ?? 80}
                              onChange={(e) =>
                                setEditForm((f) => ({
                                  ...f,
                                  sensor_rules: {
                                    ...f.sensor_rules,
                                    motion: {
                                      ...f.sensor_rules?.motion,
                                      on_brightness: Number(e.target.value) || 80,
                                    },
                                  },
                                }))
                              }
                            />
                          </div>
                          <div>
                            <span className="text-muted-foreground">Éteindre après (s)</span>
                            <Input
                              type="number"
                              min={0}
                              value={editForm.sensor_rules?.motion?.off_after_seconds ?? 300}
                              onChange={(e) =>
                                setEditForm((f) => ({
                                  ...f,
                                  sensor_rules: {
                                    ...f.sensor_rules,
                                    motion: {
                                      ...f.sensor_rules?.motion,
                                      off_after_seconds: Number(e.target.value) || 300,
                                    },
                                  },
                                }))
                              }
                            />
                          </div>
                          <div>
                            <span className="text-muted-foreground">Si luminosité &lt; (lux)</span>
                            <Input
                              type="number"
                              min={0}
                              value={editForm.sensor_rules?.illuminance?.below_lux ?? 100}
                              onChange={(e) =>
                                setEditForm((f) => ({
                                  ...f,
                                  sensor_rules: {
                                    ...f.sensor_rules,
                                    illuminance: {
                                      ...f.sensor_rules?.illuminance,
                                      below_lux: Number(e.target.value) || 100,
                                    },
                                  },
                                }))
                              }
                            />
                          </div>
                          <div>
                            <span className="text-muted-foreground">→ intensité</span>
                            <Input
                              type="number"
                              min={0}
                              max={100}
                              value={editForm.sensor_rules?.illuminance?.brightness ?? 60}
                              onChange={(e) =>
                                setEditForm((f) => ({
                                  ...f,
                                  sensor_rules: {
                                    ...f.sensor_rules,
                                    illuminance: {
                                      ...f.sensor_rules?.illuminance,
                                      brightness: Number(e.target.value) || 60,
                                    },
                                  },
                                }))
                              }
                            />
                          </div>
                          <div className="col-span-2">
                            <span className="text-muted-foreground">Si luminosité &gt; (lux) → éteindre</span>
                            <Input
                              type="number"
                              min={0}
                              value={editForm.sensor_rules?.illuminance?.above_lux ?? 2000}
                              onChange={(e) =>
                                setEditForm((f) => ({
                                  ...f,
                                  sensor_rules: {
                                    ...f.sensor_rules,
                                    illuminance: {
                                      ...f.sensor_rules?.illuminance,
                                      above_lux: Number(e.target.value) || 2000,
                                    },
                                  },
                                }))
                              }
                            />
                          </div>
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setEditingDevice(null)} disabled={isSavingEdit}>
                  Annuler
                </Button>
                <Button type="submit" disabled={isSavingEdit}>
                  {isSavingEdit ? "Enregistrement..." : "Enregistrer"}
                </Button>
              </DialogFooter>
            </form>
          )}
        </DialogContent>
      </Dialog>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Rechercher un appareil..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>
        <div className="flex gap-2">
          <Select value={filterLocation} onValueChange={setFilterLocation}>
            <SelectTrigger className="min-w-[180px]">
              <Filter className="h-4 w-4 mr-2 shrink-0" />
              <SelectValue placeholder="Lieu" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Tous les lieux</SelectItem>
              {locations.map((loc) => (
                <SelectItem key={loc} value={loc!}>
                  {loc}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={filterType} onValueChange={setFilterType}>
            <SelectTrigger className="min-w-[180px]">
              <SelectValue placeholder="Type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Tous les types</SelectItem>
              {(isAdmin ? DEVICE_TYPES_WITH_SENSOR : DEVICE_TYPES_BASE).map((type) => (
                <SelectItem key={type.value} value={type.value}>
                  {type.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Devices Grid */}
      {filteredDevices.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="p-4 rounded-full bg-muted mb-4">
            <Lightbulb className="h-8 w-8 text-muted-foreground" />
          </div>
          <h3 className="font-medium mb-1">Aucun appareil trouvé</h3>
          <p className="text-sm text-muted-foreground mb-4">
            {devices.length === 0
              ? "Ajoutez votre premier appareil pour commencer"
              : "Aucun appareil ne correspond aux filtres"}
          </p>
          {devices.length === 0 && (
            <Button onClick={() => setIsDialogOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Ajouter un appareil
            </Button>
          )}
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredDevices.map((device) =>
            isAdmin ? (
              <DeviceCard
                key={device.id}
                device={device}
                onUpdate={fetchDevices}
                onDelete={handleDelete}
                onDeviceUpdated={handleDeviceUpdated}
                onEdit={openEdit}
              />
            ) : (
              <DeviceCardUser
                key={device.id}
                device={device}
                onUpdate={fetchDevices}
                onDelete={handleDelete}
                onDeviceUpdated={handleDeviceUpdated}
              />
            ),
          )}
        </div>
      )}
    </div>
  )
}

export default function DevicesPage() {
  return (
    <Suspense fallback={<LoadingSpinner size="lg" text="Chargement..." />}>
      <DevicesContent />
    </Suspense>
  )
}
