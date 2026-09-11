# HireIQ

HireIQ is a Multimodal AI Interview Intelligence Platform.

## Day 1 Stack

- FastAPI
- PostgreSQL
- Redis
- Celery
- SQLAlchemy
- Docker
- Docker Compose

## Architecture

Client
   |
   v
FastAPI
   |
   +---- PostgreSQL
   |
   +---- Redis
             |
             v
        Celery Worker

## Run the Project

Make sure Docker Desktop is running.

Run:

```bash
docker compose up --build