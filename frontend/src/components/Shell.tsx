import type { PropsWithChildren } from "react";

export type AppView = "dashboard" | "query" | "logs";

interface ShellProps extends PropsWithChildren {
  activeView: AppView;
  onChangeView: (view: AppView) => void;
  username?: string;
  onLogout?: () => void;
}

const VIEWS: Array<{ id: AppView; label: string }> = [
  { id: "dashboard", label: "Corpus" },
  { id: "query", label: "Query Studio" },
  { id: "logs", label: "Audit Trail" },
];

export function Shell({ activeView, onChangeView, onLogout, username, children }: ShellProps) {
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
          {VIEWS.map((view) => (
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
