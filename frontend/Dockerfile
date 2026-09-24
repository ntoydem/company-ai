# Tooling image only (`make lint`, `make dev-frontend`): node_modules baked in, source
# bind-mounted at runtime by the compose `frontend` service. The production bundle is
# built by infra/caddy/Dockerfile and served by Caddy — no Node container runs in `make up`.
FROM node:20-alpine
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
CMD ["npm", "run", "dev", "--", "--host"]
