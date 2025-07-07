# Water Bottles API

This is the FastAPI backend for the Water Bottles project. It provides a complete API for user management, water tracking, social features, and much more.

## Features

*   **RESTful API:** A well-structured and documented RESTful API built with FastAPI.
*   **Authentication:** OAuth2 password flow with JWT tokens.
*   **Database:** SQLAlchemy ORM with support for SQLite and PostgreSQL.
*   **Asynchronous Support:** Asynchronous task scheduling for features like reminders.
*   **Configuration:** All settings are managed via `.env` files for easy configuration.
*   **Containerized:** Fully containerized with Docker for consistent development and deployment environments.
*   **Interactive Docs:** Automatic, interactive API documentation provided by Swagger UI (`/docs`) and ReDoc (`/redoc`).

For a full list of features, see the root [README.md](../../README.md).

## API Structure

The API is organized into the following key directories:

```
app/
├── api/          # API endpoints, dependencies
├── core/         # Core logic (config, security, logging)
├── data/         # Data files (e.g., for seeding)
├── db/           # Database setup (session, models)
├── migrations/   # Alembic database migrations
├── models/       # Pydantic schemas for data validation
├── services/     # Business logic for all features
└── static/       # Static files (e.g., user avatars)
```

## Getting Started

The recommended way to run the application for development is using Docker Compose.

### Prerequisites

*   Docker
*   Docker Compose

### Setup

1.  **Create an Environment File:**
    Navigate to the `python_app` directory and create a `.env` file by copying the example:
    ```bash
    cp .env.example .env
    ```
    Review the `.env` file and adjust any settings if necessary. The defaults are configured for local development.

2.  **Build and Run the Container:**
    From the root of the project, run:
    ```bash
    docker-compose up --build
    ```
    This command will build the Docker image, start the API service, and mount your local code into the container.

3.  **Access the API:**
    The API will be available at `http://localhost:8000`.
    *   **Interactive Docs (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)
    *   **Alternative Docs (ReDoc):** [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Live Reloading

The service is configured with live reloading. Any changes you make to the source code in the `python_app` directory will automatically restart the server inside the container.

### Database Migrations

The application uses Alembic to manage database schema migrations. To learn how to create and apply migrations, please see `python_app/SETUP.md`. 