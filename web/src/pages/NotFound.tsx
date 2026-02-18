import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div className="card" style={{ textAlign: "center" }}>
      <h2 className="section-title">Страница не найдена</h2>
      <p className="helper">Такой страницы не существует.</p>
      <Link className="btn" to="/">
        На главную
      </Link>
    </div>
  );
}
