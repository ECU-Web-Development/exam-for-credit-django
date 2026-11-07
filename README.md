# Task app

Django, HTMX, Postgres, Redis and Celery. Supports tasks, comments and notifications.

Run:
```sh
docker compose up --build -d
```

Go to localhost:8000/login. Admin can create accounts at /register.
eli is admin, eli2 and eli3 are users, no_role has no access.

Test:
```sh
docker compose exec api python manage.py test apiapp.tests
```

Logs:
```sh
docker compose logs -f frontend api worker
```

Writes go through Celery. Postgres data uses a volume. Retries and Redis persistence aren't set up yet.
