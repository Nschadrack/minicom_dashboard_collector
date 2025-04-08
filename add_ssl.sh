sudo apt-get update -y
sudo apt-get install certbot python3-certbot-nginx -y

sudo certbot --nginx -d dashboard.example.com -d www.dashboard.example.com

sudo chmod 755 /etc/letsencrypt/{live,archive}
sudo chmod 644 /etc/letsencrypt/live/dashboard.example.com/*.pem