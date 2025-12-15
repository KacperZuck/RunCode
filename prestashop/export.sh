docker exec -i some-mysql \
mysqldump \
  -h some-mysql \
  -u root \
  -p prestashop > prestashop.sql

