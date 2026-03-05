"use client"

import type React from "react"

import { useEffect, useState, useCallback } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
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
import { RuleCardUser } from "@/components/rule-card-user"
import { ruleService } from "@/lib/services/rule-service"
import { deviceService } from "@/lib/services/device-service"
import { useIsAdmin } from "@/hooks/use-is-admin"
import type { Rule, Device } from "@/lib/types"
import { Plus, RefreshCw, Settings2, AlertCircle, Filter } from "lucide-react"

interface RuleFormData {
  name: string
  description: string
  enabled: boolean
  priority: number
  // Temps
  useTime: boolean
  startTime: string
  endTime: string
  // Présence
  presenceMode: "any" | "present" | "absent"
  // Luminosité
  useLight: boolean
  lightOperator: "<" | ">" | "="
  lightValue: string
  // Action
  deviceId: number | null
  actionType: "turn_on" | "turn_off" | "set_brightness"
  brightness: number
}

const EMPTY_FORM: RuleFormData = {
  name: "",
  description: "",
  enabled: true,
  priority: 5,
  useTime: true,
  startTime: "08:00",
  endTime: "18:00",
  presenceMode: "present",
  useLight: false,
  lightOperator: "<",
  lightValue: "100",
  deviceId: null,
  actionType: "set_brightness",
  brightness: 50,
}

