# Blog API

Blog management platform built with Django.

## Project Structure

```
blog-django/
├── manage.py
├── .env
├── requirements/
│   ├── base.txt
│   └── dev.txt
├── settings/
│   ├── conf.py
│   ├── base.py
│   ├── urls.py
│   ├── wsgi.py
│   ├── asgi.py
│   └── env/
│       ├── local.py
│       └── prod.py
└── apps/
    ├── abstracts/
    ├── auths/
    └── blog/
```

## Setup & Running

```bash
# 1. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements/dev.txt

# 3. Apply migrations
python manage.py makemigrations
python manage.py migrate

# 4. Start server
python manage.py runserver
```
