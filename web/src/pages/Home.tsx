import { Link } from "react-router-dom";

export default function Home() {
  return (
    <div className="grid" style={{ gap: "32px" }}>
      <section className="hero">
        <div>
          <span className="tag">ML‑сервис прогнозов</span>
          <h1>Личный кабинет для быстрых прогнозов</h1>
          <p>
            Управляйте балансом, отправляйте запросы на прогноз и отслеживайте
            результаты в одном месте. Backend обрабатывает задачи через RabbitMQ,
            а интерфейс показывает прогресс и результат.
          </p>
          <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
            <Link className="btn" to="/register">
              Начать работу
            </Link>
            <Link className="btn secondary" to="/login">
              У меня уже есть аккаунт
            </Link>
          </div>
        </div>
        <div className="card">
          <h3 className="section-title">Что доступно</h3>
          <div className="grid three">
            <div>
              <strong>Баланс</strong>
              <p className="helper">Пополнение и контроль кредитов.</p>
            </div>
            <div>
              <strong>Прогноз</strong>
              <p className="helper">Отправка временных рядов для ML‑прогноза.</p>
            </div>
            <div>
              <strong>История</strong>
              <p className="helper">Просмотр транзакций и задач.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="grid two">
        <div className="card">
          <h3 className="section-title">Асинхронная обработка</h3>
          <p className="helper">
            Запросы попадают в очередь RabbitMQ и обрабатываются воркерами.
            Статус можно проверять в любое время.
          </p>
        </div>
        <div className="card">
          <h3 className="section-title">Безопасный доступ</h3>
          <p className="helper">
            JWT‑авторизация защищает кабинет. Выход доступен в один клик.
          </p>
        </div>
      </section>
    </div>
  );
}
