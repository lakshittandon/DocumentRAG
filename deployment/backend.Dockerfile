FROM node:20-alpine AS frontend-build

WORKDIR /app/frontend

ARG VITE_API_BASE_URL=
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

COPY frontend/package.json /app/frontend/package.json
COPY frontend/tsconfig.json /app/frontend/tsconfig.json
COPY frontend/tsconfig.node.json /app/frontend/tsconfig.node.json
COPY frontend/vite.config.ts /app/frontend/vite.config.ts
COPY frontend/index.html /app/frontend/index.html
COPY frontend/src /app/frontend/src

RUN npm install
RUN npm run build

FROM python:3.11-slim

WORKDIR /app

COPY backend/pyproject.toml /app/backend/pyproject.toml
COPY backend/README.md /app/backend/README.md
COPY backend/app /app/backend/app
COPY data /app/data
COPY --from=frontend-build /app/frontend/dist /app/frontend/dist

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir /app/backend

WORKDIR /app/backend

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
