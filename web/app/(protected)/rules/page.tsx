"use client"

import type React from "react"

import { useEffect, useState, useCallback } from "react"
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
import { RuleCard } from "@/components/rule-card"
import { ruleService } from "@/lib/services/rule-service"
import type { Rule } from "@/lib/types"
import { Plus, RefreshCw, Settings2, AlertCircle, Filter } from "lucide-react"

interface RuleFormData {
  name: string
  description: string
  condition: string
  action: string
  enabled: boolean
  priority: number
}

const EMPTY_FORM: RuleFormData = {
  name: "",
  description: "",
  condition: JSON.stringify(
    {
      type: "AND",
      conditions: [
        { type: "time", operator: "between", value: ["08:00", "18:00"] },
        { type: "presence", value: true },
      ],
    },
    null,
    2,
  ),
  action: JSON.stringify(
    {
      device_id: 1,
      action: "set_brightness",
      brightness: 50,
    },
    null,
    2,
  ),
  enabled: true,
  priority: 5,
}

export default function RulesPage() {
  const [rules, setRules] = useState<Rule[]>([])
  const [filteredRules, setFilteredRules] = useState<Rule[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [editingRule, setEditingRule] = useState<Rule | null>(null)

  // Filter
  const [filterStatus, setFilterStatus] = useState<string>("all")

  // Form state
  const [formData, setFormData] = useState<RuleFormData>(EMPTY_FORM)

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

  useEffect(() => {
    fetchRules()
  }, [fetchRules])

  // Apply filters
  useEffect(() => {
    let result = [...rules]

    if (filterStatus === "enabled") {
      result = result.filter((r) => r.enabled)
    } else if (filterStatus === "disabled") {
      result = result.filter((r) => !r.enabled)
    }

    // Sort by priority (higher first)
    result.sort((a, b) => b.priority - a.priority)

    setFilteredRules(result)
  }, [rules, filterStatus])

  const validateJson = (json: string): boolean => {
    try {
      JSON.parse(json)
      return true
    } catch {
      return false
    }
  }

  const openCreateDialog = () => {
    setEditingRule(null)
    setFormData(EMPTY_FORM)
    setSaveError(null)
    setIsDialogOpen(true)
  }

  const openEditDialog = (rule: Rule) => {
    setEditingRule(rule)
    setFormData({
      name: rule.name,
      description: rule.description || "",
      condition: JSON.stringify(rule.condition, null, 2),
      action: JSON.stringify(rule.action, null, 2),
      enabled: rule.enabled,
      priority: rule.priority,
    })
    setSaveError(null)
    setIsDialogOpen(true)
  }

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaveError(null)

    // Validate JSON
    if (!validateJson(formData.condition)) {
      setSaveError("La condition JSON n'est pas valide")
      return
    }
    if (!validateJson(formData.action)) {
      setSaveError("L'action JSON n'est pas valide")
      return
    }

    setIsSaving(true)

    try {
      const ruleData = {
        name: formData.name,
        description: formData.description || undefined,
        condition: JSON.parse(formData.condition),
        action: JSON.parse(formData.action),
        enabled: formData.enabled,
        priority: formData.priority,
      }

      if (editingRule) {
        await ruleService.updateRule(editingRule.id, ruleData)
      } else {
        await ruleService.createRule(ruleData)
      }

      setIsDialogOpen(false)
      setFormData(EMPTY_FORM)
      setEditingRule(null)
      fetchRules()
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Erreur lors de la sauvegarde")
    } finally {
      setIsSaving(false)
    }
  }

  const handleDelete = async (id: number) => {
    try {
      await ruleService.deleteRule(id)
      fetchRules()
    } catch (err) {
      console.error("Failed to delete rule:", err)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <LoadingSpinner size="lg" text="Chargement des règles..." />
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
            {enabledCount} règle(s) active(s) sur {rules.length}
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

      {/* Filter */}
      <div className="flex items-center gap-2">
        <Select value={filterStatus} onValueChange={setFilterStatus}>
          <SelectTrigger className="w-[180px]">
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

      {/* Rules Grid */}
      {filteredRules.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="p-4 rounded-full bg-muted mb-4">
            <Settings2 className="h-8 w-8 text-muted-foreground" />
          </div>
          <h3 className="font-medium mb-1">Aucune règle trouvée</h3>
          <p className="text-sm text-muted-foreground mb-4">
            {rules.length === 0
              ? "Créez votre première règle d'automatisation"
              : "Aucune règle ne correspond au filtre"}
          </p>
          {rules.length === 0 && (
            <Button onClick={openCreateDialog}>
              <Plus className="h-4 w-4 mr-2" />
              Créer une règle
            </Button>
          )}
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 gap-4">
          {filteredRules.map((rule) => (
            <RuleCard key={rule.id} rule={rule} onUpdate={fetchRules} onEdit={openEditDialog} onDelete={handleDelete} />
          ))}
        </div>
      )}

      {/* Create/Edit Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingRule ? "Modifier la règle" : "Créer une règle"}</DialogTitle>
            <DialogDescription>
              {editingRule
                ? "Modifiez les paramètres de votre règle d'automatisation."
                : "Configurez une nouvelle règle d'automatisation avec des conditions et actions JSON."}
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
                  placeholder="Lumière automatique jour"
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Description (optionnel)</Label>
                <Input
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Allume la lampe à 50% entre 8h et 18h si présence"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="priority">Priorité (1-10)</Label>
                  <Input
                    id="priority"
                    type="number"
                    min="1"
                    max="10"
                    value={formData.priority}
                    onChange={(e) => setFormData({ ...formData, priority: Number.parseInt(e.target.value) })}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label>Statut</Label>
                  <Select
                    value={formData.enabled ? "enabled" : "disabled"}
                    onValueChange={(value) => setFormData({ ...formData, enabled: value === "enabled" })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="enabled">Activée</SelectItem>
                      <SelectItem value="disabled">Désactivée</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="condition">Condition (JSON)</Label>
                <Textarea
                  id="condition"
                  value={formData.condition}
                  onChange={(e) => setFormData({ ...formData, condition: e.target.value })}
                  rows={8}
                  className="font-mono text-sm"
                  placeholder='{"type": "AND", "conditions": [...]}'
                />
                {formData.condition && !validateJson(formData.condition) && (
                  <p className="text-sm text-destructive">JSON invalide</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="action">Action (JSON)</Label>
                <Textarea
                  id="action"
                  value={formData.action}
                  onChange={(e) => setFormData({ ...formData, action: e.target.value })}
                  rows={6}
                  className="font-mono text-sm"
                  placeholder='{"device_id": 1, "action": "turn_on"}'
                />
                {formData.action && !validateJson(formData.action) && (
                  <p className="text-sm text-destructive">JSON invalide</p>
                )}
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)} disabled={isSaving}>
                Annuler
              </Button>
              <Button type="submit" disabled={isSaving}>
                {isSaving ? "Sauvegarde..." : editingRule ? "Mettre à jour" : "Créer"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}
