echo "Starting server ..."
docker compose down -f prod.docker-compose.yml
docker compose pull
docker compose up -d -f prod.docker-compose.yml
echo "Server started"

