import { useEffect, useState } from "react";

import { Shell, type AppView } from "./components/Shell";
import { useAuth } from "./hooks/useAuth";
import {
  api,
  isAuthExpiredError,
  type AuditLogEntry,
  type ConflictAnalysis,
  type DocumentRecord,
  type EvaluationRun,
  type HealthStatus,
  type QueryResponse,
  type VersionComparison,
} from "./lib/api";
import { AnalysisPage } from "./pages/AnalysisPage";
import { DashboardPage } from "./pages/DashboardPage";
import { EvaluationPage } from "./pages/EvaluationPage";
import { LogsPage } from "./pages/LogsPage";
import { LoginPage } from "./pages/LoginPage";
import { QueryPage } from "./pages/QueryPage";

const DEMO_USERNAME = "admin";
const DEMO_PASSWORD = "admin123";

export default function App() {
  const { auth, isReady, isAuthenticated, login, logout } = useAuth();
  const [activeView, setActiveView] = useState<AppView>("dashboard");
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [evaluationRuns, setEvaluationRuns] = useState<EvaluationRun[]>([]);
  const [queryResult, setQueryResult] = useState<QueryResponse | null>(null);
  const [versionComparison, setVersionComparison] = useState<VersionComparison | null>(null);
  const [conflictAnalysis, setConflictAnalysis] = useState<ConflictAnalysis | null>(null);
  const [globalError, setGlobalError] = useState("");
  const [isBootstrappingDemo, setIsBootstrappingDemo] = useState(false);
  const [bootstrapFailed, setBootstrapFailed] = useState(false);

  const loadAppData = async () => {
    if (!auth?.accessToken) {
      return;
    }

    setGlobalError("");
    try {
      const [healthResponse, documentsResponse, logResponse, evaluationsResponse] = await Promise.all([
        api.health(),
        api.listDocuments(auth.accessToken),
        api.listLogs(auth.accessToken),
        api.listEvaluations(auth.accessToken),
      ]);
      setHealth(healthResponse);
      setDocuments(documentsResponse);
      setLogs(logResponse);
      setEvaluationRuns(evaluationsResponse);
    } catch (caughtError) {
      if (isAuthExpiredError(caughtError)) {
        logout();
        return;
      }
      setGlobalError(caughtError instanceof Error ? caughtError.message : "Failed to load the app.");
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      void loadAppData();
    }
  }, [isAuthenticated, auth?.accessToken]);

  useEffect(() => {
    if (!isAuthenticated || documents.every((document) => document.status !== "processing")) {
      return;
    }

    const intervalId = window.setInterval(() => {
      void loadAppData();
    }, 3000);

    return () => window.clearInterval(intervalId);
  }, [documents, isAuthenticated]);

  useEffect(() => {
    if (!isReady || isAuthenticated || isBootstrappingDemo || bootstrapFailed) {
      return;
    }

    setIsBootstrappingDemo(true);
    setGlobalError("");

    void login(DEMO_USERNAME, DEMO_PASSWORD)
      .catch((caughtError) => {
        setBootstrapFailed(true);
        setGlobalError(
          caughtError instanceof Error
            ? caughtError.message
            : "Unable to enter the demo workspace automatically.",
        );
      })
      .finally(() => {
        setIsBootstrappingDemo(false);
      });
  }, [bootstrapFailed, isAuthenticated, isBootstrappingDemo, isReady, login]);

  if (!isReady) {
    return <div className="loading-shell">Preparing console...</div>;
  }

  if (!isAuthenticated || !auth) {
    if (isBootstrappingDemo) {
      return <div className="loading-shell">Entering demo workspace...</div>;
    }
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

  const handleDelete = async (document: DocumentRecord) => {
    await api.deleteDocument(document.id, auth.accessToken);
    setVersionComparison(null);
    setQueryResult((current) => {
      if (!current) {
        return current;
      }
      const removedDocumentUsed = current.citations.some(
        (citation) => citation.document_id === document.id,
      );
      return removedDocumentUsed ? null : current;
    });
    await loadAppData();
  };

  const handleUpdateVisibility = async (document: DocumentRecord, visibility: "private" | "public") => {
    await api.updateDocumentPermissions(document.id, visibility, auth.accessToken);
    await loadAppData();
  };

  const handleQuery = async (question: string) => {
    const result = await api.query(question, auth.accessToken);
    setQueryResult(result);
    await loadAppData();
  };

  const handleRunEvaluation = async () => {
    await api.runEvaluation(auth.accessToken);
    await loadAppData();
  };

  const handleAnalyzeConflicts = async () => {
    const analysis = await api.analyzeConflicts(auth.accessToken);
    setConflictAnalysis(analysis);
    await loadAppData();
  };

  const handleComparePreviousVersion = async (document: DocumentRecord) => {
    if (!document.previous_version_id) {
      return;
    }
    const comparison = await api.compareDocumentVersions(
      document.previous_version_id,
      document.id,
      auth.accessToken,
    );
    setVersionComparison(comparison);
    await loadAppData();
  };

  return (
    <Shell
      activeView={activeView}
      onChangeView={setActiveView}
    >
      {globalError ? <p className="error-banner">{globalError}</p> : null}

      {activeView === "dashboard" && (
        <DashboardPage
          documents={documents}
          health={health}
          onUpload={handleUpload}
          onReindex={handleReindex}
          onDelete={handleDelete}
          onUpdateVisibility={handleUpdateVisibility}
          onComparePreviousVersion={handleComparePreviousVersion}
          versionComparison={versionComparison}
        />
      )}

      {activeView === "query" && (
        <QueryPage result={queryResult} onSubmitQuestion={handleQuery} />
      )}

      {activeView === "analysis" && (
        <AnalysisPage analysis={conflictAnalysis} onAnalyzeConflicts={handleAnalyzeConflicts} />
      )}

      {activeView === "evaluation" && (
        <EvaluationPage runs={evaluationRuns} onRunEvaluation={handleRunEvaluation} />
      )}

      {activeView === "logs" && <LogsPage logs={logs} />}
    </Shell>
  );
}
