# Deployment Notes

- `docker-compose.yml` starts the frontend, backend, PostgreSQL, and Qdrant services.
- The current backend uses in-memory repositories for application state and persists uploaded files in `data/uploads/`.
- PostgreSQL and Qdrant are included to match the target architecture and can be integrated behind the existing abstractions as the project grows.
- Set environment variables through `.env` copied from `.env.example`.
- `render.yaml` deploys the project as a single public web service on Render.
- The Render deployment builds the React frontend into the backend image and serves the UI from the same FastAPI app.
- Uploaded files are ephemeral on free hosting unless persistent storage is added later.
