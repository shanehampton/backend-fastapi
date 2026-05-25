# Backend-FastAPI

\*\*\*WORK IN PROGRESS\*\*\*

A production-grade RESTful backend built with FastAPI. This serves as a reference implementation and generic backend scaffolding for a user-facing application.

## Running the app
To install necessary dependencies, the recommended approach is to establish a virtual environment and install project-specific libraries:

    pip install virtualenv
    virtualenv --python=/path/to/python/interpreter env
    source env/bin/activate
    pip install -r requirements.txt

Create a file called `.env` in the main project directory to configure the app. See `example.env` for reference. You must define a connection string for an active PostgreSQL database via the `db_url` variable. Alternatively, the app will pick up raw environment variables as well.

To run the app server locally:
    
    uvicorn app.main:app

If you would like the server to automatically reflect changes to underlying files during development:

    uvicorn app.main:app --reload
