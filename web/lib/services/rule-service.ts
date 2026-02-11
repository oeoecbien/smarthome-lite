import { api } from "@/lib/api"
import type { Rule, RuleTestResult } from "@/lib/types"

export const ruleService = {
  async getRules(enabled?: boolean): Promise<Rule[]> {
    return api.get<Rule[]>("/api/rules", { enabled: enabled !== undefined ? String(enabled) : undefined })
  },

  async getRule(id: number): Promise<Rule> {
    return api.get<Rule>(`/api/rules/${id}`)
  },

  async createRule(data: Omit<Rule, "id" | "created_at">): Promise<Rule> {
    return api.post<Rule>("/api/rules", data)
  },

  async updateRule(id: number, data: Partial<Rule>): Promise<Rule> {
    return api.put<Rule>(`/api/rules/${id}`, data)
  },

  async deleteRule(id: number): Promise<void> {
    return api.delete(`/api/rules/${id}`)
  },

  async testRule(id: number): Promise<RuleTestResult> {
    const res = await api.post<{
      condition_met?: boolean
      action_executed?: boolean
      message?: string
      error?: string
    }>(`/api/rules/${id}/test`)
    const matched = res.condition_met === true && res.action_executed === true
    const reason =
      res.message ??
      res.error ??
      (matched ? "Condition satisfaite et action exécutée" : "Condition non satisfaite")
    return {
      matched,
      reason,
      condition_met: res.condition_met,
      action_executed: res.action_executed,
      message: res.message,
      error: res.error,
    }
  },
}
