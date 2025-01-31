echo "Starting server ..."
docker compose down -f prod.docker-compose.yaml
docker compose pull
docker compose up -f prod.docker-compose.yaml -d 
echo "Server started"

