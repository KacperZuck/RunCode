docker exec -i some-mysql \
mysql \
  -u root \
  -padmin prestashop < prestashop.sql
docker exec prestashop rm -rf /var/www/html/var/cache/*

