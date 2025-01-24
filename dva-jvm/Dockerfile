FROM gradle:jdk21-alpine AS cache
RUN mkdir -p /home/gradle/cache_home/
ARG GRADLE_USER_HOME=/home/gradle/cache_home
COPY ./dva-jvm /home/gradle/app
WORKDIR /home/gradle/app/
RUN gradle clean assemble --info --stacktrace --no-daemon

FROM gradle:jdk21-alpine AS build
COPY --from=cache /home/gradle/cache_home /home/gradle/.gradle
COPY --chown=gradle:gradle ./dva-jvm /home/gradle/src
WORKDIR /home/gradle/src/
RUN gradle shadowJar --no-daemon

FROM eclipse-temurin:21-jre-alpine AS runtime
EXPOSE 8080
RUN mkdir /app/
COPY --from=build /home/gradle/src/*/build/libs/*.jar /app/
COPY --chmod=755 ./dva-jvm/docker/docker-entrypoint /app/
COPY ./docs/spec/openapi.yaml /app/
ENV DVA_OPENAPI_FILE=/app/openapi.yaml
ENTRYPOINT ["/app/docker-entrypoint"]