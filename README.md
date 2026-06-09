# 💫 Dating App

A modern Persian-language dating app for the Iranian market. Free to use, with optional premium subscription to remove ads.

---

## Features

- 🔍 Location-based profile discovery
- ❤️ Swipe to like or pass
- 💬 Real-time chat with matches
- 📸 Photo verification & moderation
- ✅ Identity verification badge
- 🎁 Rewards for watching ads and leaving reviews
- 👑 Premium subscription (ad-free experience)

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python) |
| Database | PostgreSQL + PostGIS |
| Cache / Realtime | Redis |
| Task Queue | Celery |
| Mobile | Flutter |
| Containers | Docker + Docker Compose |

---

## Prerequisites

Make sure you have these installed before starting:

| Tool | Version | Download |
|------|---------|----------|
| Python | 3.11+ | https://python.org |
| Docker | Latest | https://docker.com |
| Docker Compose | v2+ | included with Docker Desktop |
| Git | Latest | https://git-scm.com |

---

## Setup Guide

### 🐧 Ubuntu / Debian

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/dating-app.git
cd dating-app

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Copy environment file and fill in your values
cp .env.example .env
nano .env

# 5. Install Docker (skip if already installed)
sudo apt update
sudo apt install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo usermod -aG docker $USER
newgrp docker

# 6. Start database and Redis
docker compose up -d

# 7. Run database migrations
alembic upgrade head

# 8. Start the development server
uvicorn app.main:app --reload
```

---

### 🍎 macOS

```bash
# 1. Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. Install Python
brew install python@3.11

# 3. Clone the repository
git clone https://github.com/YOUR_USERNAME/dating-app.git
cd dating-app

# 4. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# 5. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 6. Copy environment file and fill in your values
cp .env.example .env
nano .env

# 7. Install Docker Desktop for Mac
# Download from: https://www.docker.com/products/docker-desktop/
# After installing, open Docker Desktop and wait for it to start

# 8. Start database and Redis
docker compose up -d

# 9. Run database migrations
alembic upgrade head

# 10. Start the development server
uvicorn app.main:app --reload
```

---

### 🪟 Windows

> **Recommended:** Use WSL2 (Windows Subsystem for Linux) for the best experience.
> Follow the Ubuntu guide inside WSL2.

**Native Windows setup:**

```powershell
# 1. Install Python from https://python.org (check "Add to PATH" during install)

# 2. Install Git from https://git-scm.com

# 3. Clone the repository (in PowerShell or Git Bash)
git clone https://github.com/YOUR_USERNAME/dating-app.git
cd dating-app

# 4. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate

# 5. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 6. Copy environment file and fill in your values
copy .env.example .env
notepad .env

# 7. Install Docker Desktop for Windows
# Download from: https://www.docker.com/products/docker-desktop/
# Enable WSL2 backend during installation

# 8. Start database and Redis (in PowerShell with Docker running)
docker compose up -d

# 9. Run database migrations
alembic upgrade head

# 10. Start the development server
uvicorn app.main:app --reload
```

---

## Verify Setup

After starting the server, open your browser:

- **Health check:** http://localhost:8000/health → should return `{"status": "ok"}`
- **API docs (Swagger):** http://localhost:8000/docs
- **API docs (ReDoc):** http://localhost:8000/redoc

---

## Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```env
# Database
DATABASE_URL=postgresql+asyncpg://dating_user:dating_pass@localhost:5432/dating_db

# Redis
REDIS_URL=redis://localhost:6379

# Security — change this to a long random string in production
SECRET_KEY=your-secret-key-here

# JWT
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Google OAuth (get from https://console.cloud.google.com)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=

# App
APP_NAME=DatingApp
DEBUG=True
```

---

## Running Tests

```bash
# Make sure venv is activated
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows

# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run a specific test file
pytest tests/test_auth.py -v
```

> Tests run against an isolated database that is created fresh and destroyed after each run.

---

## Docker Services

| Service | Port | Description |
|---------|------|-------------|
| PostgreSQL + PostGIS | 5432 | Main database |
| Redis | 6379 | Cache + realtime |

```bash
# Start services
docker compose up -d

# Stop services
docker compose down

# View logs
docker compose logs -f

# Reset database (WARNING: deletes all data)
docker compose down -v
docker compose up -d
alembic upgrade head
```

---

## Project Structure

```
dating-app/
├── app/
│   ├── api/v1/endpoints/   # Route handlers
│   ├── core/               # Config, security, dependencies
│   ├── db/                 # Database engine and session
│   ├── models/             # SQLAlchemy models
│   ├── schemas/            # Pydantic schemas (request/response)
│   ├── services/           # Business logic
│   ├── tasks/              # Celery async tasks
│   └── main.py             # FastAPI app entry point
├── alembic/                # Database migrations
├── tests/                  # Unit and integration tests
├── docker-compose.yml
├── .env.example
├── requirements.txt
├── dev.md                  # Developer session documentation
└── README.md
```

---

## Contributing

This is a private project. For access, contact the project owner.

---

## License

Private — All rights reserved.
