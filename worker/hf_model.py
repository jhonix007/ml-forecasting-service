from __future__ import annotations

import os
from typing import Iterable

import numpy as np
import torch
from transformers import TimeSeriesTransformerForPrediction


DEFAULT_MODEL_ID = "huggingface/time-series-transformer-tourism-monthly"


class HFTimeSeriesModel:
    def __init__(self, model_id: str | None = None, device: str | None = None) -> None:
        self.model_id = model_id or os.getenv("HF_MODEL_ID", DEFAULT_MODEL_ID)
        self.device = device or os.getenv("HF_DEVICE") or ("cuda" if torch.cuda.is_available() else "cpu")

        self.model = TimeSeriesTransformerForPrediction.from_pretrained(self.model_id)
        self.model.to(self.device)
        self.model.eval()

        cfg = self.model.config
        self.context_length = getattr(cfg, "context_length", None) or getattr(cfg, "prediction_length", None) or 24
        self.max_lag = max(getattr(cfg, "lags_sequence", []) or [0])
        self.num_time_features = int(getattr(cfg, "num_time_features", 0) or 0)
        self.num_static_categorical = int(getattr(cfg, "num_static_categorical_features", 0) or 0)
        self.num_static_real = int(getattr(cfg, "num_static_real_features", 0) or 0)

    @staticmethod
    def _to_float_list(series: Iterable[float]) -> list[float]:
        return [float(x) for x in series]

    def _prepare_context(self, series: list[float], horizon: int) -> list[float]:
        # Для лаговых признаков нужна история, покрывающая максимальный лаг и горизонт.
        # Длина истории: лаги + контекст.
        min_len = max(
            self.context_length,
            self.max_lag + 1,
            self.context_length + self.max_lag,
        )
        if len(series) >= min_len:
            return series[-min_len:]

        pad_value = series[0] if series else 0.0
        pad_count = min_len - len(series)
        return [pad_value] * pad_count + series

    def predict(self, series: list[float], horizon: int) -> list[float]:
        if horizon <= 0:
            raise ValueError("horizon must be > 0")
        if not series:
            raise ValueError("series must be non-empty")

        series = self._to_float_list(series)
        context = self._prepare_context(series, horizon)

        context_len = len(context)

        past_values = torch.tensor(context, dtype=torch.float32, device=self.device).unsqueeze(0)
        past_observed_mask = torch.ones((1, context_len), dtype=torch.float32, device=self.device)

        kwargs = {
            "past_values": past_values,
            "past_observed_mask": past_observed_mask,
        }

        if self.num_time_features > 0:
            ctx_len = context_len
            past_time_features = torch.zeros(
                (1, ctx_len, self.num_time_features), dtype=torch.float32, device=self.device
            )
            future_time_features = torch.zeros(
                (1, horizon, self.num_time_features), dtype=torch.float32, device=self.device
            )
            kwargs["past_time_features"] = past_time_features
            kwargs["future_time_features"] = future_time_features

        if self.num_static_categorical > 0:
            kwargs["static_categorical_features"] = torch.zeros(
                (1, self.num_static_categorical), dtype=torch.long, device=self.device
            )

        if self.num_static_real > 0:
            kwargs["static_real_features"] = torch.zeros(
                (1, self.num_static_real), dtype=torch.float32, device=self.device
            )

        # Параметры генерации задаём через конфиг для максимальной совместимости
        try:
            self.model.config.prediction_length = horizon
        except Exception:
            pass
        try:
            self.model.config.num_parallel_samples = 100
        except Exception:
            pass

        with torch.no_grad():
            out = self.model.generate(**kwargs)

        samples = getattr(out, "sequences", out)
        samples = samples.detach().cpu().numpy()

        samples = np.asarray(samples)
        samples = samples.reshape(-1, samples.shape[-1])
        mean_forecast = samples.mean(axis=0)
        return mean_forecast.tolist()
