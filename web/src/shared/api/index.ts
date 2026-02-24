import { apiRequest } from "./client";

export interface TokenResponse {
  access_token: string;
}

export interface BalanceResponse {
  balance: number;
}

export interface TaskCreateResponse {
  task_id: string;
}

export interface TaskStatusResponse {
  task_id: string;
  status: string;
  model?: string;
  worker_id?: string | null;
  prediction?: number[] | null;
  error?: string | null;
  created_at?: string | null;
}

export interface TransactionItem {
  tx_type: string;
  amount: number;
  comment: string;
  created_at: string;
}

export interface TaskHistoryItem {
  task_id: string;
  model: string;
  status: string;
  worker_id?: string | null;
  prediction?: number[] | Record<string, unknown> | null;
  error?: string | null;
  created_at?: string | null;
}

export const api = {
  register(email: string, password: string) {
    return apiRequest<TokenResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  },
  login(email: string, password: string) {
    return apiRequest<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  },
  getBalance() {
    return apiRequest<BalanceResponse>("/balance", { method: "GET" });
  },
  topUp(amount: number) {
    return apiRequest<BalanceResponse>("/balance/top-up", {
      method: "POST",
      body: JSON.stringify({ amount }),
    });
  },
  predict(payload: { model: string; series: number[]; horizon: number }) {
    return apiRequest<TaskCreateResponse>("/predict", {
      method: "POST",
      body: JSON.stringify({
        model: payload.model,
        features: {
          series: payload.series,
          horizon: payload.horizon,
        },
      }),
    });
  },
  getPrediction(taskId: string) {
    return apiRequest<TaskStatusResponse>(`/predictions/${taskId}`, { method: "GET" });
  },
  getTransactions() {
    return apiRequest<TransactionItem[]>("/history/transactions", { method: "GET" });
  },
  getPredictionsHistory() {
    return apiRequest<TaskHistoryItem[]>("/history/predictions", { method: "GET" });
  },
};
