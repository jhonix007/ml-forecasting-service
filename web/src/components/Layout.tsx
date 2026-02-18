import { Link, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../shared/auth/AuthContext";

export default function Layout() {
  const { isAuthed, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <>
      <nav className="nav">
        <Link to="/" className="brand">
          Forecast Desk
        </Link>
        <div className="nav-links">
          <Link to="/">Главная</Link>
          {isAuthed && <Link to="/cabinet">Кабинет</Link>}
          {isAuthed && <Link to="/history">История</Link>}
          {!isAuthed && <Link to="/login">Вход</Link>}
          {!isAuthed && <Link to="/register">Регистрация</Link>}
          {isAuthed && (
            <button className="btn ghost" onClick={handleLogout} type="button">
              Выйти
            </button>
          )}
        </div>
      </nav>
      <div className="container">
        <Outlet />
      </div>
    </>
  );
}
