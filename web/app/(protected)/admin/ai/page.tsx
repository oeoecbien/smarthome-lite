"use client"

import type React from "react"
import { useEffect, useState, useCallback } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { LoadingSpinner } from "@/components/loading-spinner"
import { ScenarioChip } from "@/components/scenario-chip"
import { AdminOnly } from "@/components/admin-only"
import { useIsAdmin } from "@/hooks/use-is-admin"
import { useRouter } from "next/navigation"
import { aiService } from "@/lib/services/ai-service"
import type {
  CurrentScenario,
  ClassifyRequest,
  ClassifyResponse,
  PredictIntensityRequest,
  PredictIntensityResponse,
  ModelMetrics,
  ScenarioType,
} from "@/lib/types"
import { SCENARIO_LABELS } from "@/lib/types"
import { Brain, RefreshCw, AlertCircle, Cpu, SunDim, CheckCircle, XCircle, Gauge } from "lucide-react"
import { cn } from "@/lib/utils"

const DAYS_OF_WEEK = [
  { value: 0, label: "Lundi" },
  { value: 1, label: "Mardi" },
  { value: 2, label: "Mercredi" },
  { value: 3, label: "Jeudi" },
  { value: 4, label: "Vendredi" },
  { value: 5, label: "Samedi" },
  { value: 6, label: "Dimanche" },
]

