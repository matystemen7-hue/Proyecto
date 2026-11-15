import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth";
import Layout from "./components/Layout";
import Login from "./pages/Login";
import CambiarClave from "./pages/CambiarClave";
import Beneficiarios from "./pages/Beneficiarios";
import Entregas from "./pages/Entregas";
import Dashboard from "./pages/Dashboard";
import Usuarios from "./pages/Usuarios";
import Auditoria from "./pages/Auditoria";

function Protegida({ permiso, children }) {
  const { user, can } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  if (user.must_change_password) return <Navigate to="/cambiar-clave" replace />;
  if (permiso && !can(permiso)) return <Navigate to="/" replace />;
  return children;
}

function Inicio() {
  const { can } = useAuth();
  return <Navigate to={can("dashboard") ? "/dashboard" : "/entregas"} replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/cambiar-clave" element={<CambiarClave />} />
      <Route element={<Layout />}>
        <Route path="/" element={<Protegida><Inicio /></Protegida>} />
        <Route path="/beneficiarios" element={<Protegida permiso="beneficiarios"><Beneficiarios /></Protegida>} />
        <Route path="/entregas" element={<Protegida permiso="entregas"><Entregas /></Protegida>} />
        <Route path="/dashboard" element={<Protegida permiso="dashboard"><Dashboard /></Protegida>} />
        <Route path="/usuarios" element={<Protegida permiso="usuarios"><Usuarios /></Protegida>} />
        <Route path="/auditoria" element={<Protegida permiso="auditoria"><Auditoria /></Protegida>} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
