# FastAPI CRUD Application

This project is a CRUD application built with FastAPI, utilizing SQLAlchemy for database interactions and Pydantic for data validation.

## Features

- User management
- Post management
- Comment management
- Asynchronous database operations

## Requirements

- Python 3.9 or higher
- PostgreSQL (or any other database supported by SQLAlchemy)

## Installation

1. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd <repository-directory>

2. **Create a virtual environment:**
    ```bash
    python -m venv venv

3. **Activate the virtual environment:**

    **On Windows:**
        `venv\Scripts\activate`

    **On macOS/Linux:**
        `source venv/bin/activate`

4. **Install the requirements:**
    ```bash
    pip install -r requirements.txt

5. **Set up the database:**
    Modify your database settings in `app/core/config.py` to match your PostgreSQL configuration.

    Example:
    ```bash
    DATABASE_URL = "postgresql+asyncpg://username:password@localhost/dbname"

    Then create the database in PostgreSQL if it doesn't already exist:
    ```bash
    CREATE DATABASE dbname;

6. **Run the Application:**
    ```bash
    uvicorn app.main:app --reload

    Your FastAPI application will be running at http://127.0.0.1:8000.


7. **Access the API documentation:**

    Open your web browser and go to:
    ```bash
    http://127.0.0.1:8000/docs

8. **Testing:**
    ```bash
    pytest
