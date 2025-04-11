sudo bash remove_image.sh

chmod +x postgres/initdb/setup.sh

sudo docker compose build --no-cache

sudo docker compose up -d