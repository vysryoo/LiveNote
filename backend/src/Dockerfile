FROM amazoncorretto:17-alpine

WORKDIR /app

ARG JAR_FILE=build/libs/*.jar
COPY ${JAR_FILE} /app/app.jar
COPY src/main/resources/env.properties /app/env.properties

ENTRYPOINT ["java", "-jar", "/app/app.jar"]
