"use client"

import type React from "react"
import { Suspense } from "react"

import { useEffect, useState, useCallback } from "react"
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
import type { Device } from "@/lib/types"
import { Plus, RefreshCw, Search, AlertCircle, Lightbulb, Filter } from "lucide-react"

const DEVICE_TYPES = [
  { value: "light", label: "Lumière" },
  { value: "dimmer", label: "Variateur" },
  { value: "socket", label: "Prise" },
]

interface NewDeviceForm {
  name: string
  type: "light" | "dimmer" | "socket"
  raspberry_pi_id: number
  gpio_pin: number
  location: string
}

function DevicesContent() {
  const isAdmin = useIsAdmin()
  const [devices, setDevices] = useState<Device[]>([])
  const [filteredDevices, setFilteredDevices] = useState<Device[]>([])
  const [raspberryPis, setRaspberryPis] = useState<AvailableRaspberryPi[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [isCreating, setIsCreating] = useState(false)
  const [createError, setCreateError] = useState<string | null>(null)

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
      setDevices(data)
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

    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      result = result.filter((d) => d.name.toLowerCase().includes(query) || d.location?.toLowerCase().includes(query))
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
                <DialogDescription>Configurez un nouvel appareil connecté à votre système.</DialogDescription>
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
                      onValueChange={(value: "light" | "dimmer" | "socket") =>
                        setFormData({ ...formData, type: value })
                      }
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {DEVICE_TYPES.map((type) => (
                          <SelectItem key={type.value} value={type.value}>
                            {type.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="rpi">Raspberry Pi</Label>
                      {raspberryPis.length === 0 ? (
                        <div className="text-sm text-muted-foreground p-2 border rounded-md">
                          Aucun Raspberry Pi disponible. Veuillez contacter un administrateur.
                        </div>
                      ) : (
                        <Select
                          value={String(formData.raspberry_pi_id)}
                          onValueChange={(value) => setFormData({ ...formData, raspberry_pi_id: Number.parseInt(value) })}
                        >
                          <SelectTrigger id="rpi">
                            <SelectValue placeholder="Sélectionner un Raspberry Pi" />
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
                      <Label htmlFor="gpio">Broche / Node ID</Label>
                      <Input
                        id="gpio"
                        type="number"
                        min="1"
                        max="40"
                        value={formData.gpio_pin}
                        onChange={(e) => setFormData({ ...formData, gpio_pin: Number.parseInt(e.target.value) || 17 })}
                        required
                      />
                      <p className="text-xs text-muted-foreground">
                        Sur un RPi Z-Wave : node_id du nœud (ex. 3 pour une ampoule). Sinon numéro GPIO (1–40).
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
            <SelectTrigger className="w-[140px]">
              <Filter className="h-4 w-4 mr-2" />
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
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="Type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Tous les types</SelectItem>
              {DEVICE_TYPES.map((type) => (
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
              />
            ) : (
              <DeviceCardUser
                key={device.id}
                device={device}
                onUpdate={fetchDevices}
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
