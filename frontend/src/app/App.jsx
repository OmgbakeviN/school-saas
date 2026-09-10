import { useEffect, useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import api from "../services/api";
import LandingPage from "../modules/onboarding/LandingPage";
import CreateSchoolPage from "../modules/onboarding/CreateSchoolPage";
import TenantPortal from "../modules/tenant/TenantPortal";

export default function App() {
  const [context, setContext] = useState(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let mounted = true;

    api.get("/public/context/")
      .then(({ data }) => {
        if (mounted) setContext(data);
      })
      .catch(() => {
        if (mounted) setContext({ school: null });
      })
      .finally(() => {
        if (mounted) setReady(true);
      });

    return () => {
      mounted = false;
    };
  }, []);

  if (!ready) {
    return (
      <div className="grid min-h-screen place-items-center bg-slate-50 text-sm text-slate-500">
        Chargement…
      </div>
    );
  }

  if (context?.school) {
    return <TenantPortal tenantSlug={context.school.slug} />;
  }

  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/create-school" element={<CreateSchoolPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
