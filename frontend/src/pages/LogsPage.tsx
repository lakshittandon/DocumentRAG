import type { AuditLogEntry } from "../lib/api";

interface LogsPageProps {
  logs: AuditLogEntry[];
}

export function LogsPage({ logs }: LogsPageProps) {
  return (
    <div className="stack">
      <section className="hero-card">
        <div>
          <p className="eyebrow">Audit Trail</p>
          <h2>Inspect user actions and system activity</h2>
          <p>
            Use this view during the demo to show login, ingestion, query, reindex, and evaluation events captured by the backend.
          </p>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <h3>Audit Log Entries</h3>
          <span className="panel-tag">{logs.length} events</span>
        </div>

        <div className="log-table">
          <div className="log-row log-head">
            <span>Time</span>
            <span>Actor</span>
            <span>Action</span>
            <span>Detail</span>
          </div>
          {logs.map((entry) => (
            <div key={entry.id} className="log-row">
              <span>{new Date(entry.created_at).toLocaleString()}</span>
              <span>{entry.actor}</span>
              <span>{entry.action}</span>
              <span>{entry.detail}</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

