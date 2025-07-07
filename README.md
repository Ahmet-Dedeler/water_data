# Water Bottles - Advanced Health Tracking API

This repository contains the backend API for the Water Bottles project, a comprehensive health and wellness platform designed to help users track their water intake, achieve health goals, and engage with a community.

## Project Overview

This project is built with a modern Python stack and is designed for scalability and maintainability. It features a robust FastAPI backend, a relational database managed by SQLAlchemy and Alembic, and a complete suite of features to support a rich user experience. The entire application is containerized with Docker for easy setup and deployment.

### Core Features

*   **User Management:** Secure user authentication, profile management (avatars, bios), and password reset functionality.
*   **Water Logging:** A flexible system for users to log their daily water intake.
*   **Health Goals:** Create and track custom health and hydration goals.
*   **Gamification:** An achievement system to reward users for milestones and consistency.
*   **Social Platform:** A full-featured social system with followers, friends, activity feeds, and commenting.
*   **Advanced Analytics:** In-depth statistics, time series data, and a public leaderboard.
*   **Notifications:** A configurable system for in-app and push notifications.
*   **Admin Dashboard:** A suite of tools for administrators to manage the platform and its users.
*   **API Key Management:** Securely generate and manage API keys for third-party integrations.

### Tech Stack

*   **Backend:** FastAPI, Python 3.11
*   **Database:** SQLAlchemy ORM, SQLite (for development), PostgreSQL-compatible
*   **Migrations:** Alembic
*   **Containerization:** Docker, Docker Compose
*   **Testing:** Pytest
*   **Linting:** Flake8
*   **CI/CD:** GitHub Actions

## Getting Started

For detailed instructions on setting up the development environment, please see the `README.md` and `SETUP.md` files inside the `python_app` directory.

The application is fully containerized. Once you have Docker and Docker Compose installed, you can get the entire stack running with a few simple commands.

## Contributing

Please see `docs/CONTRIBUTING.md` for details on how to contribute to the project. 