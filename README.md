# RunCode
Team making working shop about running which is model of accual site: 
https://brooks-running.pl

Shop is based on prestashop 1.7.8 version, with scrapper and automatical tests made in selenuim technology. To set up site we use docker compose and my-sql as database for avaible items on site, we also created local backup on main branch.

Sposób uruchomienia
Upewnij się, że masz zainstalowanego Dockera i Docker Compose.

Sklonuj repozytorium:
git clone https://github.com/KacperZuck/RunCode

cd RunCode/

Uruchom kontenery Dockera:

docker compose up -d

Poczekaj, aż kontenery się uruchomią. Można też zobaczyć logi kontenera prestashop

docker compose logs -f prestashop

Otwórz przeglądarkę i wpisz adres:
https://localhost:8002


Team:
Kacper Żuchowski
Tymon Szałankiewicz
Maciej Kowalczyk
Maciek Łukasiewicz

