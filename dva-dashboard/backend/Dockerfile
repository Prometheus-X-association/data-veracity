FROM node:23-slim AS base

ENV PNPM_HOME=/pnpm
ENV PATH="$PNPM_HOME:$PATH"
RUN corepack enable

WORKDIR /app/


FROM base AS prod-deps
COPY package*.json .
COPY pnpm-lock.yaml .
RUN --mount=type=cache,id=pnpm,target=/pnpm/store pnpm install --prod --frozen-lockfile


FROM base
COPY --from=prod-deps /app/node_modules /app/node_modules
COPY . .
EXPOSE 3000
CMD ["pnpm", "run", "start"]
HEALTHCHECK --interval=5s --timeout=5s CMD node -e 'require("http").get("http://localhost:3000")'
