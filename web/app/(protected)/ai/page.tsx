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
import { aiService } from "@/lib/services/ai-service"
import type {
  CurrentScenario,
  ClassifyRequest,
  ClassifyResponse,
  PredictIntensityResponse,
  ModelMetrics,
  ScenarioType,
} from "@/lib/types"
import { SCENARIO_LABELS } from "@/lib/types"
import { Brain, RefreshCw, AlertCircle, Cpu, SunDim, CheckCircle, XCircle, Gauge } from "lucide-react"
import { cn } from "@/lib/utils"

const ROOM_TYPES = ["salon", "chambre", "cuisine", "bureau", "salle_de_bain", "couloir", "exterieur"]

const DAYS_OF_WEEK = [
  { value: 0, label: "Lundi" },
  { value: 1, label: "Mardi" },
  { value: 2, label: "Mercredi" },
  { value: 3, label: "Jeudi" },
  { value: 4, label: "Vendredi" },
  { value: 5, label: "Samedi" },
  { value: 6, label: "Dimanche" },
]

export default function AIPage() {
  // Current scenario
  const [scenario, setScenario] = useState<CurrentScenario | null>(null)
  const [isLoadingScenario, setIsLoadingScenario] = useState(true)

  // Model metrics
  const [metrics, setMetrics] = useState<ModelMetrics | null>(null)
  const [isLoadingMetrics, setIsLoadingMetrics] = useState(true)

  // Classification
  const [classifyForm, setClassifyForm] = useState<ClassifyRequest>({
    hour: new Date().getHours(),
    day_of_week: new Date().getDay() === 0 ? 6 : new Date().getDay() - 1, // Convert JS day to Mon=0
    presence_detected: true,
    light_on: false,
    ambient_light_level: 500,
    temperature: 22,
  })
  const [isClassifying, setIsClassifying] = useState(false)
  const [classifyResult, setClassifyResult] = useState<ClassifyResponse | null>(null)

  // Prediction
  const [predictForm, setPredictForm] = useState({
    ambient_light_lux: 300,
    hour: new Date().getHours(),
    day_of_week: new Date().getDay() === 0 ? 6 : new Date().getDay() - 1,
    user_preference_avg: 70,
    room_type: "salon",
    scenario: 0 as ScenarioType,
  })
  const [isPredicting, setIsPredicting] = useState(false)
  const [predictResult, setPredictResult] = useState<PredictIntensityResponse | null>(null)

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

                {metrics.accuracy !== undefined && (
                  <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
                    <span className="text-sm text-muted-foreground">Précision</span>
                    <span className="font-medium">{(metrics.accuracy * 100).toFixed(1)}%</span>
                  </div>
                )}

                {metrics.scenarios && (
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

                {metrics.features && (
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

              <div className="space-y-2">
                <Label htmlFor="c-ambient">Luminosité ambiante (lux)</Label>
                <Input
                  id="c-ambient"
                  type="number"
                  min="0"
                  value={classifyForm.ambient_light_level}
                  onChange={(e) =>
                    setClassifyForm({ ...classifyForm, ambient_light_level: Number.parseInt(e.target.value) })
                  }
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="c-temp">Température (°C)</Label>
                <Input
                  id="c-temp"
                  type="number"
                  value={classifyForm.temperature}
                  onChange={(e) => setClassifyForm({ ...classifyForm, temperature: Number.parseInt(e.target.value) })}
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
                <Label htmlFor="p-ambient">Luminosité ambiante (lux)</Label>
                <Input
                  id="p-ambient"
                  type="number"
                  min="0"
                  value={predictForm.ambient_light_lux}
                  onChange={(e) =>
                    setPredictForm({ ...predictForm, ambient_light_lux: Number.parseInt(e.target.value) })
                  }
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="p-pref">Préférence moyenne utilisateur (%)</Label>
                <Input
                  id="p-pref"
                  type="number"
                  min="0"
                  max="100"
                  value={predictForm.user_preference_avg}
                  onChange={(e) =>
                    setPredictForm({ ...predictForm, user_preference_avg: Number.parseInt(e.target.value) })
                  }
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="p-room">Type de pièce</Label>
                <Select
                  value={predictForm.room_type}
                  onValueChange={(v) => setPredictForm({ ...predictForm, room_type: v })}
                >
                  <SelectTrigger id="p-room">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {ROOM_TYPES.map((room) => (
                      <SelectItem key={room} value={room}>
                        {room.charAt(0).toUpperCase() + room.slice(1).replace("_", " ")}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
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
                      <span className="text-2xl font-bold">{Math.round(predictResult.predicted_brightness)}%</span>
                    </div>
                    <div
                      className="flex-1 h-4 bg-muted-foreground/20 rounded-full overflow-hidden"
                      role="progressbar"
                      aria-valuenow={predictResult.predicted_brightness}
                      aria-valuemin={0}
                      aria-valuemax={100}
                    >
                      <div
                        className={cn(
                          "h-full rounded-full transition-all",
                          predictResult.predicted_brightness > 70
                            ? "bg-warning"
                            : predictResult.predicted_brightness > 40
                              ? "bg-secondary"
                              : "bg-info",
                        )}
                        style={{ width: `${predictResult.predicted_brightness}%` }}
                      />
                    </div>
                  </div>
                  {predictResult.confidence !== undefined && (
                    <p className="text-sm text-muted-foreground mt-2">
                      Confiance: {(predictResult.confidence * 100).toFixed(1)}%
                    </p>
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
