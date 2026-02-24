import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../shared/api";
import { useAuth } from "../shared/auth/AuthContext";

export default function Register() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const data = await api.register(email, password);
      login(data.access_token);
      navigate("/cabinet");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось зарегистрироваться");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card" style={{ maxWidth: "460px", margin: "0 auto" }}>
      <h2 className="section-title">Регистрация</h2>
      <form className="form" onSubmit={handleSubmit}>
        <label className="label">Электронная почта</label>
        <input
          className="input"
          type="email"
          required
          value={email}
          onChange={(event) => setEmail(event.target.value)}
        />
        <label className="label">Пароль</label>
        <input
          className="input"
          type="password"
          required
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />
        {error && <div className="error">{error}</div>}
        <button className="btn" type="submit" disabled={loading}>
          {loading ? "Создаём..." : "Создать аккаунт"}
        </button>
      </form>
      <p className="helper" style={{ marginTop: "12px" }}>
        Уже есть аккаунт? <Link to="/login">Войти</Link>
      </p>
    </div>
  );
}
