"use client"

import { useMemo } from "react"
import { Line, LineChart, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from "recharts"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import type { LightReading } from "@/lib/types"

interface LightChartProps {
  data: LightReading[]
}

export function LightChart({ data }: LightChartProps) {
  const chartData = useMemo(() => {
    // Take last 50 readings and reverse to show oldest first
    return [...data]
      .slice(0, 50)
      .reverse()
      .map((reading, index) => ({
        index,
        lux: reading.lux,
        percentage: reading.percentage,
        time: new Date(reading.timestamp).toLocaleTimeString("fr-FR", {
          hour: "2-digit",
          minute: "2-digit",
        }),
      }))
  }, [data])

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Évolution de la luminosité</CardTitle>
        <CardDescription>50 dernières mesures (lux et pourcentage)</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
              <XAxis dataKey="time" tick={{ fontSize: 10 }} className="text-muted-foreground" interval="preserveEnd" />
              <YAxis yAxisId="left" tick={{ fontSize: 12 }} className="text-muted-foreground" />
              <YAxis
                yAxisId="right"
                orientation="right"
                tick={{ fontSize: 12 }}
                className="text-muted-foreground"
                domain={[0, 100]}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "hsl(var(--popover))",
                  borderColor: "hsl(var(--border))",
                  borderRadius: "8px",
                }}
                labelStyle={{ color: "hsl(var(--foreground))" }}
              />
              <Legend />
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="lux"
                stroke="hsl(var(--primary))"
                strokeWidth={2}
                dot={false}
                name="Lux"
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="percentage"
                stroke="hsl(var(--secondary))"
                strokeWidth={2}
                dot={false}
                name="Pourcentage"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}
