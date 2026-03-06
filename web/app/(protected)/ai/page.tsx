"use client"

import { useEffect, useState, useCallback } from "react"
import { useRouter } from "next/navigation"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { LoadingSpinner } from "@/components/loading-spinner"
import { ScenarioChip } from "@/components/scenario-chip"
import { AdminOnly } from "@/components/admin-only"
import { aiService } from "@/lib/services/ai-service"
import type { CurrentScenario, ModelMetrics } from "@/lib/types"
import { Brain, RefreshCw, AlertCircle, Cpu, CheckCircle, XCircle } from "lucide-react"
import { useIsAdmin } from "@/hooks/use-is-admin"

export default function AIPage() {
  const isAdmin = useIsAdmin()
  const router = useRouter()
  // Current scenario
  const [scenario, setScenario] = useState<CurrentScenario | null>(null)
  const [isLoadingScenario, setIsLoadingScenario] = useState(true)

  // Model metrics
  const [metrics, setMetrics] = useState<ModelMetrics | null>(null)
  const [isLoadingMetrics, setIsLoadingMetrics] = useState(true)

  const [error, setError] = useState<string | null>(null)

  const fetchScenario = useCallback(async () => {
    try {
      const data = await aiService.getCurrentScenario()
      setScenario(data)
    } catch {
      console.error("Failed to fetch scenario")
    } finally {
      setIsLoadingScenario(false)
    }
  }, [])

  const fetchMetrics = useCallback(async () => {
    try {
      const data = await aiService.getModelMetrics()
      setMetrics(data)
    } catch {
      console.error("Failed to fetch metrics")
    } finally {
      setIsLoadingMetrics(false)
    }
  }, [])

  useEffect(() => {
    fetchScenario()
    fetchMetrics()
  }, [fetchScenario, fetchMetrics])

  useEffect(() => {
    if (isAdmin) {
      router.replace("/admin/ai")
    }
  }, [isAdmin, router])

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
          <h1 className="text-2xl font-semibold text-balance">Intelligence Artificielle</h1>
          <p className="text-muted-foreground">Classification de scénarios et prédiction d&apos;intensité</p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            fetchScenario()
            fetchMetrics()
          }}
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          Actualiser
        </Button>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-4 rounded-lg bg-destructive/10 text-destructive">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Current Scenario - Visible to all */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Brain className="h-5 w-5 text-primary" />
            Scénario actuel
          </CardTitle>
          <CardDescription>Scénario détecté par le système IA</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoadingScenario ? (
            <LoadingSpinner size="sm" />
          ) : scenario ? (
            <div className="space-y-4">
              <ScenarioChip scenario={scenario.scenario} confidence={scenario.confidence} className="text-base" />
              {scenario.confidence !== undefined && (
                <p className="text-xs text-muted-foreground">
                  Ce pourcentage indique à quel point le système est sûr du scénario (heure, présence, état des lampes). Il peut varier légèrement selon la situation.
                </p>
              )}
              <p className="text-sm text-muted-foreground">
                {scenario.scenario === 0 && "Mode Jour - Lumière naturelle suffisante"}
                {scenario.scenario === 1 && "Mode Nuit - Éclairage minimal nécessaire"}
                {scenario.scenario === 2 && "Mode Absence - Économie d'énergie prioritaire"}
                {scenario.scenario === 3 && "Mode Soirée - Ambiance lumineuse"}
              </p>
              <AdminOnly>
                {scenario.context && (
                  <div className="mt-4">
                    <p className="text-sm font-medium text-muted-foreground mb-2">Contexte utilisé (heure, présence, lampe):</p>
                    <pre className="text-xs bg-muted p-3 rounded-lg overflow-x-auto">
                      {JSON.stringify(scenario.context, null, 2)}
                    </pre>
                  </div>
                )}
              </AdminOnly>
            </div>
          ) : (
            <p className="text-muted-foreground">Scénario non disponible</p>
          )}
        </CardContent>
      </Card>

      {/* Model Status - Admin Only */}
      <AdminOnly>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Cpu className="h-5 w-5 text-primary" />
              État du modèle
            </CardTitle>
            <CardDescription>Métriques et informations du modèle IA</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoadingMetrics ? (
              <LoadingSpinner size="sm" />
            ) : metrics ? (
              <div className="space-y-4">
                <div className="flex items-center gap-2">
                  {metrics.model_loaded ? (
                    <CheckCircle className="h-5 w-5 text-secondary" />
                  ) : (
                    <XCircle className="h-5 w-5 text-destructive" />
                  )}
                  <span className="font-medium">{metrics.model_loaded ? "Modèle chargé" : "Modèle non chargé"}</span>
                </div>

                <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
                  <span className="text-sm text-muted-foreground">Précision</span>
                  <span className="font-medium">
                    {typeof metrics.accuracy === "number" && metrics.accuracy >= 0
                      ? `${(metrics.accuracy * 100).toFixed(1)}%`
                      : "Non disponible"}
                  </span>
                </div>

                {metrics.scenarios && Array.isArray(metrics.scenarios) && (
                  <div>
                    <p className="text-sm text-muted-foreground mb-2">Scénarios détectables:</p>
                    <div className="flex flex-wrap gap-2">
                      {metrics.scenarios.map((s) => (
                        <span key={s} className="px-2 py-1 bg-primary/10 text-primary rounded-full text-xs">
                          {s}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {metrics.features && Array.isArray(metrics.features) && (
                  <div>
                    <p className="text-sm text-muted-foreground mb-2">Features utilisées:</p>
                    <div className="flex flex-wrap gap-1">
                      {metrics.features.map((f) => (
                        <span key={f} className="px-2 py-0.5 bg-muted text-muted-foreground rounded text-xs">
                          {f}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-muted-foreground">Métriques non disponibles</p>
            )}
          </CardContent>
        </Card>
      </AdminOnly>
    </div>
  )
}
