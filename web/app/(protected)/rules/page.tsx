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
import { RuleCard } from "@/components/rule-card"
import { RuleCardUser } from "@/components/rule-card-user"
import { AdminOnly } from "@/components/admin-only"
import { ruleService } from "@/lib/services/rule-service"
import { useIsAdmin } from "@/hooks/use-is-admin"
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
  const isAdmin = useIsAdmin()
  const router = useRouter()
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

  useEffect(() => {
    if (isAdmin) {
      router.replace("/admin/rules")
    } else {
      router.replace("/dashboard")
    }
  }, [isAdmin, router])

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

  if (isAdmin) {
    return (
      <div className="flex justify-center items-center min-h-[400px]">
        <LoadingSpinner size="lg" text="Redirection..." />
      </div>
    )
  }

  return (
    <div className="flex justify-center items-center min-h-[400px]">
      <LoadingSpinner size="lg" text="Redirection..." />
    </div>
  )
}
