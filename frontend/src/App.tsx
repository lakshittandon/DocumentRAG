import { useEffect, useState } from "react";

import { Shell, type AppView } from "./components/Shell";
import { useAuth } from "./hooks/useAuth";
import {
  api,
  type AuditLogEntry,
  type DocumentRecord,
  type EvaluationRun,
  type HealthStatus,
  type QueryResponse,
} from "./lib/api";
import { DashboardPage } from "./pages/DashboardPage";
import { EvaluationsPage } from "./pages/EvaluationsPage";
import { LogsPage } from "./pages/LogsPage";
import { LoginPage } from "./pages/LoginPage";
import { QueryPage } from "./pages/QueryPage";

export default function App() {
  const { auth, isReady, isAuthenticated, login, logout } = useAuth();
  const [activeView, setActiveView] = useState<AppView>("dashboard");
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [evaluations, setEvaluations] = useState<EvaluationRun[]>([]);
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [queryResult, setQueryResult] = useState<QueryResponse | null>(null);
  const [globalError, setGlobalError] = useState("");

  const loadAppData = async () => {
    if (!auth?.accessToken) {
      return;
    }

    setGlobalError("");
    try {
      const [healthResponse, documentsResponse, evaluationResponse, logResponse] = await Promise.all([
        api.health(),
        api.listDocuments(auth.accessToken),
        api.listEvaluations(auth.accessToken),
        api.listLogs(auth.accessToken),
      ]);
      setHealth(healthResponse);
      setDocuments(documentsResponse);
      setEvaluations(evaluationResponse);
      setLogs(logResponse);
    } catch (caughtError) {
      setGlobalError(caughtError instanceof Error ? caughtError.message : "Failed to load the app.");
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      void loadAppData();
    }
  }, [isAuthenticated, auth?.accessToken]);

  if (!isReady) {
    return <div className="loading-shell">Preparing console...</div>;
  }

  if (!isAuthenticated || !auth) {
    return <LoginPage onLogin={login} />;
  }

  const handleUpload = async (file: File) => {
    await api.uploadDocument(file, auth.accessToken);
    await loadAppData();
  };

  const handleReindex = async (documentId: string) => {
    await api.reindexDocument(documentId, auth.accessToken);
    await loadAppData();
  };

  const handleQuery = async (question: string) => {
    const result = await api.query(question, auth.accessToken);
    setQueryResult(result);
    await loadAppData();
  };

  const handleRunEvaluation = async () => {
    const run = await api.runEvaluation(auth.accessToken);
    setEvaluations((current) => [run, ...current.filter((item) => item.id !== run.id)]);
    await loadAppData();
  };

  return (
    <Shell
      activeView={activeView}
      onChangeView={setActiveView}
      onLogout={logout}
      username={auth.username}
    >
      {globalError ? <p className="error-banner">{globalError}</p> : null}

      {activeView === "dashboard" && (
        <DashboardPage
          documents={documents}
          health={health}
          onUpload={handleUpload}
          onReindex={handleReindex}
        />
      )}

      {activeView === "query" && (
        <QueryPage result={queryResult} onSubmitQuestion={handleQuery} />
      )}

      {activeView === "evaluations" && (
        <EvaluationsPage runs={evaluations} onRunEvaluation={handleRunEvaluation} />
      )}

      {activeView === "logs" && <LogsPage logs={logs} />}
    </Shell>
  );
}

