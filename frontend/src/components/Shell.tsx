import type { PropsWithChildren } from "react";

export type AppView = "dashboard" | "query" | "analysis" | "evaluation" | "logs";

interface ShellProps extends PropsWithChildren {
  activeView: AppView;
  onChangeView: (view: AppView) => void;
  username?: string;
  role?: string;
  onLogout?: () => void;
}

const VIEWS: Array<{ id: AppView; label: string; adminOnly?: boolean }> = [
  { id: "dashboard", label: "Corpus" },
  { id: "query", label: "Query Studio" },
  { id: "analysis", label: "Analysis Lab" },
  { id: "evaluation", label: "Evaluation Lab", adminOnly: true },
  { id: "logs", label: "Audit Trail" },
];

export function Shell({ activeView, onChangeView, onLogout, username, role, children }: ShellProps) {
  const visibleViews = VIEWS.filter((view) => !view.adminOnly || role === "admin");

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-panel">
          <h1>Reliable RAG Platform</h1>
          <p className="brand-copy">
            Hybrid retrieval, grounded answers, and verification in one demo system.
          </p>
        </div>

        <nav className="nav-list">
          {visibleViews.map((view) => (
            <button
              key={view.id}
              className={view.id === activeView ? "nav-button active" : "nav-button"}
              onClick={() => onChangeView(view.id)}
              type="button"
            >
              {view.label}
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          {username ? <p className="user-chip">{username}</p> : null}
          {onLogout ? (
            <button type="button" className="secondary-button" onClick={onLogout}>
              Logout
            </button>
          ) : null}
        </div>
      </aside>

      <main className="content-panel">{children}</main>
    </div>
  );
}