export default function RulesPage() {
  const isAdmin = useIsAdmin()
  const router = useRouter()

  const [rules, setRules] = useState<Rule[]>([])
  const [filteredRules, setFilteredRules] = useState<Rule[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [devices, setDevices] = useState<Device[]>([])
  const [devicesError, setDevicesError] = useState<string | null>(null)

  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)

  // Filtre
  const [filterStatus, setFilterStatus] = useState<string>("all")

  // Formulaire (création ou édition)
  const [formData, setFormData] = useState<RuleFormData>(EMPTY_FORM)
  const [editingRule, setEditingRule] = useState<Rule | null>(null)

  const fetchRules = useCallback(async () => {
    try {
      const data = await ruleService.getRules()
      setRules(data)
      setError(null)
    } catch {
      setError("Erreur lors du chargement des règles")
    } finally {
      setIsLoading(false)
    }
  }, [])

  const fetchDevices = useCallback(async () => {
    try {
      const data = await deviceService.getDevices()
      setDevices(data)
      setDevicesError(null)
    } catch {
      setDevicesError("Impossible de charger la liste des appareils")
    }
  }, [])

  useEffect(() => {
    // Admin : redirection vers l’interface avancée
    if (isAdmin) {
      router.replace("/admin/rules")
      return
    }

    const load = async () => {
      await Promise.all([fetchRules(), fetchDevices()])
    }
    void load()
  }, [isAdmin, router, fetchRules, fetchDevices])

  // Application des filtres
  useEffect(() => {
    let result = [...rules]

    if (filterStatus === "enabled") {
      result = result.filter((r) => r.enabled)
    } else if (filterStatus === "disabled") {
      result = result.filter((r) => !r.enabled)
    }

    result.sort((a, b) => b.priority - a.priority)
    setFilteredRules(result)
  }, [rules, filterStatus])

  const openCreateDialog = () => {
    setEditingRule(null)
    setFormData(EMPTY_FORM)
    setSaveError(null)
    setIsDialogOpen(true)
  }

  /** Remplit le formulaire à partir d'une règle existante (pour édition). */
  const ruleToFormData = (rule: Rule): RuleFormData => {
    const cond = rule.condition as any
    const conditions = cond?.conditions && Array.isArray(cond.conditions) ? cond.conditions : cond ? [cond] : []
    let useTime = false
    let startTime = "08:00"
    let endTime = "18:00"
    let presenceMode: "any" | "present" | "absent" = "any"
    let useLight = false
    let lightOperator: "<" | ">" | "=" = "<"
    let lightValue = "100"
    for (const c of conditions) {
      if (c?.type === "time" && c.operator === "between" && Array.isArray(c.value) && c.value.length >= 2) {
        useTime = true
        startTime = String(c.value[0])
        endTime = String(c.value[1])
      } else if (c?.type === "presence") {
        presenceMode = c.value === true ? "present" : "absent"
      } else if (c?.type === "light") {
        useLight = true
        lightOperator = (c.operator === ">" || c.operator === "=" ? c.operator : "<") as "<" | ">" | "="
        lightValue = String(c.value ?? 100)
      }
    }
    const act = rule.action as any
    const deviceId = act?.device_id ?? null
    const actionType = (act?.action === "turn_on" || act?.action === "turn_off" || act?.action === "set_brightness" ? act.action : "set_brightness") as "turn_on" | "turn_off" | "set_brightness"
    const brightness = typeof act?.brightness === "number" ? act.brightness : 50
    return {
      name: rule.name,
      description: rule.description ?? "",
      enabled: rule.enabled,
      priority: rule.priority,
      useTime,
      startTime,
      endTime,
      presenceMode,
      useLight,
      lightOperator,
      lightValue,
      deviceId,
      actionType,
      brightness,
    }
  }

  const openEditDialog = (rule: Rule) => {
    setEditingRule(rule)
    setFormData(ruleToFormData(rule))
    setSaveError(null)
    setIsDialogOpen(true)
  }

  const buildConditionJson = () => {
    const conditions: any[] = []

    if (formData.useTime) {
      conditions.push({
        type: "time",
        operator: "between",
        value: [formData.startTime, formData.endTime],
      })
    }

    if (formData.presenceMode === "present") {
      conditions.push({ type: "presence", value: true })
    } else if (formData.presenceMode === "absent") {
      conditions.push({ type: "presence", value: false })
    }

    if (formData.useLight && formData.lightValue.trim() !== "") {
      conditions.push({
        type: "light",
        operator: formData.lightOperator,
        value: Number.parseInt(formData.lightValue, 10),
      })
    }

    if (conditions.length === 0) {
      throw new Error("Ajoutez au moins une condition (temps, présence ou luminosité).")
    }

    if (conditions.length === 1) {
      return conditions[0]
    }

    return {
      type: "AND",
      conditions,
    }
  }

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaveError(null)

    if (!formData.name.trim()) {
      setSaveError("Le nom de la règle est obligatoire.")
      return
    }

    if (!formData.deviceId) {
      setSaveError("Sélectionnez un appareil à contrôler.")
      return
    }

    if (formData.actionType === "set_brightness" && (formData.brightness < 0 || formData.brightness > 100)) {
      setSaveError("La luminosité doit être comprise entre 0 et 100%.")
      return
    }

    let conditionJson: any
    try {
      conditionJson = buildConditionJson()
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Condition invalide.")
      return
    }

    const actionJson: any = {
      device_id: formData.deviceId,
      action: formData.actionType,
    }
    if (formData.actionType === "set_brightness") {
      actionJson.brightness = formData.brightness
    }

    setIsSaving(true)

    try {
      const payload = {
        name: formData.name,
        description: formData.description || undefined,
        condition: conditionJson,
        action: actionJson,
        enabled: formData.enabled,
        priority: formData.priority,
      }
      if (editingRule) {
        await ruleService.updateRule(editingRule.id, payload)
      } else {
        await ruleService.createRule(payload)
      }

      setIsDialogOpen(false)
      setFormData(EMPTY_FORM)
      setEditingRule(null)
      await fetchRules()
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Erreur lors de la sauvegarde de la règle.")
    } finally {
      setIsSaving(false)
    }
  }

  const handleDelete = async (id: number) => {
    try {
      await ruleService.deleteRule(id)
      await fetchRules()
    } catch (err) {
      console.error("Failed to delete rule:", err)
    }
  }

  if (isAdmin) {
    return (
      <div className="flex justify-center items-center min-h-[400px]">
        <LoadingSpinner size="lg" text="Redirection vers l’interface admin..." />
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <LoadingSpinner size="lg" text="Chargement de vos règles..." />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
        <AlertCircle className="h-12 w-12 text-destructive" />
        <p className="text-muted-foreground">{error}</p>
        <Button onClick={fetchRules}>Réessayer</Button>
      </div>
    )
  }

  const enabledCount = rules.filter((r) => r.enabled).length

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-balance">Règles d&apos;automatisation</h1>
          <p className="text-muted-foreground">
            {enabledCount} règle(s) active(s) sur {rules.length}. Ajoutez et gérez simplement vos règles d&apos;éclairage.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={fetchRules}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Actualiser
          </Button>
          <Button size="sm" onClick={openCreateDialog}>
            <Plus className="h-4 w-4 mr-2" />
            Nouvelle règle
          </Button>
        </div>
      </div>

      {/* Filtres */}
      <div className="flex items-center gap-2">
        <Select value={filterStatus} onValueChange={setFilterStatus}>
          <SelectTrigger className="min-w-[220px] sm:min-w-[260px]">
            <Filter className="h-4 w-4 mr-2" />
            <SelectValue placeholder="Statut" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Toutes les règles</SelectItem>
            <SelectItem value="enabled">Activées</SelectItem>
            <SelectItem value="disabled">Désactivées</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Liste des règles */}
      {filteredRules.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="p-4 rounded-full bg-muted mb-4">
            <Settings2 className="h-8 w-8 text-muted-foreground" />
          </div>
          <h3 className="font-medium mb-1">Aucune règle pour le moment</h3>
          <p className="text-sm text-muted-foreground mb-4">
            Créez votre première règle pour automatiser vos lumières.
          </p>
          <Button onClick={openCreateDialog}>
            <Plus className="h-4 w-4 mr-2" />
            Créer une règle
          </Button>
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 gap-4">
          {filteredRules.map((rule) => (
            <RuleCardUser key={rule.id} rule={rule} onUpdate={fetchRules} onEdit={openEditDialog} onDelete={handleDelete} />
          ))}
        </div>
      )}

      {/* Dialogue création / édition règle */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="w-full max-w-xl sm:max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingRule ? "Modifier la règle" : "Nouvelle règle"}</DialogTitle>
            <DialogDescription>
              {editingRule
                ? "Modifiez les paramètres de votre règle puis enregistrez."
                : "Choisissez dans quels cas vos lumières doivent réagir, puis ce qu'elles doivent faire. Répondez simplement aux questions ci‑dessous."}
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSave}>
            <div className="space-y-4 py-4">
              {saveError && (
                <div className="p-3 rounded-lg bg-destructive/10 text-destructive text-sm">{saveError}</div>
              )}

              <div className="space-y-2">
                <Label htmlFor="name">Nom de la règle</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Lumière automatique du salon"
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Description (optionnel)</Label>
                <Input
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Ex : Allume la lampe entre 8h et 18h quand quelqu’un passe."
                />
              </div>

              {/* Conditions */}
              <div className="space-y-3 border rounded-lg p-4">
                <p className="font-medium text-sm flex items-center gap-2">
                  <Settings2 className="h-4 w-4" />
                  Dans quels cas cette règle s&apos;applique-t-elle ?
                </p>

                {/* Temps */}
                <div className="space-y-2">
                  <Label>Heures pendant lesquelles la règle est active</Label>
                  <div className="flex flex-col sm:flex-row gap-2 items-center">
                    <Select
                      value={formData.useTime ? "enabled" : "disabled"}
                      onValueChange={(value) =>
                        setFormData({ ...formData, useTime: value === "enabled" })
                      }
                    >
                      <SelectTrigger className="w-full sm:w-auto min-w-[230px]">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="enabled">Limiter à une plage horaire</SelectItem>
                        <SelectItem value="disabled">Ignorer l&apos;heure</SelectItem>
                      </SelectContent>
                    </Select>
                    {formData.useTime && (
                      <div className="flex items-center gap-2">
                        <Input
                          type="time"
                          value={formData.startTime}
                          onChange={(e) => setFormData({ ...formData, startTime: e.target.value })}
                          className="w-[120px]"
                        />
                        <span className="text-sm text-muted-foreground">à</span>
                        <Input
                          type="time"
                          value={formData.endTime}
                          onChange={(e) => setFormData({ ...formData, endTime: e.target.value })}
                          className="w-[120px]"
                        />
                      </div>
                    )}
                  </div>
                </div>

                {/* Présence */}
                <div className="space-y-2">
                  <Label>Présence de personnes</Label>
                  <Select
                    value={formData.presenceMode}
                    onValueChange={(value: "any" | "present" | "absent") =>
                      setFormData({ ...formData, presenceMode: value })
                    }
                  >
                    <SelectTrigger className="w-full sm:w-[260px]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="present">Seulement si présence détectée</SelectItem>
                      <SelectItem value="absent">Seulement s&apos;il n&apos;y a personne</SelectItem>
                      <SelectItem value="any">Présence indifférente</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Luminosité */}
                <div className="space-y-2">
                  <Label>Luminosité de la pièce (optionnel)</Label>
                  <div className="flex flex-col sm:flex-row gap-2 items-center">
                    <Select
                      value={formData.useLight ? "enabled" : "disabled"}
                      onValueChange={(value) =>
                        setFormData({ ...formData, useLight: value === "enabled" })
                      }
                    >
                      <SelectTrigger className="w-full sm:w-auto min-w-[250px]">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="enabled">Prendre en compte la luminosité</SelectItem>
                        <SelectItem value="disabled">Ignorer la luminosité</SelectItem>
                      </SelectContent>
                    </Select>
                    {formData.useLight && (
                      <div className="flex items-center gap-2">
                        <Select
                          value={formData.lightOperator}
                          onValueChange={(value: "<" | ">" | "=") =>
                            setFormData({ ...formData, lightOperator: value })
                          }
                        >
                          <SelectTrigger className="w-[140px]">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="<">inférieure à</SelectItem>
                            <SelectItem value=">">supérieure à</SelectItem>
                            <SelectItem value="=">environ égale à</SelectItem>
                          </SelectContent>
                        </Select>
                        <Input
                          type="number"
                          min={0}
                          id="lightValue"
                          value={formData.lightValue}
                          onChange={(e) => setFormData({ ...formData, lightValue: e.target.value })}
                          className="w-[120px]"
                        />
                        <span className="text-sm text-muted-foreground">lux</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Action */}
              <div className="space-y-3 border rounded-lg p-4">
                <p className="font-medium text-sm">Que doit faire la lumière ?</p>

                <div className="space-y-2">
                  <Label>Appareil à contrôler</Label>
                  <Select
                    value={formData.deviceId ? String(formData.deviceId) : ""}
                    onValueChange={(value) =>
                      setFormData({ ...formData, deviceId: Number.parseInt(value, 10) })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder={devicesError ?? "Sélectionnez une lampe ou prise"} />
                    </SelectTrigger>
                    <SelectContent>
                      {devices.map((device) => (
                        <SelectItem key={device.id} value={String(device.id)}>
                          {device.name} {device.location ? `(${device.location})` : ""}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>Action</Label>
                  <Select
                    value={formData.actionType}
                    onValueChange={(value: "turn_on" | "turn_off" | "set_brightness") =>
                      setFormData({ ...formData, actionType: value })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="turn_on">Allumer</SelectItem>
                      <SelectItem value="turn_off">Éteindre</SelectItem>
                      <SelectItem value="set_brightness">Régler la luminosité</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {formData.actionType === "set_brightness" && (
                  <div className="space-y-2">
                    <Label>Luminosité cible (%)</Label>
                    <Input
                      type="number"
                      min={0}
                      max={100}
                      value={formData.brightness}
                      onChange={(e) =>
                        setFormData({ ...formData, brightness: Number.parseInt(e.target.value || "0", 10) })
                      }
                    />
                  </div>
                )}
              </div>

              {/* Options */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Priorité (1-10)</Label>
                  <Input
                    type="number"
                    min={1}
                    max={10}
                    value={formData.priority}
                    onChange={(e) =>
                      setFormData({ ...formData, priority: Number.parseInt(e.target.value || "5", 10) })
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label>Statut</Label>
                  <Select
                    value={formData.enabled ? "enabled" : "disabled"}
                    onValueChange={(value) =>
                      setFormData({ ...formData, enabled: value === "enabled" })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="enabled">Activée immédiatement</SelectItem>
                      <SelectItem value="disabled">Créer en désactivée</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)} disabled={isSaving}>
                Annuler
              </Button>
              <Button type="submit" disabled={isSaving}>
                {isSaving ? "Enregistrement..." : editingRule ? "Mettre à jour" : "Créer la règle"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}
