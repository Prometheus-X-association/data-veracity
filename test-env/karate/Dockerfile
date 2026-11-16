FROM eclipse-temurin:24-jre-alpine-3.22

# Download karate JAR to /app/karate.jar
RUN mkdir /app/
WORKDIR /app/

COPY ./karate-features /app/features
COPY ./test-data /app/test-data
COPY ./karate-configs /app/classpath

RUN apk --no-cache add curl~=8.14 && curl -Lo karate.jar \
  https://github.com/karatelabs/karate/releases/download/v1.5.0/karate-1.5.0.jar
ENTRYPOINT ["java", "-cp", "/app/classpath:/app/karate.jar", "com.intuit.karate.Main"]
