"use client"

import { useMemo } from "react"
import { Bar, BarChart, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import type { PresenceRecord } from "@/lib/types"

interface PresenceChartProps {
  data: PresenceRecord[]
}

export function PresenceChart({ data }: PresenceChartProps) {
  const chartData = useMemo(() => {
    // Group by hour (0-23)
    const hourCounts: Record<number, number> = {}
    for (let i = 0; i < 24; i++) {
      hourCounts[i] = 0
    }

    data.forEach((record) => {
      const hour = new Date(record.detected_at).getHours()
      hourCounts[hour]++
    })

    return Object.entries(hourCounts).map(([hour, count]) => ({
      hour: `${hour}h`,
      detections: count,
    }))
  }, [data])

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Détections par heure</CardTitle>
        <CardDescription>Répartition des détections Bluetooth sur 24h</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
              <XAxis dataKey="hour" tick={{ fontSize: 12 }} className="text-muted-foreground" interval={1} />
              <YAxis tick={{ fontSize: 12 }} className="text-muted-foreground" allowDecimals={false} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "hsl(var(--popover))",
                  borderColor: "hsl(var(--border))",
                  borderRadius: "8px",
                }}
                labelStyle={{ color: "hsl(var(--foreground))" }}
              />
              <Bar dataKey="detections" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}
