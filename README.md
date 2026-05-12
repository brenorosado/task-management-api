# Task Management API

A REST API for managing workspaces, projects, and tasks. Built with Django and Django REST Framework.

## Tech Stack

- **Python 3.9+**
- **Django 4.2**
- **Django REST Framework**
- **Simple JWT** — authentication
- **drf-spectacular** — OpenAPI/Swagger docs
- **django-environ** — environment variable management
- **uv** — package manager

---

## Getting Started

### 1. Clone and install dependencies

```bash
git clone <repo-url>
cd task-management-api
uv sync
```

### 2. Configure environment variables

Copy the example below into a `.env` file at the project root:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 3. Run migrations

```bash
python manage.py migrate
```

### 4. Start the development server

```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000`.  
Interactive docs are at `http://localhost:8000/api/docs/`.

---

## Running Tests

```bash
python manage.py test apps/tasks apps/projects apps/workspaces apps/users
```

---

## API Reference

With the server running, the full interactive API reference is available at:

```
http://localhost:8000/api/docs/
```

---

## Data Model

```
Workspace
└── Project (many)
    ├── ProjectMember (many)
    └── Task (many)
        ├── assigned_to → User (M2M)
        └── blocked_by → Task (M2M, self-referential)
```

### Task statuses

- `todo` — not started
- `in_progress` — being worked on
- `blocked` — waiting on another task
- `done` — completed

### Soft deletes

Workspaces, projects, and tasks are never permanently deleted. Each has a `deleted` boolean and `deleted_at` timestamp. Deleted resources are excluded from all standard listing and detail endpoints.

---

## Access Control

| Resource | Create | Read | Update | Delete |
|----------|--------|------|--------|--------|
| Workspace | Any authenticated user | Owner or project member | Owner only | Owner only |
| Project | Workspace owner | Owner or project member | Owner only | Owner only |
| Task | Owner or project member | Owner or project member | Owner or project member | Owner or project member |
| Deleted tasks | — | Workspace owner only | — | — |
| Reactivate task | — | — | Workspace owner only | — |
