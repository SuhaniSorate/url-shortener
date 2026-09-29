# URL Shortener

A URL shortener built with **Python, Django and Django REST Framework**. It creates short Base62 links, redirects visitors, tracks clicks, and includes user accounts (JWT), rate limiting, caching and a simple web interface.

## Features

- Base62 short-code generation
- Custom aliases (3-30 characters: letters, numbers, `-`, `_`)
- Link expiry dates (expired links return `410 Gone`)
- Click tracking: time, referrer, device type, hashed IP (for privacy)
- Analytics per link: total clicks, unique visitors, clicks per day, top referrers, devices
- User registration and login with JWT; users can only manage their own links
- Full CRUD API for links, including enable/disable
- Rate limiting on link creation (20 per minute per user)
- Redirect caching, cleared when a link is edited or deleted
- Input and URL validation
- Simple responsive web interface
- Automated tests (13)

## Tech stack

| Area | Technology |
|---|---|
| Backend | Python, Django, Django REST Framework |
| Auth | JWT (djangorestframework-simplejwt) |
| Database | SQLite (development) |
| Cache | Redis (falls back to Django's in-memory cache when REDIS_URL is not set) |
| Frontend | HTML, CSS, JavaScript (single page) |

## Setup

```bash
git clone https://github.com/SuhaniSorate/url-shortener.git
cd url-shortener
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open http://127.0.0.1:8000 for the web interface.

### Optional: use Redis for caching

Start Redis with Docker (or use any local Redis server), then point the app at it:

```bash
docker compose up -d
export REDIS_URL=redis://127.0.0.1:6379/1
python manage.py runserver
```

Without `REDIS_URL`, the app falls back to Django's in-memory cache. The caching code is the same for both.

### Run the tests

```bash
python manage.py test
```

## How it works

1. A logged-in user submits a long URL (optionally with an alias and expiry).
2. The URL is validated and saved. The short code is the custom alias, or the Base62 encoding of the database id.
3. When someone opens `/<short_code>`, the app looks the link up (cache first, then database).
4. If the link is active and not expired, a click is recorded and the visitor is redirected with `302`.
5. Editing, disabling or deleting a link clears its cache entry.

## API

All `/api/urls...` endpoints need the header `Authorization: Bearer <access_token>`.

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/register` | Create an account |
| POST | `/api/login` | Get an access token |
| POST | `/api/urls` | Create a short URL |
| GET | `/api/urls` | List your URLs |
| GET | `/api/urls/{id}` | Get URL details |
| PUT | `/api/urls/{id}` | Update alias, expiry or status |
| DELETE | `/api/urls/{id}` | Delete a URL |
| GET | `/api/urls/{id}/analytics` | Click analytics |
| GET | `/{short_code}` | Redirect to the original URL |

## Project structure

```
config/              Django settings and root URL configuration
urls/models.py       ShortURL and ClickEvent models, Base62 encoder, cache invalidation
urls/serializers.py  Validation and short-code creation
urls/views.py        API views, redirect and analytics
urls/templates/      Single-page web interface
urls/tests.py        Automated tests
```

## Notes and limitations

- Settings are for development (`DEBUG` on, `ALLOWED_HOSTS = ['*']`). A production deployment would need a secret key from the environment, a production database and a proper web server.
- Background jobs (scheduled expiry cleanup and daily analytics aggregation) are not implemented. Expiry is enforced at redirect time, and analytics are computed on request.

## Possible improvements

QR codes, password-protected links, bulk CSV upload, Celery scheduled jobs, team workspaces, exportable analytics.

## Author

Suhani Sorate | Priyadarshini College of Engineering , Nagpur