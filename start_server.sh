echo "Starting server ..."
docker compose down -f prod.docker-compose.yml
docker compose pull
docker compose up -f prod.docker-compose.yml -d 
echo "Server started"

