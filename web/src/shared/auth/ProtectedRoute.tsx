import { Navigate } from "react-router-dom";
import { useAuth } from "./AuthContext";

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthed } = useAuth();
  if (!isAuthed) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}
