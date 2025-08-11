# README

# Requirements:

## Local

uv and nodejs:

```bash
# for macos:
brew install uv
brew install nodejs
```

## External Services

Setup a GCP project for both oauth and bigtable and set env vars:

- GOOGLE_CLIENT_ID (oauth)
- GOOGLE_CLIENT_SECRET (oauth)
- GOOGLE_CLOUD_PROJECT (bigtable)
- ANTHROPIC_API_KEY (anthropic api console)

Setup GCP auth locally:

```
gcloud auth application-default login
```

# Development

```bash
# dependencies:
uv sync
cd client && npm install

# development
uv run fastapi dev server/main.py
npm run dev
```

# Architecture

Python backend and SPA for the chat client.

## Auth endpoints under /auth

- GET /auth/login
- GET /auth/logout
- GET /auth/me
- POST /auth/callback (for oauth2 callback)

## Chat endpoints under /chat

- POST /chat/:id (for updating or extending to a new chat; clients are responsible for setting the chat id)
- GET /chats
- GET /chat/:id
