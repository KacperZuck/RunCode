# PrestaShop Docker Environment

This repository provides a reproducible PrestaShop development environment using Docker and MySQL.

---

## Requirements

* Docker and Docker Compose installed

* Git repository cloned locally

---

## Getting Started

1.  Run the containers in detached mode:

    ```bash
    docker compose up -d
    ```

2.  Open the shop in your browser:
    * **Frontend:** `http://localhost:8080`

---

## Admin Panel

* **URL:** `http://localhost:8080/admin-dev`
* **Email:** `demo@prestashop.com`
* **Password:** `prestashop_demo`

---

## Database Management

### Importing Database Dump

Run this command to import the `db.sql` file into the `some-mysql` container:

    ```bash
    docker exec -i some-mysql mysql -u root -padmin prestashop < db.sql
    ```

### Exporting Database Dump
Run this command to export the current database state from the container into `db.sql`:

    ```bash
    docker exec some-mysql mysqldump -u root -padmin prestashop > db.sql
    ```


### When to Update the Dump
The db.sql file in the repository should be updated after any significant changes, such as:
* After installing or removing modules
* After adding products or configuration changes
* After data or structural database updates
Note: Team members only need to pull the changes and re-import the updated db.sql.

## First-Time setup

1. Clone the repository.
2. Start the containers from Runcode/prestashop:
    ```bash
    docker compose up -d
    ```
3. Import the shared database dump:
    ```bash
    docker exec -i some-mysql mysql -u root -padmin prestashop < db.sql

    ```
