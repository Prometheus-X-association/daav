docker run --rm --network host -v "$PWD:/usr/src" \
  -e SONAR_HOST_URL=http://localhost:9000 -e SONAR_TOKEN=sqp_9b61362ff1ef927e67c1c7f60be7b750e10ffdc9 \
  sonarsource/sonar-scanner-cli \
  -Dsonar.projectKey=daav \
  -Dsonar.python.version=3.13 \
  -Dsonar.sources=. \
  -Dsonar.tests=. \
  -Dsonar.test.inclusions='backendApi/tests/**,**/*.spec.ts,frontendApp/src/test.ts' \
  -Dsonar.exclusions='**/node_modules/**,**/.angular/**,**/www/**,**/dist/**,docs/**,backendApi/tests/**,**/*.spec.ts,frontendApp/src/test.ts'