docker volume create --name gradle-cache
docker run --rm -v gradle-cache:/home/gradle/.gradle -v "$PWD":/home/gradle/project -w /home/gradle/project gradle:8.1.1-jdk17 sh -c "gradle clean && gradle build -x test"
ls -ltrh ./build/libs
docker build -t demo-0.0.1 .
docker run -dp 8080:8080 -e DOCKER_HOST_IP="$(sh demo-ip.sh)" -e POSTGRES_USERNAME=demo -e POSTGRES_PASSWORD=demo --name cloud-app demo-0.0.1