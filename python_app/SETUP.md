# Advanced Setup Guide

This document provides advanced setup and maintenance instructions for the Water Bottles API, focusing on database migrations and local development without Docker.

## Database Migrations (Alembic)

This project uses [Alembic](https://alembic.sqlalchemy.org/) to handle database schema migrations. When you make changes to the SQLAlchemy models in `app/db/models.py`, you will need to generate a new migration script and apply it.

All Alembic commands should be run from within the `python_app` directory.

### Generating a New Migration

After you have modified your models, you can automatically generate a new migration script.

1.  **Access the Running Container:**
    If your Docker container is running, you can get a shell inside it:
    ```bash
    docker-compose exec api bash
    ```

2.  **Generate the Migration:**
    From inside the container (or your local venv if not using Docker), run:
    ```bash
    alembic revision --autogenerate -m "A descriptive message about your changes"
    ```
    This will create a new file in `python_app/migrations/versions/`.

3.  **Review the Migration Script:**
    Always open the newly generated script and review the changes to ensure they are correct. Alembic is good, but not perfect.

### Applying Migrations

To apply all outstanding migrations to your database, run:

```bash
alembic upgrade head
```

The application's entrypoint is configured to run this command on startup, so your database should always be up-to-date when running via Docker Compose. However, you may need to run this manually in other environments.

### Downgrading a Migration

To revert a migration, you can specify the revision to downgrade to, or use a relative number. To revert the last migration:

```bash
alembic downgrade -1
```

## Local Development Without Docker

While Docker is recommended, you can run the application locally using a Python virtual environment.

### Prerequisites

*   Python 3.11+
*   A running PostgreSQL server (optional, can use SQLite)

### Setup

1.  **Create a Virtual Environment:**
    From the `python_app` directory:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Environment:**
    Copy `.env.example` to `.env` and configure your database URL (`DATABASE_URL`). For SQLite, the default is `sqlite:///./water_bottles.db`.

4.  **Run the Application:**
    ```bash
    uvicorn main:app --reload
    ```
    The server will start on `http://localhost:8000`. 