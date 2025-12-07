FROM prestashop/prestashop:1.7.8

RUN apt-get update && apt-get install -y openssl
RUN openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/private/ssl-cert-snakeoil.key \
    -out /etc/ssl/certs/ssl-cert-snakeoil.pem \
    -subj "/C=PL/ST=./L=Gdansk/O=./OU=./CN=localhost"

RUN a2enmod ssl

RUN a2ensite default-ssl

RUN apt-get clean && rm -rf /var/lib/apt/lists/*