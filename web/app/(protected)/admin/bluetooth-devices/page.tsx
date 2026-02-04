"use client"

import { useEffect, useState, useCallback } from "react"
import { useRouter } from "next/navigation"
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
import { useIsAdmin } from "@/hooks/use-is-admin"
import { api } from "@/lib/api"
import {
  bluetoothDeviceService,
  type BluetoothDevice,
  type BluetoothDeviceCreate,
} from "@/lib/services/bluetooth-device-service"
import { Smartphone, Plus, Trash2, AlertCircle, RefreshCw } from "lucide-react"
import { toast } from "@/hooks/use-toast"

interface AdminUser {
  id: number
  username: string
  email: string | null
  role: string
}

export default function AdminBluetoothDevicesPage() {
  const isAdmin = useIsAdmin()
  const router = useRouter()
  const [devices, setDevices] = useState<BluetoothDevice[]>([])
  const [users, setUsers] = useState<AdminUser[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [isCreating, setIsCreating] = useState(false)
  const [formData, setFormData] = useState<BluetoothDeviceCreate>({
    user_id: 0,
    mac_address: "",
    device_name: "",
    device_type: "phone",
  })

  const fetchDevices = useCallback(async () => {
    try {
      const data = await bluetoothDeviceService.list()
      setDevices(data)
      setError(null)
    } catch {
      setError("Erreur lors du chargement des appareils Bluetooth")
    } finally {
      setIsLoading(false)
    }
  }, [])

  const fetchUsers = useCallback(async () => {
    try {
      const data = await api.get<AdminUser[]>("/api/admin/users")
      setUsers(data)
    } catch {
      // ignore
    }
  }, [])

  useEffect(() => {
    if (!isAdmin) {
      router.push("/dashboard")
    }
  }, [isAdmin, router])

  useEffect(() => {
    if (isAdmin) {
      fetchDevices()
      fetchUsers()
    }
  }, [isAdmin, fetchDevices, fetchUsers])

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.user_id || !formData.mac_address.trim()) {
      toast({
        variant: "destructive",
        title: "Champs requis",
        description: "Sélectionnez un utilisateur et saisissez l'adresse MAC.",
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
      await bluetoothDeviceService.create({
        user_id: formData.user_id,
        mac_address: mac,
        device_name: formData.device_name || null,
        device_type: formData.device_type || null,
      })
      setIsDialogOpen(false)
      setFormData({ user_id: 0, mac_address: "", device_name: "", device_type: "phone" })
      fetchDevices()
      toast({
        title: "Appareil ajouté",
        description: "La MAC est maintenant associée à l'utilisateur. Les détections du RPi seront enregistrées avec ce compte.",
      })
    } catch (err) {
      toast({
        variant: "destructive",
        title: "Erreur",
        description: err instanceof Error ? err.message : "Impossible d'ajouter l'appareil",
      })
    } finally {
      setIsCreating(false)
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm("Supprimer cette association MAC → utilisateur ?")) return
    try {
      await bluetoothDeviceService.delete(id)
      fetchDevices()
      toast({ title: "Appareil supprimé", description: "L'association a été retirée." })
    } catch (err) {
      toast({
        variant: "destructive",
        title: "Erreur",
        description: err instanceof Error ? err.message : "Impossible de supprimer",
      })
    }
  }

  if (!isAdmin) return null

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Appareils Bluetooth</h1>
          <p className="text-muted-foreground">
            Associez les adresses MAC (téléphones, montres) aux utilisateurs (jean, mehdi…). Quand le RPi capteur détecte
            une de ces MAC, la présence est enregistrée automatiquement et l&apos;IA peut l&apos;utiliser.
          </p>
        </div>
        <Button onClick={() => setIsDialogOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Associer un appareil
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Smartphone className="h-5 w-5" />
            Associations MAC → utilisateur
          </CardTitle>
          <CardDescription>
            Liste des appareils Bluetooth enregistrés. Le RPi (10.109.150.133) envoie les MAC détectées au backend ;
            si la MAC figure ici, la présence est liée à l&apos;utilisateur.
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
              Aucun appareil associé. Cliquez sur &quot;Associer un appareil&quot; pour lier une MAC à un utilisateur (ex. Galaxy J7
              → jean).
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
                    <span className="text-muted-foreground">→</span>
                    <span className="font-medium">{d.username}</span>
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
            <DialogTitle>Associer un appareil Bluetooth à un utilisateur</DialogTitle>
            <DialogDescription>
              Saisissez l&apos;adresse MAC du téléphone ou de la montre (ex. 94:7B:E7:A1:E7:A0). Lorsque le RPi capteur
              détectera cette MAC à portée, la présence sera enregistrée pour l&apos;utilisateur choisi.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreate}>
            <div className="space-y-4 py-4">
              <div>
                <Label>Utilisateur</Label>
                <Select
                  value={formData.user_id ? String(formData.user_id) : ""}
                  onValueChange={(v) => setFormData((prev) => ({ ...prev, user_id: Number(v) }))}
                  required
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Choisir (jean, mehdi…)" />
                  </SelectTrigger>
                  <SelectContent>
                    {users.map((u) => (
                      <SelectItem key={u.id} value={String(u.id)}>
                        {u.username}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
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
                  placeholder="Galaxy J7 de Jean"
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
                {isCreating ? "Ajout…" : "Associer"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}
