## Сервер

Лінк для nginx

```
sudo ln -s ~/startlink-server/etc/nginx/s.navi.cc /etc/nginx/sites-enabled
```


Ось покрокові команди для bindfs (рекомендовано):

Встанови bindfs (якщо ще не встановлено):

```
sudo apt update
sudo apt install bindfs
```

Створи точку монтування для nginx:

```
sudo mkdir -p /var/www/s.navi.cc
```

Змонтуй каталог з правами для www-data:

```
sudo bindfs -u www-data -g www-data /home/baden/s.navi.cc /var/www/s.navi.cc
```

Файли залишаються у /home/baden/s.navi.cc, але nginx бачить їх у /var/www/s.navi.cc з потрібними правами.

Додай цей монтування у /etc/fstab для автозавантаження:

```
/home/baden/startlink-server/s.navi.cc /var/www/s.navi.cc fuse.bindfs defaults,force-user=www-data,force-group=www-data 0 0
```

Перезапусти nginx:

```
sudo systemctl restart nginx
```

Тепер nginx може показувати сайт з каталогу baden, а всі інші сайти працюють як раніше.

Якшо все ОК, накатуємо SSL.

### SSL

```
  sudo snap install --classic certbot
  sudo ln -s /snap/bin/certbot /usr/bin/certbot
  sudo certbot --nginx
```

## Сервер дрона

```
sudo ln -s /home/baden/startlink-server/etc/systemd/system/drone_server.service /etc/systemd/system/drone_server.service

sudo systemctl daemon-reload
sudo systemctl enable drone_server
sudo systemctl start drone_server
sudo systemctl status drone_server
```
