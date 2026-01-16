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
    return api.post<RuleTestResult>(`/api/rules/${id}/test`)
  },
}
