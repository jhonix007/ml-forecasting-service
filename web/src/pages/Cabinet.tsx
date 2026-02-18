import { useEffect, useMemo, useState } from "react";
import { api, TaskStatusResponse } from "../shared/api";

export default function Cabinet() {
  const [balance, setBalance] = useState<number | null>(null);
  const [topUpAmount, setTopUpAmount] = useState("100");
  const [predictModel, setPredictModel] = useState("hf-timeseries");
  const [seriesInput, setSeriesInput] = useState("10,12,11,13,15,14");
  const [horizonInput, setHorizonInput] = useState("5");
  const [task, setTask] = useState<TaskStatusResponse | null>(null);
  const [loadingPredict, setLoadingPredict] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const maxHorizon = 50;

  const formatStatus = (value?: string) => {
    switch (value?.toLowerCase()) {
      case "success":
        return "Успех";
      case "failed":
        return "Ошибка";
      case "pending":
        return "В ожидании";
      default:
        return value || "-";
    }
  };

  const parsedSeries = useMemo(() => {
    return seriesInput
      .split(/[,\s]+/)
      .map((value) => value.trim())
      .filter(Boolean)
      .map((value) => Number(value));
  }, [seriesInput]);

  const refreshBalance = async () => {
    try {
      const data = await api.getBalance();
      setBalance(data.balance);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось загрузить баланс");
    }
  };

  useEffect(() => {
    refreshBalance();
  }, []);

  const handleTopUp = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    setNotice(null);
    const amount = Number(topUpAmount);
    if (!Number.isFinite(amount) || amount <= 0) {
      setError("Сумма пополнения должна быть положительной");
      return;
    }
    try {
      const data = await api.topUp(amount);
      setBalance(data.balance);
      setNotice("Баланс обновлён");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось пополнить баланс");
    }
  };

  const handlePredict = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    setNotice(null);
    setTask(null);

    if (parsedSeries.length === 0 || parsedSeries.some((x) => Number.isNaN(x))) {
      setError("Ряд должен содержать только числа, разделённые запятыми или пробелами");
      return;
    }

    const horizon = Number(horizonInput);
    if (!Number.isFinite(horizon) || horizon <= 0) {
      setError("Горизонт должен быть положительным числом");
      return;
    }

    setLoadingPredict(true);
    try {
      const response = await api.predict({
        model: predictModel,
        series: parsedSeries,
        horizon: Math.min(horizon, maxHorizon),
      });
      setNotice(`Задача создана: ${response.task_id}`);
      const status = await api.getPrediction(response.task_id);
      setTask(status);
      await refreshBalance();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось выполнить прогноз");
    } finally {
      setLoadingPredict(false);
    }
  };

  const refreshTask = async () => {
    if (!task?.task_id) return;
    setError(null);
    try {
      const status = await api.getPrediction(task.task_id);
      setTask(status);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось обновить статус");
    }
  };

  return (
    <div className="grid" style={{ gap: "24px" }}>
      <div className="grid two">
        <div className="card">
          <h2 className="section-title">Баланс</h2>
          <p className="helper">Доступно кредитов: {balance ?? "..."}</p>
          <form className="form" onSubmit={handleTopUp}>
            <label className="label">Сумма пополнения</label>
            <input
              className="input"
              type="number"
              min="1"
              value={topUpAmount}
              onChange={(event) => setTopUpAmount(event.target.value)}
            />
            <button className="btn" type="submit">
              Пополнить
            </button>
          </form>
        </div>

        <div className="card">
          <h2 className="section-title">Быстрый статус</h2>
          <p className="helper">Последняя задача:</p>
          {task ? (
            <div>
              <p>
                <strong>Статус:</strong> {formatStatus(task.status)}
              </p>
              <p>
                <strong>ID задачи:</strong> {task.task_id}
              </p>
              {task.error && <p className="error">{task.error}</p>}
              {task.prediction && (
                <p>
                  <strong>Прогноз:</strong> {task.prediction.join(", ")}
                </p>
              )}
              <button className="btn ghost" type="button" onClick={refreshTask}>
                Обновить статус
              </button>
            </div>
          ) : (
            <p className="helper">Пока задач нет.</p>
          )}
        </div>
      </div>

      <div className="card">
        <h2 className="section-title">Новый прогноз</h2>
        <form className="form" onSubmit={handlePredict}>
          <label className="label">Модель</label>
          <input
            className="input"
            value={predictModel}
            onChange={(event) => setPredictModel(event.target.value)}
            placeholder="hf-timeseries"
          />

          <label className="label">Ряд (разделение запятой или пробелом)</label>
          <textarea
            value={seriesInput}
            onChange={(event) => setSeriesInput(event.target.value)}
          />
          <div className="helper">Распознанные значения: {parsedSeries.join(", ") || "-"}</div>

          <label className="label">Горизонт</label>
          <input
            className="input"
            type="number"
            min="1"
            max={maxHorizon}
            value={horizonInput}
            onChange={(event) => setHorizonInput(event.target.value)}
          />
          <div className="helper">Максимальный горизонт: {maxHorizon}. Если больше — будет ограничен.</div>

          {error && <div className="error">{error}</div>}
          {notice && <div className="notice">{notice}</div>}

          <button className="btn" type="submit" disabled={loadingPredict}>
            {loadingPredict ? "Отправляем..." : "Отправить прогноз"}
          </button>
        </form>
      </div>
    </div>
  );
}
