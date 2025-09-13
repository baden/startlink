server {
    server_name s.navi.cc;

    root /var/www/s.navi.cc;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }

    # Для WebSocket (якщо потрібно)
    location /ws {
        proxy_pass http://localhost:8765;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    # Логи
    access_log /var/log/nginx/s.navi.cc.access.log;
    error_log /var/log/nginx/s.navi.cc.error.log;

    listen 443 ssl; # managed by Certbot
    ssl_certificate /etc/letsencrypt/live/s.navi.cc/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/s.navi.cc/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot

}
server {
    if ($host = s.navi.cc) {
        return 301 https://$host$request_uri;
    } # managed by Certbot


    listen 80;
    server_name s.navi.cc;
    return 404; # managed by Certbot


}
