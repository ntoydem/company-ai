# The production bundle lives inside the Caddy image (ADR-001 — no separate frontend
# runtime container). The source comes from the named build context `src`
# (docker-compose.yml `additional_contexts`, chosen by FRONTEND_DIR): AI-BalBal
# (frontend-balbal/frontend, default) or the retired company-ai frontend/ (rollback).
# Explicit file list rather than `COPY . .`: a named context ignores .dockerignore, so a
# stray node_modules/ or dist/ in the source tree must never reach the image.
# The Caddyfile stays a bind-mounted config, editable without a rebuild.
FROM node:20-alpine AS build
WORKDIR /app
COPY --from=src package.json package-lock.json ./
RUN npm ci
COPY --from=src index.html vite.config.ts tsconfig.json tsconfig.node.json ./
COPY --from=src src ./src
RUN npm run build

FROM caddy:2-alpine
COPY --from=build /app/dist /srv
