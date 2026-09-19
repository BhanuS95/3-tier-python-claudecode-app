# Frontend -- Task Manager UI

Plain HTML/CSS/JavaScript (no build step, no framework) that consumes
the backend's REST API under `/api/tasks` and `/health/*`.

## Files

```
frontend/
├── index.html      Page structure + create-task form + edit modal
├── css/style.css   Styling
├── js/app.js        API calls, rendering, event handling
├── nginx.conf       Nginx config used inside the Docker image (static
│                    files + reverse proxy of /api and /health to the
│                    backend service)
└── Dockerfile        Builds an Nginx-based static image
```

## Running locally without Docker

Because this is static HTML/CSS/JS, you can serve it with any static
file server. From the `frontend/` directory:

```bash
python3 -m http.server 3000
```

Then open **http://localhost:3000**.

By default, `js/app.js` calls the backend at `http://localhost:5000`
(see the `API_BASE_URL` constant at the top of the file). Make sure
the backend is running there, and that `CORS_ORIGINS` on the backend
includes `http://localhost:3000` (or `*` for local development).

## Running via Docker / Docker Compose

See the root `README.md` and `docker-compose.yml`. In Compose, the
frontend's own Nginx also proxies `/api/*` and `/health/*` to the
`backend` service over the internal Docker network, so the frontend
works even if you don't expose the backend's port to the host.

## Configuration

The only frontend-facing configuration is `API_BASE_URL` in
`js/app.js`. There is no build step and nothing to compile -- edit and
refresh.
