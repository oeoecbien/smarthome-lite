import { api } from "@/lib/api"
import type {
  CurrentScenario,
  ClassifyRequest,
  ClassifyResponse,
  PredictIntensityRequest,
  PredictIntensityResponse,
  ModelMetrics,
} from "@/lib/types"

export const aiService = {
  async getCurrentScenario(raspberryPiId?: number): Promise<CurrentScenario> {
    return api.get<CurrentScenario>("/api/ai/current-scenario", { raspberry_pi_id: raspberryPiId })
  },

  async classify(data: ClassifyRequest): Promise<ClassifyResponse> {
    return api.post<ClassifyResponse>("/api/ai/classify", data)
  },

  async predictIntensity(data: PredictIntensityRequest): Promise<PredictIntensityResponse> {
    return api.post<PredictIntensityResponse>("/api/ai/predict-intensity", data)
  },

  async getModelMetrics(): Promise<ModelMetrics> {
    return api.get<ModelMetrics>("/api/ai/model-metrics")
  },
}
