# Hugo CMS

This is a Django-based Content Management System designed to generate and deploy Hugo static sites.

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd hugo_cms_prod
   ```

2. **Set up the virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Environment Configuration:**
   Set your Django secret key:
   ```bash
   export DJANGO_SECRET_KEY="your-super-secret-key-here"
   ```

4. **Hugo Binary setup:**
   Download the Hugo Extended binary and place it in the `bin/` directory or somewhere in your system PATH.

5. **Database Setup & Run:**
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

## Note on security
The `SECRET_KEY` is loaded from the environment variable `DJANGO_SECRET_KEY`. Ensure this is set appropriately in production. 

## Utilities
The `bin/` directory contains various utility scripts and data ingest scrapers used during development.
