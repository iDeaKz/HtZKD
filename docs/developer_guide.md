# Developer Guide

Welcome to the **Developer Guide** for the **H(t) Zkaedi Healing Solution Dashboard**. This guide provides detailed instructions for setting up the development environment, understanding the project structure, contributing to the codebase, and extending the application's functionalities.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Setting Up the Development Environment](#setting-up-the-development-environment)
- [Project Structure](#project-structure)
- [Running the Application](#running-the-application)
- [Testing](#testing)
- [Database Migrations](#database-migrations)
- [Adding New Features](#adding-new-features)
- [Coding Standards](#coding-standards)
- [Debugging](#debugging)
- [Deployment](#deployment)
- [Contribution Guidelines](#contribution-guidelines)
- [Resources](#resources)

## Prerequisites

Before diving into development, ensure you have the following installed:

- **Operating System:** Linux (Ubuntu 20.04+ recommended) or macOS. Windows users can utilize WSL2.
- **Git:** Version control system.
- **Docker & Docker Compose:** For containerization and orchestration.
- **Python 3.8+:** Programming language for backend development.
- **Node.js & npm:** Required for frontend dependencies (if applicable).
- **Virtual Environment Tools:** `venv` or `virtualenv`.

## Setting Up the Development Environment

1. **Clone the Repository:**

    ```bash
    git clone https://github.com/yourusername/HtZkaediHealingSolution.git /mnt/b/project_plot/HtZkaediHealingSolution
    cd /mnt/b/project_plot/HtZkaediHealingSolution
    ```

2. **Run the Setup Script:**

    ```bash
    ./scripts/setup_env.sh
    ```

    **Note:** Ensure that `setup_env.sh` is executable. If not, run `chmod +x scripts/setup_env.sh`.

3. **Activate the Virtual Environment:**

    ```bash
    source venv/bin/activate
    ```

4. **Edit Environment Variables:**

    After running the setup script, edit the `.env` file to set your `SECRET_KEY` and `API_KEY`.

    ```bash
    nano .env
    ```

## Project Structure

Understanding the project structure is crucial for efficient development.


## Running the Application

1. **Start Docker Services:**

    ```bash
    docker-compose up -d
    ```

    **Explanation:**
    - **Detached Mode (`-d`):** Runs containers in the background.
    - **Services:** Starts both `web` (Dash application) and `db` (PostgreSQL database) services.

2. **Access the Dashboard:**

    Open your web browser and navigate to:

    ```
    http://localhost:8050
    ```

## Testing

1. **Activate the Virtual Environment:**

    ```bash
    source venv/bin/activate
    ```

2. **Run Tests:**

    ```bash
    pytest
    ```

3. **Generate Coverage Report:**

    ```bash
    pytest --cov=app --cov-report=html
    ```

    Open `htmlcov/index.html` in your browser to view detailed coverage metrics.

## Database Migrations

Use **Alembic** for handling database migrations.

1. **Create a Migration Script:**

    ```bash
    alembic revision --autogenerate -m "Add new feature"
    ```

2. **Apply Migrations:**

    ```bash
    alembic upgrade head
    ```

## Adding New Features

1. **Define Models:**

    Add new models in `app/models.py` following SQLAlchemy conventions.

2. **Create Migration:**

    ```bash
    alembic revision --autogenerate -m "Add new model"
    alembic upgrade head
    ```

3. **Develop Components:**

    - **Layouts:** Add new layout components in `app/layouts/`.
    - **Callbacks:** Register new callbacks in `app/callbacks/`.
    - **Utilities:** Add helper functions in `app/utils/`.

4. **Update Tests:**

    Write corresponding tests in the `tests/` directory to ensure new features work as expected.

## Coding Standards

- **PEP 8 Compliance:** Ensure all Python code adheres to PEP 8 standards for readability and consistency.
- **Docstrings:** Provide docstrings for all classes, methods, and functions.
- **Type Hinting:** Utilize type hints for function parameters and return types.
- **Modularity:** Keep the code modular to enhance maintainability and scalability.

## Debugging

- **Logging:** Utilize logging to track application behavior and errors.
- **Debug Mode:** Enable `DEBUG=True` in the `.env` file during development for detailed error messages.
- **Breakpoints:** Use debugging tools and breakpoints to inspect code execution.

## Deployment

Refer to the [Deployment Section](../Deployment.md) for instructions on deploying the application using Docker or Heroku.

## Contribution Guidelines

- **Branching:** Follow Git branching strategies (e.g., feature branches, develop branch).
- **Pull Requests:** Submit pull requests for code reviews before merging.
- **Issue Tracking:** Use GitHub Issues to track bugs and feature requests.
- **Code Reviews:** Ensure code is reviewed by peers for quality and adherence to standards.

## Resources

- **Flask Documentation:** [https://flask.palletsprojects.com/](https://flask.palletsprojects.com/)
- **Dash Documentation:** [https://dash.plotly.com/](https://dash.plotly.com/)
- **SQLAlchemy Documentation:** [https://www.sqlalchemy.org/](https://www.sqlalchemy.org/)
- **Alembic Documentation:** [https://alembic.sqlalchemy.org/](https://alembic.sqlalchemy.org/)
- **Pytest Documentation:** [https://docs.pytest.org/](https://docs.pytest.org/)
- **Docker Documentation:** [https://docs.docker.com/](https://docs.docker.com/)
- **Heroku Documentation:** [https://devcenter.heroku.com/](https://devcenter.heroku.com/)
