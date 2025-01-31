echo "Starting server ..."
docker compose -f prod.docker-compose.yaml down
docker compose pull
docker compose -f prod.docker-compose.yaml up  -d 
echo "Server started"

