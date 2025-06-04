# Starting5

This project is a Flask application. The configuration expects a `DATABASE_URL` environment variable pointing to your database.
If `DATABASE_URL` is not provided, the app falls back to a local SQLite database named `app.db` for development.

Set `SECRET_KEY` if you want a custom session secret; otherwise a default development key is used.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the application:
   ```bash
   export DATABASE_URL=<your-database-url>
   export SECRET_KEY=<optional-secret>
   python run.py
   ```
