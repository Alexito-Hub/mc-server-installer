FROM eclipse-temurin:17-jre-jammy
WORKDIR /opt/minecraft
COPY . /opt/minecraft
EXPOSE 25565
VOLUME ["/opt/minecraft/world", "/opt/minecraft/plugins"]
CMD ["bash", "./bin/start.sh"]
