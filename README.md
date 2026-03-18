# WhereDidIShoot

Starter stack for a Nuxt 3 frontend, Flask API, MariaDB database, and Nginx reverse proxy.

## Run

```bash
docker compose up --build
```

The app is exposed through Nginx on `http://localhost:8080` by default.

## Dev run

```bash
docker compose -f docker-compose.dev.yml up --build
```

The dev stack is exposed through Nginx on `http://localhost:8081` by default.
Frontend source is mounted into the Nuxt dev container with hot reload enabled, and backend source is mounted into the Flask debug container for automatic reloads.

## Environment

The stack runs with the defaults embedded in `docker-compose.yml`. Copy `.env.example` to `.env` if you want to override credentials or ports.

## Services

- `nginx`: public entrypoint and reverse proxy
- `frontend`: Nuxt 3 SSR app
- `backend`: Flask API served by Gunicorn
- `db`: MariaDB with a named Docker volume

## SDK generation

The frontend uses `@openapitools/openapi-generator-cli` to generate a TypeScript SDK from `backend/openapi.yml`.

```bash
cd frontend
npm install
npm run generate:sdk
```

`docker compose up --build` also runs SDK generation during the frontend image build, so the containerized build stays aligned with the backend spec.

## Useful routes

- `/`: Nuxt frontend
- `/api/health`: Flask health endpoint that also checks database connectivity
