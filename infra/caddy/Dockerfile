# Phase 3.3: the production bundle lives inside the Caddy image (ADR-001 — no separate
# frontend runtime container). Build context is ./frontend (see docker-compose.yml).
# The Caddyfile stays a bind-mounted config, editable without a rebuild.
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM caddy:2-alpine
COPY --from=build /app/dist /srv
