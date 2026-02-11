"use client"

import { useEffect, useState, useCallback } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { LoadingSpinner } from "@/components/loading-spinner"
import { AdminOnly } from "@/components/admin-only"
import { useIsAdmin } from "@/hooks/use-is-admin"
import { useRouter } from "next/navigation"
import { raspberryPiService, type RaspberryPi, type RaspberryPiCreate, type RaspberryPiUpdate } from "@/lib/services/raspberry-pi-service"
import { Cpu, Plus, RefreshCw, AlertCircle, Trash2, Edit, Copy, CheckCircle, XCircle } from "lucide-react"
import { cn } from "@/lib/utils"
import { toast } from "@/hooks/use-toast"

export default function AdminRaspberryPisPage() {
  const isAdmin = useIsAdmin()
  const router = useRouter()
  const [raspberryPis, setRaspberryPis] = useState<RaspberryPi[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [isCreating, setIsCreating] = useState(false)
  const [isUpdating, setIsUpdating] = useState(false)
  const [editingRpi, setEditingRpi] = useState<RaspberryPi | null>(null)
  const [copiedKey, setCopiedKey] = useState<number | null>(null)

  const [formData, setFormData] = useState<RaspberryPiCreate>({
    name: "",
    location: "",
    ip_address: "",
  })
  const [isOnline, setIsOnline] = useState(false)
  const [newApiKey, setNewApiKey] = useState("")

  useEffect(() => {
    if (!isAdmin) {
      router.push("/dashboard")
    }
  }, [isAdmin, router])

  const fetchRaspberryPis = useCallback(async () => {
    try {
      const data = await raspberryPiService.getRaspberryPis()
      setRaspberryPis(data)
      setError(null)
    } catch {
      setError("Erreur lors du chargement des Raspberry Pi")
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    if (isAdmin) {
      fetchRaspberryPis()
    }
  }, [isAdmin, fetchRaspberryPis])

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsCreating(true)

    try {
      await raspberryPiService.createRaspberryPi(formData)
      setIsDialogOpen(false)
      setFormData({ name: "", location: "", ip_address: "" })
      setEditingRpi(null)
      fetchRaspberryPis()
      toast({
        title: "Raspberry Pi créé",
        description: "Le Raspberry Pi a été enregistré avec succès.",
      })
    } catch (err) {
      toast({
        variant: "destructive",
        title: "Erreur",
        description: err instanceof Error ? err.message : "Erreur lors de la création",
      })
    } finally {
      setIsCreating(false)
    }
  }

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!editingRpi) return

    setIsUpdating(true)

    try {
      const updateData: RaspberryPiUpdate = {
        name: formData.name,
        location: formData.location || undefined,
        ip_address: formData.ip_address,
        is_online: isOnline,
        ...(newApiKey.trim() ? { api_key: newApiKey.trim() } : {}),
      }
      await raspberryPiService.updateRaspberryPi(editingRpi.id, updateData)
      setIsDialogOpen(false)
      setFormData({ name: "", location: "", ip_address: "" })
      setIsOnline(false)
      setNewApiKey("")
      setEditingRpi(null)
      fetchRaspberryPis()
      toast({
        title: "Raspberry Pi modifié",
        description: "Le Raspberry Pi a été mis à jour avec succès.",
      })
    } catch (err) {
      toast({
        variant: "destructive",
        title: "Erreur",
        description: err instanceof Error ? err.message : "Erreur lors de la modification",
      })
    } finally {
      setIsUpdating(false)
    }
  }

  const handleDelete = async (id: number) => {
    if (!window.confirm("Êtes-vous sûr de vouloir supprimer ce Raspberry Pi ?")) {
      return
    }

    try {
      await raspberryPiService.deleteRaspberryPi(id)
      fetchRaspberryPis()
      toast({
        title: "Raspberry Pi supprimé",
        description: "Le Raspberry Pi a été supprimé avec succès.",
      })
    } catch (err) {
      toast({
        variant: "destructive",
        title: "Erreur",
        description: err instanceof Error ? err.message : "Erreur lors de la suppression",
      })
    }
  }

  const handleCopyKey = async (apiKey: string, id: number) => {
    try {
      // Vérifier que navigator.clipboard est disponible
      if (typeof navigator !== "undefined" && navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(apiKey)
        setCopiedKey(id)
        setTimeout(() => setCopiedKey(null), 2000)
        toast({
          title: "Clé API copiée",
          description: "La clé API a été copiée dans le presse-papiers.",
        })
      } else {
        // Fallback pour les navigateurs qui ne supportent pas clipboard API
        const textArea = document.createElement("textarea")
        textArea.value = apiKey
        textArea.style.position = "fixed"
        textArea.style.left = "-999999px"
        document.body.appendChild(textArea)
        textArea.select()
        document.execCommand("copy")
        document.body.removeChild(textArea)
        setCopiedKey(id)
        setTimeout(() => setCopiedKey(null), 2000)
        toast({
          title: "Clé API copiée",
          description: "La clé API a été copiée dans le presse-papiers.",
        })
      }
    } catch (err) {
      toast({
        variant: "destructive",
        title: "Erreur",
        description: "Impossible de copier la clé API dans le presse-papiers.",
      })
    }
  }

  const openCreateDialog = () => {
    setEditingRpi(null)
    setFormData({ name: "", location: "", ip_address: "" })
    setIsOnline(false)
    setNewApiKey("")
    setIsDialogOpen(true)
  }

  const openEditDialog = (rpi: RaspberryPi) => {
    setEditingRpi(rpi)
    setFormData({
      name: rpi.name,
      location: rpi.location || "",
      ip_address: rpi.ip_address,
    })
    setIsOnline(rpi.is_online)
    setNewApiKey("")
    setIsDialogOpen(true)
  }

  if (!isAdmin) {
    return null
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <LoadingSpinner size="lg" text="Chargement des Raspberry Pi..." />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
        <AlertCircle className="h-12 w-12 text-destructive" />
        <p className="text-muted-foreground">{error}</p>
        <Button onClick={fetchRaspberryPis}>Réessayer</Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-balance">Gestion Raspberry Pi</h1>
          <p className="text-muted-foreground">{raspberryPis.length} Raspberry Pi enregistré(s)</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={fetchRaspberryPis}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Actualiser
          </Button>
          <Button size="sm" onClick={openCreateDialog}>
            <Plus className="h-4 w-4 mr-2" />
            Nouveau Raspberry Pi
          </Button>
        </div>
      </div>

      {/* Raspberry Pi Grid */}
      {raspberryPis.length === 0 ? (
        <Card>
          <CardContent className="py-16 text-center">
            <Cpu className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="font-medium mb-1">Aucun Raspberry Pi</h3>
            <p className="text-sm text-muted-foreground mb-4">Ajoutez votre premier Raspberry Pi pour commencer</p>
            <Button onClick={openCreateDialog}>
              <Plus className="h-4 w-4 mr-2" />
              Ajouter un Raspberry Pi
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {raspberryPis.map((rpi) => (
            <Card key={rpi.id} className={cn(rpi.is_online && "ring-2 ring-green-500/50")}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className={cn("p-2 rounded-xl", rpi.is_online ? "bg-green-500/20" : "bg-muted")}>
                      <Cpu className={cn("h-5 w-5", rpi.is_online ? "text-green-500" : "text-muted-foreground")} />
                    </div>
                    <div>
                      <CardTitle className="text-lg">{rpi.name}</CardTitle>
                      {rpi.location && (
                        <CardDescription className="mt-1">{rpi.location}</CardDescription>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-1">
                    {rpi.is_online ? (
                      <CheckCircle className="h-5 w-5 text-green-500" />
                    ) : (
                      <XCircle className="h-5 w-5 text-destructive" />
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="text-sm space-y-1">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">IP:</span>
                    <span className="font-mono">{rpi.ip_address ?? "—"}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Appareils:</span>
                    <span>{rpi.device_count ?? 0}</span>
                  </div>
                  {rpi.device_ids && rpi.device_ids.length > 0 && (
                    <div className="flex justify-between items-start gap-2">
                      <span className="text-muted-foreground shrink-0">IDs appareils:</span>
                      <span className="font-mono text-xs break-all" title="IDs pour debug">
                        {rpi.device_ids.join(", ")}
                      </span>
                    </div>
                  )}
                  <div className="flex justify-between items-center">
                    <span className="text-muted-foreground">Clé API:</span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleCopyKey(rpi.api_key, rpi.id)}
                      className="h-6 px-2"
                    >
                      {copiedKey === rpi.id ? (
                        <CheckCircle className="h-3 w-3 text-green-500" />
                      ) : (
                        <Copy className="h-3 w-3" />
                      )}
                    </Button>
                  </div>
                </div>
                <div className="pt-2 border-t flex gap-2">
                  <Button 
                    variant="outline" 
                    size="sm" 
                    className="flex-1" 
                    onClick={() => openEditDialog(rpi)}
                  >
                    <Edit className="h-4 w-4 mr-1" />
                    Modifier
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDelete(rpi.id)}
                    className="text-destructive hover:bg-destructive hover:text-white"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Create/Edit Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={(open) => {
        setIsDialogOpen(open)
        if (!open) {
          setEditingRpi(null)
          setFormData({ name: "", location: "", ip_address: "" })
          setIsOnline(false)
          setNewApiKey("")
        }
      }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {editingRpi ? "Modifier un Raspberry Pi" : "Ajouter un Raspberry Pi"}
            </DialogTitle>
            <DialogDescription>
              {editingRpi 
                ? "Modifiez les informations du Raspberry Pi" 
                : "Enregistrez un nouveau Raspberry Pi dans le système"}
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={editingRpi ? handleUpdate : handleCreate}>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="name">Nom</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="RPi Salon"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="location">Emplacement (optionnel)</Label>
                <Input
                  id="location"
                  value={formData.location}
                  onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                  placeholder="Salon"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="ip_address">Adresse IP</Label>
                <Input
                  id="ip_address"
                  value={formData.ip_address}
                  onChange={(e) => setFormData({ ...formData, ip_address: e.target.value })}
                  placeholder="192.168.1.100"
                  required
                />
                <p className="text-xs text-muted-foreground">
                  Le backend utilise cette adresse pour vérifier si le RPi est en ligne (ping GET / sur le port 5000). 
                  Si <em>is_online</em> reste à false, vérifiez que l’IP correspond bien à celle du RPi (ex. 10.109.150.133).
                </p>
              </div>
              {editingRpi && (
                <>
                  <div className="space-y-2">
                    <Label htmlFor="new_api_key">Nouvelle clé API (optionnel)</Label>
                    <Input
                      id="new_api_key"
                      type="password"
                      autoComplete="off"
                      value={newApiKey}
                      onChange={(e) => setNewApiKey(e.target.value)}
                      placeholder="Ex: smarthome2025 (celle du .env du RPi)"
                    />
                    <p className="text-xs text-muted-foreground">
                      Renseignez la clé définie dans RASPBERRY_API_KEY sur le RPi pour que heartbeat et appels backend correspondent.
                    </p>
                  </div>
                  <div className="flex items-center justify-between space-x-2 py-2">
                    <Label htmlFor="is_online" className="flex-1">
                      Statut en ligne
                    </Label>
                    <Switch
                      id="is_online"
                      checked={isOnline}
                      onCheckedChange={setIsOnline}
                    />
                  </div>
                </>
              )}
            </div>
            <DialogFooter>
              <Button 
                type="button" 
                variant="outline" 
                onClick={() => {
                  setIsDialogOpen(false)
                  setEditingRpi(null)
                  setFormData({ name: "", location: "", ip_address: "" })
                  setIsOnline(false)
                  setNewApiKey("")
                }} 
                disabled={isCreating || isUpdating}
              >
                Annuler
              </Button>
              <Button type="submit" disabled={isCreating || isUpdating}>
                {isCreating ? "Création..." : isUpdating ? "Modification..." : editingRpi ? "Modifier" : "Créer"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}