export default function AdminAIPage() {
  const isAdmin = useIsAdmin()
  const router = useRouter()
  // Current scenario
  const [scenario, setScenario] = useState<CurrentScenario | null>(null)
  const [isLoadingScenario, setIsLoadingScenario] = useState(true)

  // Model metrics
  const [metrics, setMetrics] = useState<ModelMetrics | null>(null)
  const [isLoadingMetrics, setIsLoadingMetrics] = useState(true)

  // Classification (API: hour, day_of_week, presence_detected, light_on)
  const [classifyForm, setClassifyForm] = useState<ClassifyRequest>({
    hour: new Date().getHours(),
    day_of_week: new Date().getDay() === 0 ? 6 : new Date().getDay() - 1,
    presence_detected: true,
    light_on: false,
  })
  const [isClassifying, setIsClassifying] = useState(false)
  const [classifyResult, setClassifyResult] = useState<ClassifyResponse | null>(null)

  // Prédiction d'intensité (API: hour, day_of_week, lux_value, presence_detected, scenario)
  const [predictForm, setPredictForm] = useState<PredictIntensityRequest>({
    hour: new Date().getHours(),
    day_of_week: new Date().getDay() === 0 ? 6 : new Date().getDay() - 1,
    lux_value: 300,
    presence_detected: true,
    scenario: 0 as ScenarioType,
  })
  const [isPredicting, setIsPredicting] = useState(false)
  const [predictResult, setPredictResult] = useState<PredictIntensityResponse | null>(null)

  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!isAdmin) {
      router.push("/dashboard")
    }
  }, [isAdmin, router])

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
    if (isAdmin) {
      fetchScenario()
      fetchMetrics()
    }
  }, [isAdmin, fetchScenario, fetchMetrics])

  const handleClassify = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsClassifying(true)
    setClassifyResult(null)
    setError(null)

    try {
      const result = await aiService.classify(classifyForm)
      setClassifyResult(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur lors de la classification")
    } finally {
      setIsClassifying(false)
    }
  }

  const handlePredict = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsPredicting(true)
    setPredictResult(null)
    setError(null)

    try {
      const result = await aiService.predictIntensity(predictForm)
      setPredictResult(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur lors de la prédiction")
    } finally {
      setIsPredicting(false)
    }
  }

  if (!isAdmin) {
    return null
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-balance">Configuration IA (Admin)</h1>
          <p className="text-muted-foreground">Métriques détaillées, classification et prédiction manuelle</p>
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

      {/* Current Scenario & Model Status */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Current Scenario */}
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
                {scenario.features && (
                  <div className="mt-4">
                    <p className="text-sm font-medium text-muted-foreground mb-2">Features utilisées:</p>
                    <pre className="text-xs bg-muted p-3 rounded-lg overflow-x-auto">
                      {JSON.stringify(scenario.features, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-muted-foreground">Scénario non disponible</p>
            )}
          </CardContent>
        </Card>

        {/* Model Status */}
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
      </div>

      {/* Classification & Prediction Forms */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Classification Form */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Brain className="h-5 w-5 text-primary" />
              Classification manuelle
            </CardTitle>
            <CardDescription>Testez la classification avec des données personnalisées</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleClassify} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="c-hour">Heure (0-23)</Label>
                  <Input
                    id="c-hour"
                    type="number"
                    min="0"
                    max="23"
                    value={classifyForm.hour}
                    onChange={(e) => setClassifyForm({ ...classifyForm, hour: Number.parseInt(e.target.value) })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="c-day">Jour de la semaine</Label>
                  <Select
                    value={String(classifyForm.day_of_week)}
                    onValueChange={(v) => setClassifyForm({ ...classifyForm, day_of_week: Number.parseInt(v) })}
                  >
                    <SelectTrigger id="c-day">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {DAYS_OF_WEEK.map((day) => (
                        <SelectItem key={day.value} value={String(day.value)}>
                          {day.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <Label htmlFor="c-presence">Présence détectée</Label>
                <Switch
                  id="c-presence"
                  checked={classifyForm.presence_detected}
                  onCheckedChange={(v) => setClassifyForm({ ...classifyForm, presence_detected: v })}
                />
              </div>

              <div className="flex items-center justify-between">
                <Label htmlFor="c-light">Lumière allumée</Label>
                <Switch
                  id="c-light"
                  checked={classifyForm.light_on}
                  onCheckedChange={(v) => setClassifyForm({ ...classifyForm, light_on: v })}
                />
              </div>

              <Button type="submit" className="w-full" disabled={isClassifying}>
                {isClassifying ? "Classification..." : "Classifier"}
              </Button>

              {classifyResult && (
                <div className="p-4 bg-muted rounded-lg">
                  <p className="text-sm text-muted-foreground mb-2">Résultat:</p>
                  <div className="flex items-center justify-between">
                    <ScenarioChip scenario={classifyResult.scenario} />
                    <span className="text-sm font-medium">
                      Confiance: {(classifyResult.confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>
              )}
            </form>
          </CardContent>
        </Card>

        {/* Prediction Form */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <SunDim className="h-5 w-5 text-primary" />
              Prédiction d&apos;intensité
            </CardTitle>
            <CardDescription>Prédisez l&apos;intensité lumineuse optimale</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handlePredict} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="p-hour">Heure (0-23)</Label>
                  <Input
                    id="p-hour"
                    type="number"
                    min="0"
                    max="23"
                    value={predictForm.hour}
                    onChange={(e) => setPredictForm({ ...predictForm, hour: Number.parseInt(e.target.value) })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="p-day">Jour de la semaine</Label>
                  <Select
                    value={String(predictForm.day_of_week)}
                    onValueChange={(v) => setPredictForm({ ...predictForm, day_of_week: Number.parseInt(v) })}
                  >
                    <SelectTrigger id="p-day">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {DAYS_OF_WEEK.map((day) => (
                        <SelectItem key={day.value} value={String(day.value)}>
                          {day.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="p-lux">Luminosité ambiante (lux)</Label>
                <Input
                  id="p-lux"
                  type="number"
                  min="0"
                  value={predictForm.lux_value}
                  onChange={(e) =>
                    setPredictForm({ ...predictForm, lux_value: Number(e.target.value) || 0 })
                  }
                />
              </div>

              <div className="flex items-center justify-between">
                <Label htmlFor="p-presence">Présence détectée</Label>
                <Switch
                  id="p-presence"
                  checked={predictForm.presence_detected}
                  onCheckedChange={(v) => setPredictForm({ ...predictForm, presence_detected: v })}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="p-scenario">Scénario</Label>
                <Select
                  value={String(predictForm.scenario)}
                  onValueChange={(v) =>
                    setPredictForm({ ...predictForm, scenario: Number.parseInt(v) as ScenarioType })
                  }
                >
                  <SelectTrigger id="p-scenario">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(SCENARIO_LABELS).map(([value, label]) => (
                      <SelectItem key={value} value={value}>
                        {label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <Button type="submit" className="w-full" disabled={isPredicting}>
                {isPredicting ? "Prédiction..." : "Prédire l'intensité"}
              </Button>

              {predictResult && (
                <div className="p-4 bg-muted rounded-lg">
                  <p className="text-sm text-muted-foreground mb-3">Résultat:</p>
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                      <Gauge className="h-5 w-5 text-primary" />
                      <span className="text-2xl font-bold">{predictResult.intensity}%</span>
                    </div>
                    <div
                      className="flex-1 h-4 bg-muted-foreground/20 rounded-full overflow-hidden"
                      role="progressbar"
                      aria-valuenow={predictResult.intensity}
                      aria-valuemin={0}
                      aria-valuemax={100}
                    >
                      <div
                        className={cn(
                          "h-full rounded-full transition-all",
                          predictResult.intensity > 70
                            ? "bg-warning"
                            : predictResult.intensity > 40
                              ? "bg-secondary"
                              : "bg-info",
                        )}
                        style={{ width: `${predictResult.intensity}%` }}
                      />
                    </div>
                  </div>
                  {predictResult.confidence !== undefined && (
                    <p className="text-sm text-muted-foreground mt-2">
                      Confiance: {(predictResult.confidence * 100).toFixed(1)}%
                    </p>
                  )}
                  {predictResult.method && (
                    <p className="text-xs text-muted-foreground mt-1">Méthode: {predictResult.method}</p>
                  )}
                </div>
              )}
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
