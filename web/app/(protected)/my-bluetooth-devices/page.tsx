"use client"

import { useEffect, useState, useCallback } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
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
import { LoadingSpinner } from "@/components/loading-spinner"
import {
  bluetoothDeviceService,
  type BluetoothDevice,
  type MyBluetoothDeviceCreate,
} from "@/lib/services/bluetooth-device-service"
import { presenceService, type RecentDetection } from "@/lib/services/presence-service"
import { Smartphone, Plus, Trash2, AlertCircle, RefreshCw, Radio, Link2 } from "lucide-react"
import { toast } from "@/hooks/use-toast"

export default function MyBluetoothDevicesPage() {
  const [devices, setDevices] = useState<BluetoothDevice[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [isCreating, setIsCreating] = useState(false)
  const [formData, setFormData] = useState<MyBluetoothDeviceCreate>({
    mac_address: "",
    device_name: "",
    device_type: "phone",
  })
  const [recentDetections, setRecentDetections] = useState<RecentDetection[]>([])
  const [loadingRecent, setLoadingRecent] = useState(false)
  const [claimingMac, setClaimingMac] = useState<string | null>(null)

  const fetchDevices = useCallback(async () => {
    try {
      const data = await bluetoothDeviceService.listMy()
      setDevices(data)
      setError(null)
    } catch {
      setError("Erreur lors du chargement de vos appareils Bluetooth")
    } finally {
      setIsLoading(false)
    }
  }, [])

  const fetchRecentDetections = useCallback(async () => {
    setLoadingRecent(true)
    try {
      const data = await presenceService.getRecentDetections(2)
      setRecentDetections(data)
    } catch {
      setRecentDetections([])
    } finally {
      setLoadingRecent(false)
    }
  }, [])

  useEffect(() => {
    fetchDevices()
  }, [fetchDevices])

  useEffect(() => {
    fetchRecentDetections()
    const t = setInterval(fetchRecentDetections, 15000)
    return () => clearInterval(t)
  }, [fetchRecentDetections])

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.mac_address.trim()) {
      toast({
        variant: "destructive",
        title: "Champ requis",
        description: "Saisissez l'adresse MAC de votre appareil.",
      })
      return
    }
    const mac = formData.mac_address.trim().toUpperCase().replace(/-/g, ":")
    if (!/^([0-9A-F]{2}:){5}[0-9A-F]{2}$/.test(mac)) {
      toast({
        variant: "destructive",
        title: "MAC invalide",
        description: "Format attendu : AA:BB:CC:DD:EE:FF (ex: 94:7B:E7:A1:E7:A0)",
      })
      return
    }
    setIsCreating(true)
    try {
      await bluetoothDeviceService.createMy({
        mac_address: mac,
        device_name: formData.device_name || null,
        device_type: formData.device_type || null,
      })
      setIsDialogOpen(false)
      setFormData({ mac_address: "", device_name: "", device_type: "phone" })
      fetchDevices()
      toast({
        title: "Appareil ajouté",
        description:
          "Votre appareil est enregistré. Quand le RPi capteur détectera cette MAC à portée, votre présence sera enregistrée.",
      })
    } catch (err: unknown) {
      const msg =
        err && typeof err === "object" && "detail" in err && typeof (err as { detail: string }).detail === "string"
        ? (err as { detail: string }).detail
        : "Impossible d'ajouter l'appareil"
      toast({
        variant: "destructive",
        title: "Erreur",
        description: msg,
      })
    } finally {
      setIsCreating(false)
    }
  }

  const handleClaimDetection = async (det: RecentDetection) => {
    setClaimingMac(det.device_mac_address)
    try {
      await bluetoothDeviceService.createMy({
        mac_address: det.device_mac_address,
        device_name: det.device_name || null,
        device_type: "phone",
      })
      fetchDevices()
      setRecentDetections((prev) => prev.filter((d) => d.device_mac_address !== det.device_mac_address))
      toast({
        title: "Appareil lié",
        description: "Cet appareil est maintenant associé à votre compte. Votre présence sera reconnue quand il est à portée.",
      })
    } catch (err: unknown) {
      const msg =
        err && typeof err === "object" && "detail" in err && typeof (err as { detail: string }).detail === "string"
          ? (err as { detail: string }).detail
          : "Impossible de lier l'appareil"
      toast({ variant: "destructive", title: "Erreur", description: msg })
    } finally {
      setClaimingMac(null)
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm("Retirer cet appareil de votre compte ?")) return
    try {
      await bluetoothDeviceService.deleteMy(id)
      fetchDevices()
      toast({ title: "Appareil retiré", description: "L'appareil n'est plus associé à votre compte." })
    } catch (err) {
      toast({
        variant: "destructive",
        title: "Erreur",
        description: err instanceof Error ? err.message : "Impossible de supprimer",
      })
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Mon appareil Bluetooth</h1>
          <p className="text-muted-foreground">
            Enregistrez l&apos;adresse MAC de votre téléphone ou montre. Quand le RPi capteur détecte cette MAC à
            portée, votre présence est enregistrée et l&apos;IA peut l&apos;utiliser pour le scénario.
          </p>
        </div>
        <Button onClick={() => setIsDialogOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Ajouter mon appareil
        </Button>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Radio className="h-5 w-5" />
              Appareils détectés à l&apos;instant
            </CardTitle>
            <CardDescription className="space-y-2">
              <span className="block">
                Appareils vus par le RPi dans les 2 dernières minutes. Cliquez sur &quot;Lier à mon compte&quot; pour
                associer l&apos;un d&apos;eux à votre compte.
              </span>
              <span className="block mt-2 rounded-md bg-muted/80 p-2 text-xs">
                <strong>Votre téléphone n&apos;apparaît pas avec l&apos;adresse des Réglages (ex. 94:7B:E7:A1:E7:A0) ?</strong>
                {" "}Sous Android (Samsung, etc.), le Bluetooth utilise souvent une <strong>adresse aléatoire</strong> en BLE :
                le RPi voit donc une autre MAC. Pour trouver votre J7 : éteignez le Bluetooth du téléphone → Rafraîchir →
                une adresse disparaît ; rallumez le Bluetooth et liez cette adresse. Sinon, utilisez &quot;Ajouter mon appareil&quot; et
                saisissez 94:7B:E7:A1:E7:A0 (ça fonctionnera si le téléphone l&apos;annonce un jour).
              </span>
            </CardDescription>
          </div>
          <Button variant="outline" size="sm" onClick={fetchRecentDetections} disabled={loadingRecent}>
            <RefreshCw className={`h-4 w-4 mr-1 ${loadingRecent ? "animate-spin" : ""}`} />
            Rafraîchir
          </Button>
        </CardHeader>
        <CardContent>
          {loadingRecent && recentDetections.length === 0 ? (
            <div className="flex justify-center py-6">
              <LoadingSpinner size="sm" />
            </div>
          ) : recentDetections.length === 0 ? (
            <p className="text-muted-foreground py-6 text-center text-sm">
              Aucun appareil détecté récemment. Assurez-vous que le script BLE tourne sur le RPi et que votre
              téléphone a le Bluetooth activé à portée.
            </p>
          ) : (
            <div className="space-y-2">
              {recentDetections.map((det) => (
                <div
                  key={det.device_mac_address}
                  className="flex flex-wrap items-center justify-between gap-2 rounded-lg border p-3"
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-mono text-sm">{det.device_mac_address}</span>
                    {det.device_name && (
                      <span className="text-muted-foreground text-sm">({det.device_name})</span>
                    )}
                    {det.signal_strength != null && (
                      <span className="text-xs text-muted-foreground">RSSI {det.signal_strength}</span>
                    )}
                  </div>
                  <Button
                    size="sm"
                    onClick={() => handleClaimDetection(det)}
                    disabled={claimingMac !== null}
                  >
                    <Link2 className="h-4 w-4 mr-1" />
                    {claimingMac === det.device_mac_address ? "Liaison…" : "Lier à mon compte"}
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Smartphone className="h-5 w-5" />
            Mes appareils enregistrés
          </CardTitle>
          <CardDescription>
            Appareils associés à votre compte pour la détection de présence. Ils apparaissent aussi dans la liste
            Admin → Appareils BT pour les administrateurs.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex justify-center py-8">
              <LoadingSpinner size="lg" />
            </div>
          ) : error ? (
            <div className="flex flex-col items-center gap-4 py-8">
              <AlertCircle className="h-12 w-12 text-destructive" />
              <p className="text-muted-foreground">{error}</p>
              <Button onClick={fetchDevices}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Réessayer
              </Button>
            </div>
          ) : devices.length === 0 ? (
            <p className="text-muted-foreground py-8 text-center">
              Aucun appareil. Cliquez sur &quot;Ajouter mon appareil&quot; et saisissez l&apos;adresse MAC de votre
              téléphone (réglages → À propos → Adresse Bluetooth).
            </p>
          ) : (
            <div className="space-y-2">
              {devices.map((d) => (
                <div
                  key={d.id}
                  className="flex flex-wrap items-center justify-between gap-2 rounded-lg border p-3"
                >
                  <div className="flex flex-wrap items-center gap-3">
                    <span className="font-mono text-sm">{d.mac_address}</span>
                    {d.device_name && (
                      <span className="text-muted-foreground text-sm">({d.device_name})</span>
                    )}
                    {d.device_type && (
                      <span className="text-xs bg-muted px-2 py-0.5 rounded">{d.device_type}</span>
                    )}
                  </div>
                  <Button variant="ghost" size="sm" onClick={() => handleDelete(d.id)}>
                    <Trash2 className="h-4 w-4 text-destructive" />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Ajouter mon appareil Bluetooth</DialogTitle>
            <DialogDescription>
              Saisissez l&apos;adresse MAC de votre téléphone ou montre (ex. 94:7B:E7:A1:E7:A0). Elle sera associée à
              votre compte pour la détection de présence.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreate}>
            <div className="space-y-4 py-4">
              <div>
                <Label>Adresse MAC (AA:BB:CC:DD:EE:FF)</Label>
                <Input
                  placeholder="94:7B:E7:A1:E7:A0"
                  value={formData.mac_address}
                  onChange={(e) => setFormData((prev) => ({ ...prev, mac_address: e.target.value }))}
                  className="font-mono"
                />
              </div>
              <div>
                <Label>Nom du device (optionnel)</Label>
                <Input
                  placeholder="Mon Galaxy"
                  value={formData.device_name || ""}
                  onChange={(e) => setFormData((prev) => ({ ...prev, device_name: e.target.value }))}
                />
              </div>
              <div>
                <Label>Type (optionnel)</Label>
                <Select
                  value={formData.device_type || "phone"}
                  onValueChange={(v) => setFormData((prev) => ({ ...prev, device_type: v }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="phone">Téléphone</SelectItem>
                    <SelectItem value="watch">Montre</SelectItem>
                    <SelectItem value="headphones">Écouteurs</SelectItem>
                    <SelectItem value="other">Autre</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>
                Annuler
              </Button>
              <Button type="submit" disabled={isCreating}>
                {isCreating ? "Ajout…" : "Ajouter"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}
