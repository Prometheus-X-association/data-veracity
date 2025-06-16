FROM node:23-slim AS base

ENV PNPM_HOME=/pnpm
ENV PATH="$PNPM_HOME:$PATH"
RUN corepack enable

WORKDIR /app/


FROM base AS prod-deps
COPY package*.json /app/
COPY pnpm-lock.yaml /app/
RUN --mount=type=cache,id=pnpm,target=/pnpm/store pnpm install --prod --frozen-lockfile


FROM base AS build
ARG DVA_DASHBOARD_BACKEND_URL
ENV VITE_BACKEND_BASE_URL=$DVA_DASHBOARD_BACKEND_URL
COPY . /app
RUN --mount=type=cache,id=pnpm,target=/pnpm/store pnpm install --frozen-lockfile
RUN pnpm run build


FROM busybox:stable-musl
RUN adduser -D web
USER web
WORKDIR /home/web/
COPY --from=prod-deps /app/node_modules .
COPY --from=build /app/dist .
EXPOSE 3000
CMD ["httpd", "-f", "-v", "-p", "3000"]
HEALTHCHECK --interval=5s --timeout=2s CMD nc -z localhost 3000
