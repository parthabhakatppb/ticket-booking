# Support Ticket System

## Overview
This project delivers a support ticket system with a Django REST backend, a Vite + React frontend, and a PostgreSQL database. Tickets can be filtered and searched, and a dashboard surfaces aggregate stats in real time.

## Setup
1. Export your LLM API key before starting Docker:

```bash
export LLM_API_KEY="your-key-here"
```

2. Build and run everything:

```bash
docker-compose up --build
```

3. Open the app at `http://localhost:5173`.

The backend automatically waits for Postgres and runs `python manage.py migrate` on startup.

## API Endpoints
- `GET /api/tickets/` (filter by `category`, `priority`, `status`, search via `search`)
- `POST /api/tickets/`
- `GET /api/tickets/stats/`
- `POST /api/tickets/classify/`

Example create:

```bash
curl -X POST http://localhost:8000/api/tickets/   -H "Content-Type: application/json"   -d '{"title":"Login fails","description":"Users see a 500 error","category":"technical","priority":"high"}'
```

## LLM Prompt
The backend sends the following prompt for classification:

```text
Return ONLY a JSON object with the keys "suggested_category" and "suggested_priority"
based on these specific options:
categories: billing, technical, account, general
priorities: low, medium, high, critical
```

## LLM Choice
The project uses `gpt-4o-mini` via the Responses API because it is fast and cost-effective for short classification tasks while maintaining strong accuracy.
