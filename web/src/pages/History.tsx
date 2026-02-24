import { useEffect, useState } from "react";
import { api, TaskHistoryItem, TransactionItem } from "../shared/api";
import { formatDate, formatPrediction } from "../shared/utils/format";

export default function History() {
  const [transactions, setTransactions] = useState<TransactionItem[]>([]);
  const [tasks, setTasks] = useState<TaskHistoryItem[]>([]);
  const [error, setError] = useState<string | null>(null);

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

  useEffect(() => {
    const load = async () => {
      setError(null);
      try {
        const [txs, preds] = await Promise.all([
          api.getTransactions(),
          api.getPredictionsHistory(),
        ]);
        setTransactions(txs);
        setTasks(preds);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Не удалось загрузить историю");
      }
    };
    load();
  }, []);

  return (
    <div className="grid" style={{ gap: "24px" }}>
      <div className="card">
        <h2 className="section-title">Транзакции</h2>
        {error && <div className="error">{error}</div>}
        <table className="table">
          <thead>
            <tr>
              <th>Дата</th>
              <th>Тип</th>
              <th>Сумма</th>
              <th>Комментарий</th>
            </tr>
          </thead>
          <tbody>
            {transactions.map((tx, index) => (
              <tr key={`${tx.created_at}-${index}`}>
                <td>{formatDate(tx.created_at)}</td>
                <td>{tx.tx_type}</td>
                <td>{tx.amount}</td>
                <td>{tx.comment}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card">
        <h2 className="section-title">Задачи прогнозирования</h2>
        <table className="table">
          <thead>
            <tr>
              <th>Дата</th>
              <th>Модель</th>
              <th>Статус</th>
              <th>Воркер</th>
              <th>Результат</th>
            </tr>
          </thead>
          <tbody>
            {tasks.map((task) => (
              <tr key={task.task_id}>
                <td>{formatDate(task.created_at)}</td>
                <td>{task.model}</td>
                <td>
                  <span
                    className={`badge ${task.status?.toLowerCase() === "success" ? "success" : task.status?.toLowerCase() === "failed" ? "failed" : "pending"}`}
                  >
                    {formatStatus(task.status)}
                  </span>
                </td>
                <td>{task.worker_id || "-"}</td>
                <td>{formatPrediction(task.prediction)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
