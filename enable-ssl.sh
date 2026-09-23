#!/usr/bin/env bash
set -e

DOMAIN="smartlawer.com.br"
WWW_DOMAIN="www.smartlawer.com.br"
EMAIL="sergioschina@hotmail.com"
WEBROOT="/srv/certbot/www"

echo "==============================================="
echo "  Ativacao de SSL HTTPS - SmartLawer V2"
echo "==============================================="

# 1. Verificar se DNS ja aponta para a VPS (164.152.35.112)
echo "[1/4] Verificando propagacao DNS..."
RESOLVED_IP=$(python3 -c "import socket; print(socket.gethostbyname('$DOMAIN'))" 2>/dev/null || echo "not_resolved")

if [ "$RESOLVED_IP" != "164.152.35.112" ]; then
    echo "AVISO: $DOMAIN ainda aponta para '$RESOLVED_IP' (esperado: 164.152.35.112)."
    echo "Certifique-se de que publicou a zona no Registro.br e aguarde alguns minutos para propagar."
    echo "Deseja forcar a tentativa mesmo assim? (s/N)"
    read -r resp
    if [[ ! "$resp" =~ ^[sSyY]$ ]]; then
        echo "Cancelado. Execute novamente quando o DNS propagar: ./enable-ssl.sh"
        exit 1
    fi
fi

# 2. Obter certificado Let's Encrypt via webroot
echo "[2/4] Solicitando certificado Let's Encrypt..."
sudo certbot certonly --webroot -w "$WEBROOT" \
    -d "$DOMAIN" -d "$WWW_DOMAIN" \
    --agree-tos --non-interactive \
    --email "$EMAIL"

# 3. Atualizar configuracao do Nginx com bloco HTTPS
echo "[3/4] Atualizando configuracao Nginx..."
cat << 'NGINX_EOF' | sudo tee /opt/smarteng/deploy/nginx-smartlawer.conf > /dev/null
# Redirecionamento HTTP -> HTTPS
server {
    listen 80;
    server_name smartlawer.com.br www.smartlawer.com.br;

    location ^~ /.well-known/acme-challenge/ {
        root /srv/certbot/www;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

# Bloco seguro HTTPS
server {
    listen 443 ssl;
    server_name smartlawer.com.br www.smartlawer.com.br;

    ssl_certificate /etc/letsencrypt/live/smartlawer.com.br/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/smartlawer.com.br/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # HSTS
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains" always;

    location ^~ /.well-known/acme-challenge/ {
        root /srv/certbot/www;
    }

    location /api/ {
        proxy_pass http://smartlawer-api:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 50M;
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
    }

    location = /health {
        proxy_pass http://smartlawer-api:8000/health;
        proxy_set_header Host $host;
    }

    location / {
        proxy_pass http://smartlawer-frontend:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINX_EOF

# 4. Validar e Recarregar Nginx
echo "[4/4] Validando e recarregando Nginx..."
sudo docker cp /opt/smarteng/deploy/nginx-smartlawer.conf smarteng-proxy:/etc/nginx/conf.d/smartlawer.conf
sudo docker exec smarteng-proxy nginx -t
sudo docker exec smarteng-proxy nginx -s reload

echo "==============================================="
echo "  SSL ativado com sucesso em https://$DOMAIN !"
echo "==============================================="
