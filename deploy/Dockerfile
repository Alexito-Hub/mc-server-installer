FROM eclipse-temurin:17-jre-jammy
WORKDIR /opt/auralix/minecraft
COPY . /opt/auralix/minecraft
EXPOSE 25565
VOLUME ["/opt/auralix/minecraft/world", "/opt/auralix/minecraft/plugins"]
CMD ["bash", "./bin/start.sh"]
