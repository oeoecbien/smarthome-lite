"use client"

import { useState } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Switch } from "@/components/ui/switch"
import { Badge } from "@/components/ui/badge"
import { ruleService } from "@/lib/services/rule-service"
import type { Rule, RuleTestResult } from "@/lib/types"
import { formatRelativeTime } from "@/lib/formatters"
import { Settings2, Trash2, Play, Edit, Loader2, CheckCircle, XCircle, ChevronDown, ChevronUp } from "lucide-react"
import { cn } from "@/lib/utils"

interface RuleCardProps {
  rule: Rule
  onUpdate: () => void
  onEdit: (rule: Rule) => void
  onDelete: (id: number) => void
}

export function RuleCard({ rule, onUpdate, onEdit, onDelete }: RuleCardProps) {
  const [isUpdating, setIsUpdating] = useState(false)
  const [isTesting, setIsTesting] = useState(false)
  const [testResult, setTestResult] = useState<RuleTestResult | null>(null)
  const [isExpanded, setIsExpanded] = useState(false)

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

  const handleTest = async () => {
    setIsTesting(true)
    setTestResult(null)
    try {
      const result = await ruleService.testRule(rule.id)
      setTestResult(result)
    } catch (error) {
      console.error("Failed to test rule:", error)
      setTestResult({ matched: false, reason: "Erreur lors du test" })
    } finally {
      setIsTesting(false)
    }
  }

  const handleDelete = () => {
    if (window.confirm(`Êtes-vous sûr de vouloir supprimer la règle "${rule.name}" ?`)) {
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
              {rule.description && (
                <p className="text-sm text-muted-foreground mt-0.5 line-clamp-2">{rule.description}</p>
              )}
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
          <Badge variant="outline" className="text-xs">
            Priorité: {rule.priority}
          </Badge>
          <span className="text-xs text-muted-foreground">Créée {formatRelativeTime(rule.created_at)}</span>
        </div>

        {/* Test Result */}
        {testResult && (
          <div
            className={cn(
              "mt-3 p-3 rounded-lg text-sm flex items-center gap-2",
              testResult.matched ? "bg-secondary/10 text-secondary" : "bg-destructive/10 text-destructive",
            )}
          >
            {testResult.matched ? (
              <CheckCircle className="h-4 w-4 shrink-0" />
            ) : (
              <XCircle className="h-4 w-4 shrink-0" />
            )}
            <span>{testResult.matched ? "Condition satisfaite" : testResult.reason || "Condition non satisfaite"}</span>
          </div>
        )}

        {/* Expandable JSON Preview */}
        <button
          type="button"
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full mt-3 pt-3 border-t border-border flex items-center justify-between text-sm text-muted-foreground hover:bg-muted hover:text-white transition-colors rounded-md px-2 py-1"
        >
          <span>Voir la configuration JSON</span>
          {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </button>

        {isExpanded && (
          <div className="mt-3 space-y-2">
            <div>
              <p className="text-xs font-medium text-muted-foreground mb-1">Condition:</p>
              <pre className="text-xs bg-muted p-2 rounded-lg overflow-x-auto">
                {JSON.stringify(rule.condition, null, 2)}
              </pre>
            </div>
            <div>
              <p className="text-xs font-medium text-muted-foreground mb-1">Action:</p>
              <pre className="text-xs bg-muted p-2 rounded-lg overflow-x-auto">
                {JSON.stringify(rule.action, null, 2)}
              </pre>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center gap-2 mt-4 pt-3 border-t border-border">
          <Button
            variant="outline"
            size="sm"
            onClick={handleTest}
            disabled={isTesting}
            className="flex-1 bg-transparent"
          >
            {isTesting ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Play className="h-4 w-4 mr-2" />}
            Tester
          </Button>
          <Button variant="outline" size="sm" onClick={() => onEdit(rule)} className="flex-1">
            <Edit className="h-4 w-4 mr-2" />
            Modifier
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={handleDelete}
            disabled={isUpdating}
            className="text-muted-foreground hover:bg-destructive hover:text-white"
          >
            <Trash2 className="h-4 w-4" />
            <span className="sr-only">Supprimer</span>
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
