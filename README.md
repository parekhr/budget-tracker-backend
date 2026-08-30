# Budget Tracker - Backend

Django REST API powering [Budget Tracker](https://github.com/parekhr/budget-tracker-frontend) - a personal spending, budgeting, and monthly-summary app. Every dollar figure returned by this API is computed server-side; the frontend never re-derives totals from raw records.

## Tech Stack

- Django 6.1 + Django REST Framework
- PostgreSQL (via Docker)
- JWT auth via `djangorestframework-simplejwt`, with a custom email-based login (the API authenticates by email, not username)
- `djangorestframework-camel-case` - the API renders/accepts camelCase JSON so the frontend never touches snake_case
- `django-cors-headers`

## Features

- **Auth**: registration (with auto-login), email-based login + refresh, forgot-password (real email delivery), authenticated change-password, change-username
- **Categories / Transactions / Budgets**: full CRUD, every queryset scoped to `request.user` - users only ever see their own data
- **Protected default category**: every new user automatically gets an "Uncategorized" category that can't be edited or deleted. Deleting any other category atomically reassigns its transactions to "Uncategorized" first, so no transaction is ever left orphaned
- **Summary aggregation**: a single endpoint returns total spent, budgeted, remaining, per-category spend breakdown, and budget-vs-actual - all computed via Django ORM aggregation, never in a loop
- **Spending trends**: a multi-month time series of total spend per month, for charting

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/register/` | Create an account (returns JWTs, doubles as login) |
| POST | `/api/token/` | Login with email + password |
| POST | `/api/token/refresh/` | Exchange a refresh token for a new access token |
| POST | `/api/password-reset/` | Request a password reset email |
| POST | `/api/password-reset/confirm/` | Complete a password reset |
| POST | `/api/change-password/` | Change password (authenticated) |
| POST | `/api/change-username/` | Change username (authenticated) |
| GET | `/api/username/` | Get the current user's username |
| GET/POST | `/api/categories/` | List / create categories |
| GET/PUT/PATCH/DELETE | `/api/categories/{id}/` | Retrieve / update / delete a category |
| GET/POST | `/api/transactions/` | List / create transactions |
| GET/PUT/PATCH/DELETE | `/api/transactions/{id}/` | Retrieve / update / delete a transaction |
| GET/POST | `/api/budgets/` | List / create budgets |
| GET/PUT/PATCH/DELETE | `/api/budgets/{id}/` | Retrieve / update / delete a budget |
| GET | `/api/summary/?month=YYYY-MM` | Monthly totals, spend-by-category, budget-vs-actual |
| GET | `/api/trends/?months=N&endMonth=YYYY-MM` | Total spend per month, for the last N months |

All endpoints except registration, login, token refresh, and the two password-reset endpoints require a `Bearer` JWT in the `Authorization` header.

## Setup

### Prerequisites

- Python 3.14+
- Docker Desktop (for PostgreSQL)

### 1. Clone and create a virtual environment

```bash
python -m venv venv
venv\Scripts\activate   # Windows
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment variables

Create a `.env` file in `backend/`:

```
POSTGRES_DB=budget_tracker
POSTGRES_USER=budget_tracker
POSTGRES_PASSWORD=your-local-password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password
```

`EMAIL_HOST_PASSWORD` is a [Gmail App Password](https://myaccount.google.com/apppasswords), not your regular account password.

> Note: `SECRET_KEY` is currently hardcoded in `config/settings.py` for local development - this needs to move to an environment variable before this is ever deployed publicly.

### 4. Start PostgreSQL

```bash
docker compose up -d
```

### 5. Run migrations

```bash
python manage.py migrate
```

### 6. Create a superuser (for `/admin/`)

```bash
python manage.py createsuperuser
```

### 7. Run the dev server

```bash
python manage.py runserver
```

The API is now available at `http://localhost:8000/api/`.

## Related

- [Frontend](https://github.com/parekhr/budget-tracker-frontend) - the React app this API serves
