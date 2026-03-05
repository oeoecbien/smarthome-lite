"use client"

import { useEffect, useState, useCallback } from "react"
import { useRouter } from "next/navigation"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { LoadingSpinner } from "@/components/loading-spinner"
import { api } from "@/lib/api"
import { useIsAdmin } from "@/hooks/use-is-admin"
import {
  Activity,
  RefreshCw,
  AlertTriangle,
  Clock,
  BarChart3,
  FileText,
  ArrowLeft,
} from "lucide-react"
import Link from "next/link"

interface ApiMetrics {
  total_requests: number
  total_errors: number
  error_rate: number
  avg_response_time: number
  endpoints: Record<string, { count: number; errors: number; avg_time: number }>
  timestamp: string
}

interface LogsResponse {
  lines: string[]
  count: number
  message?: string
}

export default function AdminMonitoringPage() {
  const isAdmin = useIsAdmin()
  const router = useRouter()
  const [metrics, setMetrics] = useState<ApiMetrics | null>(null)
  const [logs, setLogs] = useState<LogsResponse | null>(null)
  const [isLoadingMetrics, setIsLoadingMetrics] = useState(true)
  const [isLoadingLogs, setIsLoadingLogs] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [logLevel, setLogLevel] = useState<string>("all")
  const [tail, setTail] = useState<number>(300)
  const [autoRefresh, setAutoRefresh] = useState(true)

  const fetchMetrics = useCallback(async () => {
    try {
      const data = await api.get<ApiMetrics>("/api/admin/metrics")
      setMetrics(data)
    } catch {
      setError("Impossible de charger les métriques")
    } finally {
      setIsLoadingMetrics(false)
    }
  }, [])

  const fetchLogs = useCallback(async () => {
    try {
      const data = await api.get<LogsResponse>("/api/admin/logs", {
        tail,
        ...(logLevel !== "all" ? { level: logLevel } : {}),
      })
      setLogs(data)
    } catch {
      setError("Impossible de charger les logs")
    } finally {
      setIsLoadingLogs(false)
    }
  }, [tail, logLevel])

  useEffect(() => {
    if (!isAdmin) {
      router.push("/dashboard")
    }
  }, [isAdmin, router])

  useEffect(() => {
    if (!isAdmin) return
    fetchMetrics()
  }, [isAdmin, fetchMetrics])

  useEffect(() => {
    if (!isAdmin) return
    fetchLogs()
  }, [isAdmin, fetchLogs])

  useEffect(() => {
    if (!isAdmin || !autoRefresh) return
    const t = setInterval(() => {
      fetchMetrics()
      fetchLogs()
    }, 10000)
    return () => clearInterval(t)
  }, [isAdmin, autoRefresh, fetchMetrics, fetchLogs])

  if (!isAdmin) {
    return null
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/admin">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div>
          <h1 className="text-2xl font-semibold flex items-center gap-2">
            <Activity className="h-6 w-6 text-orange-500" />
            Monitoring
          </h1>
          <p className="text-muted-foreground text-sm">
            Logs et métriques de l&apos;API (réservé aux administrateurs)
          </p>
        </div>
      </div>

      {error && (
        <Card className="border-destructive/50 bg-destructive/5">
          <CardContent className="pt-4 flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-destructive" />
            <span>{error}</span>
          </CardContent>
        </Card>
      )}

      {/* Métriques */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <div>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-primary" />
              Métriques API
            </CardTitle>
            <CardDescription>
              Requêtes, erreurs et temps de réponse (dernières requêtes)
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={() => { setIsLoadingMetrics(true); fetchMetrics(); }}>
              <RefreshCw className="h-4 w-4 mr-1" />
              Actualiser
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {isLoadingMetrics ? (
            <div className="flex justify-center py-8">
              <LoadingSpinner />
            </div>
          ) : metrics ? (
            <div className="space-y-4">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div className="rounded-lg border bg-muted/50 p-3">
                  <p className="text-xs text-muted-foreground">Requêtes totales</p>
                  <p className="text-xl font-semibold">{metrics.total_requests}</p>
                </div>
                <div className="rounded-lg border bg-muted/50 p-3">
                  <p className="text-xs text-muted-foreground">Erreurs</p>
                  <p className="text-xl font-semibold text-destructive">{metrics.total_errors}</p>
                </div>
                <div className="rounded-lg border bg-muted/50 p-3">
                  <p className="text-xs text-muted-foreground">Taux d&apos;erreur</p>
                  <p className="text-xl font-semibold">{metrics.error_rate} %</p>
                </div>
                <div className="rounded-lg border bg-muted/50 p-3">
                  <p className="text-xs text-muted-foreground flex items-center gap-1">
                    <Clock className="h-3 w-3" /> Temps moyen
                  </p>
                  <p className="text-xl font-semibold">{metrics.avg_response_time} s</p>
                </div>
              </div>
              {metrics.timestamp && (
                <p className="text-xs text-muted-foreground">
                  Dernière mise à jour : {new Date(metrics.timestamp).toLocaleString("fr-FR")}
                </p>
              )}
              {Object.keys(metrics.endpoints || {}).length > 0 && (
                <div>
                  <p className="text-sm font-medium mb-2">Top endpoints</p>
                  <div className="rounded-md border overflow-hidden">
                    <table className="w-full text-sm">
                      <thead className="bg-muted/50">
                        <tr>
                          <th className="text-left p-2">Endpoint</th>
                          <th className="text-right p-2">Requêtes</th>
                          <th className="text-right p-2">Erreurs</th>
                          <th className="text-right p-2">Temps moy. (s)</th>
                        </tr>
                      </thead>
                      <tbody>
                        {Object.entries(metrics.endpoints).map(([ep, st]) => (
                          <tr key={ep} className="border-t">
                            <td className="p-2 font-mono text-xs">{ep}</td>
                            <td className="p-2 text-right">{st.count}</td>
                            <td className="p-2 text-right text-destructive">{st.errors}</td>
                            <td className="p-2 text-right">{st.avg_time.toFixed(3)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <p className="text-muted-foreground">Aucune métrique disponible</p>
          )}
        </CardContent>
      </Card>

      {/* Logs */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <div>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-primary" />
              Fichier de logs
            </CardTitle>
            <CardDescription>
              Dernières lignes du fichier de log (configurer LOG_FILE dans .env pour activer)
            </CardDescription>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <div className="flex items-center gap-2">
              <Label htmlFor="tail" className="text-xs whitespace-nowrap">Lignes</Label>
              <Select
                value={String(tail)}
                onValueChange={(v) => setTail(Number(v))}
              >
                <SelectTrigger id="tail" className="w-[100px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="100">100</SelectItem>
                  <SelectItem value="300">300</SelectItem>
                  <SelectItem value="500">500</SelectItem>
                  <SelectItem value="1000">1000</SelectItem>
                  <SelectItem value="2000">2000</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center gap-2">
              <Label htmlFor="level" className="text-xs whitespace-nowrap">Niveau</Label>
              <Select value={logLevel} onValueChange={setLogLevel}>
                <SelectTrigger id="level" className="w-[110px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tous</SelectItem>
                  <SelectItem value="DEBUG">DEBUG</SelectItem>
                  <SelectItem value="INFO">INFO</SelectItem>
                  <SelectItem value="WARNING">WARNING</SelectItem>
                  <SelectItem value="ERROR">ERROR</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center gap-2">
              <Switch id="auto" checked={autoRefresh} onCheckedChange={setAutoRefresh} />
              <Label htmlFor="auto" className="text-xs">Rafraîchir 10s</Label>
            </div>
            <Button variant="outline" size="sm" onClick={() => { setIsLoadingLogs(true); fetchLogs(); }}>
              <RefreshCw className="h-4 w-4 mr-1" />
              Actualiser
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {isLoadingLogs ? (
            <div className="flex justify-center py-8">
              <LoadingSpinner />
            </div>
          ) : logs ? (
            <div className="space-y-2">
              {logs.message && (
                <p className="text-sm text-muted-foreground">{logs.message}</p>
              )}
              <pre className="rounded-md border bg-muted/30 p-3 text-xs font-mono overflow-x-auto max-h-[500px] overflow-y-auto whitespace-pre-wrap break-all">
                {logs.lines.length === 0
                  ? "Aucune ligne (fichier vide ou non configuré)"
                  : logs.lines.join("\n")}
              </pre>
              {logs.lines.length > 0 && (
                <p className="text-xs text-muted-foreground">
                  {logs.count} ligne{logs.count > 1 ? "s" : ""} affichée{logs.count > 1 ? "s" : ""}
                </p>
              )}
            </div>
          ) : (
            <p className="text-muted-foreground">Impossible de charger les logs</p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
