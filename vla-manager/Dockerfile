FROM node:23-slim AS build

ENV PNPM_HOME=/pnpm
ENV PATH="$PNPM_HOME:$PATH"
RUN corepack enable

WORKDIR /app/
COPY . /app

RUN --mount=type=cache,id=pnpm,target=/pnpm/store pnpm install --frozen-lockfile
RUN pnpm run build


FROM nginx:1.27-alpine-slim
# Pristine build (with base path placeholder); copied into the web root and
# configured at container start-up from the BASE_PATH env var (default: /)
ARG BASE_PATH_ARG=/
RUN echo "BASE_PATH_ARG: ${BASE_PATH_ARG}"

COPY --from=build /app/dist /opt/app/dist
COPY --from=build --chmod=755 /app/misc/base-path.sh /docker-entrypoint.d/40-base-path.sh
ENV BASE_PATH=${BASE_PATH_ARG}
RUN echo "BASE_PATH: ${BASE_PATH}"
COPY --from=build /app/misc/nginx.conf.template /etc/nginx/templates/default.conf.template
# Let the nginx image export NGINX_LOCAL_RESOLVERS from /etc/resolv.conf
ENV NGINX_ENTRYPOINT_LOCAL_RESOLVERS=1
EXPOSE 80
HEALTHCHECK --interval=5s --timeout=2s \
    CMD wget -q -O /dev/null http://127.0.0.1/livez
