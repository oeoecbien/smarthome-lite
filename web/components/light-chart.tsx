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
    return [...data]
      .slice(0, 50)
      .reverse()
      .map((reading, index) => {
        const lux = reading.lux_value
        return {
          index,
          lux,
          time: new Date(reading.measured_at).toLocaleTimeString("fr-FR", {
            hour: "2-digit",
            minute: "2-digit",
          }),
        }
      })
  }, [data])

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Évolution de la luminosité</CardTitle>
        <CardDescription>50 dernières mesures (en lux)</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
              <XAxis dataKey="time" tick={{ fontSize: 10 }} className="text-muted-foreground" interval="preserveEnd" />
              <YAxis tick={{ fontSize: 12 }} className="text-muted-foreground" />
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
                type="monotone"
                dataKey="lux"
                stroke="hsl(var(--primary))"
                strokeWidth={2}
                dot={false}
                name="Lux"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}
