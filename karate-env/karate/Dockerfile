FROM eclipse-temurin:23-jre-alpine

# Download karate JAR to /app/karate.jar
RUN mkdir /app/
WORKDIR /app/
RUN apk add curl
RUN curl \
  -Lo karate.jar \
  https://github.com/karatelabs/karate/releases/download/v1.5.0/karate-1.5.0.jar
ENTRYPOINT ["java", "-jar", "karate.jar"]
