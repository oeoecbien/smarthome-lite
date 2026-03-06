"use client"

import { useState } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Switch } from "@/components/ui/switch"
import { Badge } from "@/components/ui/badge"
import { ruleService } from "@/lib/services/rule-service"
import type { Rule } from "@/lib/types"
import { formatRelativeTime } from "@/lib/formatters"
import { Button } from "@/components/ui/button"
import { Settings2, Loader2, Edit, Trash2 } from "lucide-react"
import { cn } from "@/lib/utils"

interface RuleCardUserProps {
  rule: Rule
  onUpdate: () => void
  onEdit?: (rule: Rule) => void
  onDelete?: (id: number) => void
}

// Fonction pour formater une règle en langage naturel
function formatRuleDescription(rule: Rule): string {
  if (rule.description) {
    return rule.description
  }

  // Tentative de formatage basique depuis la condition et l'action
  const condition = rule.condition
  const action = rule.action

  let desc = "Si "
  
  // Formatage simplifié de la condition
  if (condition.type === "AND" && condition.conditions) {
    const parts: string[] = []
    condition.conditions.forEach((cond: any) => {
      if (cond.type === "time" && cond.operator === "between") {
        parts.push(`entre ${cond.value[0]} et ${cond.value[1]}`)
      } else if (cond.type === "presence") {
        parts.push(cond.value ? "présence détectée" : "aucune présence")
      } else if (cond.type === "light") {
        parts.push(`luminosité ${cond.operator} ${cond.value}`)
      }
    })
    desc += parts.join(" et ")
  }

  desc += ", alors "

  // Formatage de l'action
  if (action.action === "turn_on") {
    desc += "allumer"
  } else if (action.action === "turn_off") {
    desc += "éteindre"
  } else if (action.action === "set_brightness") {
    desc += `régler à ${action.brightness}%`
  }

  return desc
}

export function RuleCardUser({ rule, onUpdate, onEdit, onDelete }: RuleCardUserProps) {
  const [isUpdating, setIsUpdating] = useState(false)

  const handleToggle = async () => {
    setIsUpdating(true)
    try {
      await ruleService.updateRule(rule.id, { enabled: !rule.enabled })
      onUpdate()
    } catch (error) {
      console.error("Failed to toggle rule:", error)
    } finally {
      setIsUpdating(false)
    }
  }

  const handleDelete = () => {
    if (onDelete && window.confirm(`Êtes-vous sûr de vouloir supprimer la règle « ${rule.name } » ?`)) {
      onDelete(rule.id)
    }
  }

  return (
    <Card
      className={cn(
        "transition-all duration-200",
        rule.enabled ? "ring-1 ring-secondary/30" : "opacity-80",
        isUpdating && "opacity-70",
      )}
    >
      <CardContent className="p-4">
        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-3 min-w-0">
            <div
              className={cn(
                "p-2.5 rounded-xl shrink-0",
                rule.enabled ? "bg-secondary/20 text-secondary" : "bg-muted text-muted-foreground",
              )}
            >
              <Settings2 className="h-5 w-5" />
            </div>
            <div className="min-w-0">
              <h3 className="font-medium truncate">{rule.name}</h3>
              <p className="text-sm text-muted-foreground mt-1">
                {formatRuleDescription(rule)}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            {isUpdating ? (
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            ) : (
              <Switch checked={rule.enabled} onCheckedChange={handleToggle} aria-label={`Toggle ${rule.name}`} />
            )}
          </div>
        </div>

        {/* Meta */}
        <div className="flex items-center gap-2 mt-3 flex-wrap">
          <Badge variant={rule.enabled ? "default" : "secondary"} className="text-xs">
            {rule.enabled ? "Activée" : "Désactivée"}
          </Badge>
          <span className="text-xs text-muted-foreground">Créée {formatRelativeTime(rule.created_at)}</span>
        </div>

        {/* Modifier / Supprimer */}
        <div className="mt-4 pt-3 border-t border-border flex flex-wrap items-center gap-2">
          {onEdit && (
            <Button variant="outline" size="sm" onClick={() => onEdit(rule)} className="w-full sm:w-auto">
              <Edit className="h-4 w-4 mr-2" />
              Modifier
            </Button>
          )}
          {onDelete && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleDelete}
              disabled={isUpdating}
              className="text-muted-foreground hover:bg-destructive hover:text-white"
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Supprimer
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
