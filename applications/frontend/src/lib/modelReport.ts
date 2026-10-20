import { parseISO } from "date-fns"
import { ApiError, apiFetch } from "./api"
import type { ModelReport } from "@/types"

interface ModelReportResponse {
  version: string
  model_type: string
  trained_at: string
  train_period: string
  test_period: string
  n_hours: number
  performance_ratio: number
  gain_over_baseline_pct: number
  models: {
    name: string
    is_champion: boolean
    is_baseline: boolean
    train_rmse_wh: number
    cv_train_rmse_wh: number
    cv_rmse_wh: number
    cv_rmse_std_wh: number
    test_rmse_wh: number
    test_r2: number
    test_daily_mape_pct: number
  }[]
  champion_folds: { fold: number; train_rmse_wh: number; validation_rmse_wh: number }[]
  residuals_by_hour: { hour: number; baseline_wh: number; champion_wh: number }[]
}

export const modelLabels: Record<string, string> = {
  baseline: "Baseline físico",
  knn: "KNN",
  decision_tree: "Árvore de decisão",
  random_forest: "Random Forest",
  adaboost: "AdaBoost",
  mlp: "Rede neural (MLP)",
}

export function modelLabel(name: string): string {
  return modelLabels[name] ?? name
}

function parsePeriod(period: string): [Date, Date] {
  const [start, end] = period.split("..")
  return [parseISO(start), parseISO(end)]
}

export async function getModelReport(systemId: string): Promise<ModelReport | null> {
  try {
    const r = await apiFetch<ModelReportResponse>(`/systems/${systemId}/model`)
    return {
      version: r.version,
      modelType: r.model_type,
      trainedAt: new Date(r.trained_at),
      trainPeriod: parsePeriod(r.train_period),
      testPeriod: parsePeriod(r.test_period),
      nHours: r.n_hours,
      performanceRatio: r.performance_ratio,
      gainOverBaselinePct: r.gain_over_baseline_pct,
      models: r.models.map((m) => ({
        name: m.name,
        isChampion: m.is_champion,
        isBaseline: m.is_baseline,
        trainRmseWh: m.train_rmse_wh,
        cvTrainRmseWh: m.cv_train_rmse_wh,
        cvRmseWh: m.cv_rmse_wh,
        cvRmseStdWh: m.cv_rmse_std_wh,
        testRmseWh: m.test_rmse_wh,
        testR2: m.test_r2,
        testDailyMapePct: m.test_daily_mape_pct,
      })),
      championFolds: r.champion_folds.map((f) => ({
        fold: f.fold,
        trainRmseWh: f.train_rmse_wh,
        validationRmseWh: f.validation_rmse_wh,
      })),
      residualsByHour: r.residuals_by_hour.map((h) => ({
        hour: h.hour,
        baselineWh: h.baseline_wh,
        championWh: h.champion_wh,
      })),
    }
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null
    throw error
  }
}
