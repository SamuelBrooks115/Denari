# Backend

Denari backend application for financial data ingestion and analysis.

## Setup

1. Install Python 3.12 or higher
2. Install Poetry: `pip install poetry` or follow [Poetry installation guide](https://python-poetry.org/docs/#installation)
3. Install dependencies: `poetry install`
4. Set up environment variables in `.env` file
5. Run the application: `poetry run uvicorn app.main:app --reload`

## Environment Variables

See `.env.example` or `app/core/config.py` for required environment variables.

