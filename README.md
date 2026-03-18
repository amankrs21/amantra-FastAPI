# Amantra Backend

![Python 3.13](https://img.shields.io/badge/Python-3.13-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.135+-009688?logo=fastapi)
![MongoDB](https://img.shields.io/badge/MongoDB-Motor-47A248?logo=mongodb)
![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue)

FastAPI backend for the **Amantra** mobile/web app — a personal productivity suite with encrypted vault, journal, watchlist tracker, and AI-powered newsletter.

## Features

- **Authentication** — Email/password with OTP email verification + Google OAuth
- **Password Vault** — AES-GCM encrypted password storage with client-side key
- **Encrypted Journal** — End-to-end encrypted journal entries
- **Watchlist Tracker** — Track movies/series/anime with parts progress
- **AI Newsletter** — Personalized news feed via Tavily search + Mistral AI curation
- **PIN/Encryption Key** — User-managed encryption key for vault & journal

## Tech Stack

| Layer | Tech |
|-------|------|
| Framework | FastAPI + Pydantic v2 |
| Database | MongoDB (Motor async driver) |
| Auth | PyJWT, bcrypt, Google OAuth |
| Encryption | cryptography (AES-GCM) |
| Email | aiosmtplib |
| AI | Tavily API, Mistral AI |
| Serialization | orjson |
| HTTP Client | aiohttp |

## Project Structure

```
src/
├── app.py                  # FastAPI app, lifespan, CORS, routes
├── config.py               # Pydantic settings from .env
├── database.py             # Motor MongoDB connection
├── dependencies.py         # Dependency injection (services/repos)
├── middleware/
│   └── auth.py             # JWT auth + encryption key verification
├── models/                 # Pydantic request/response models
├── routers/                # API route handlers
├── services/               # Business logic
├── repository/             # Data access layer (MongoDB)
└── helpers/
    ├── auth_helper.py      # Password hashing, JWT, OTP, Google token
    ├── cipher.py           # AES-GCM encrypt/decrypt
    └── response_helper.py  # Response builders, serialization
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| **Auth** | `/api/auth` | |
| `POST` | `/api/auth/login` | Login with email/password |
| `POST` | `/api/auth/register` | Register new account |
| `POST` | `/api/auth/verify` | Verify email OTP |
| `POST` | `/api/auth/resend-otp` | Resend verification OTP |
| `POST` | `/api/auth/forgot-password` | Send password reset OTP |
| `POST` | `/api/auth/reset-password` | Reset password with OTP |
| `POST` | `/api/auth/google` | Google OAuth login |
| **User** | `/api/user` | |
| `GET` | `/api/user/fetch` | Get current user profile |
| `PATCH` | `/api/user/update` | Update profile |
| `PATCH` | `/api/user/changePassword` | Change password |
| `DELETE` | `/api/user/deactivate` | Delete account + all data |
| **PIN** | `/api/pin` | |
| `POST` | `/api/pin/verify` | Verify encryption key |
| `POST` | `/api/pin/setText` | Set encryption key |
| `GET` | `/api/pin/reset` | Reset PIN (wipes encrypted data) |
| **Vault** | `/api/vault` | |
| `POST` | `/api/vault/fetch` | List vaults (paginated) |
| `POST` | `/api/vault/add` | Add vault entry |
| `PATCH` | `/api/vault/update` | Update vault entry |
| `DELETE` | `/api/vault/delete/{id}` | Delete vault entry |
| `POST` | `/api/vault/{id}` | Decrypt vault password |
| **Journal** | `/api/journal` | |
| `GET` | `/api/journal/fetch` | List journals |
| `POST` | `/api/journal/add` | Add journal entry |
| `PATCH` | `/api/journal/update` | Update journal entry |
| `DELETE` | `/api/journal/delete/{id}` | Delete journal entry |
| `POST` | `/api/journal/{id}` | Decrypt journal content |
| **Watchlist** | `/api/watchlist` | |
| `GET` | `/api/watchlist/fetch` | List watchlist items |
| `POST` | `/api/watchlist/add` | Add to watchlist |
| `PUT` | `/api/watchlist/update/{id}` | Update watchlist item |
| `DELETE` | `/api/watchlist/delete/{id}` | Delete watchlist item |
| `GET` | `/api/watchlist/subscribed` | Get news-subscribed items |
| **Newsletter** | `/api/newsletter` | |
| `GET` | `/api/newsletter/feed` | Get AI-curated news feed |

## Setup

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager
- MongoDB instance

### Install & Run

```bash
git clone https://github.com/amankrs21/amantra-FastAPI.git
cd amantra-FastAPI

# Install dependencies
uv sync

# Configure environment
cp .env.example .env
# Edit .env with your values

# Run development server
uv run uvicorn src.app:app --reload --port 8000
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `CORS_ORIGIN` | Comma-separated allowed origins |
| `MONGO_URL` | MongoDB connection string |
| `JWT_SECRET` | Secret key for JWT signing |
| `PASSWORD_KEY` | 32-char key for AES-GCM encryption |
| `GOOGLE_CLIENT_IDS` | Google OAuth client IDs (comma-separated) |
| `SMTP_EMAIL` | Gmail address for sending OTP |
| `SMTP_PASSWORD` | Gmail app password |
| `TAVILY_API_KEY` | Tavily API key for news search |
| `MISTRAL_API_KEY` | Mistral AI API key for curation |

## Docker

```bash
docker build -t amantra-backend .
docker run -p 7860:7860 --env-file .env amantra-backend
```

## HuggingFace Spaces

This app is configured to run on [HuggingFace Spaces](https://huggingface.co/spaces) (port 7860). Set environment variables as Space secrets.

## Related

- **Frontend**: [amankrs21/amantra](https://github.com/amankrs21/amantra)

## License

[Apache 2.0](LICENSE)
