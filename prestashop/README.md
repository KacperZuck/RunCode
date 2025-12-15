# PrestaShop Docker Environment

This repository provides a reproducible PrestaShop 1.7.8 development environment using Docker and MySQL.

The environment is fully configured to meet project requirements, including:
* **HTTPS:** Self-signed SSL certificate generated automatically during the build.
* **MailHog:** Email trapping tool for testing notifications.
* **Database:** MySQL 5.7.

---

## Requirements

* Docker and Docker Compose installed

* Git repository cloned locally

* Ports **80**, **443**, and **8025** must be free on your host machine.

---

## Getting Started

1.  **Build and Run**
    Since we use a custom `Dockerfile` to handle SSL certificates, use the `--build` flag for the first run:

    ```bash
    docker compose up -d --build
    ```

2.  **Access the Shop**
    * **Frontend:** [https://localhost](https://localhost)
    * *Note:* Your browser will show a **"Not Secure"** or "Connection is not private" warning. This is expected because we are using a self-signed certificate. You must accept the risk (Click "Advanced" -> "Proceed to localhost") to access the site.

---

## Admin Panel

* **URL:** `https://localhost/admin-dev`
* **Email:** `demo@prestashop.com`
* **Password:** `prestashop_demo`


## MailHog (Email Testing)
Captures all emails sent by the shop (e.g., registration, order confirmation).
* **Interface:** `http://localhost:8025`


## Database (MySQL)
* **Container Name:** `some-mysql`
* **Root Password:** `admin`
* **Database:** `prestashop`
---

## Database Management

### Importing changes

If a team member has pushed a new `db.sql` to the repository, you need to reset your database to match theirs. The cleanest way to do this is:

1.  Stop containers and remove volumes (this wipes your current DB data):
    ```bash
    docker compose down -v
    ```
2.  Start again (Docker will automatically import the new `db.sql`):
    ```bash
    docker compose up -d
    ```

### Exporting changes
If you have made significant changes (e.g., added products, configured modules, changed settings), you must update the `db.sql` file:

1. Export the current database state:

    ```bash
    docker exec some-mysql mysqldump -u root -padmin prestashop > db.sql
    ```

2. Commit and push the updated `db.sql` to the repository.
