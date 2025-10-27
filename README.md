# Videoflix Backend

Videoflix is a Django-based backend for a streaming platform that allows users to register, log in, and stream videos using HTTP Live Streaming (HLS).  
It includes secure JWT authentication with HttpOnly cookies, email-based account activation and password reset, background processing with Redis and Django-RQ, and REST API endpoints for managing video content.

---

## Table of Contents

- [Features](#features)
- [Technology Stack](#technology-stack)
- [Setup Scenarios](#setup-scenarios)
  - [Scenario A: Local Development (venv)](#scenario-a-local-development-venv)
  - [Scenario B: Docker Compose (recommended)](#scenario-b-docker-compose-recommended)
- [Environment Variables](#environment-variables)
- [Running Tests](#running-tests)
- [API Overview](#api-overview)
- [Video Streaming](#video-streaming)
- [Development Notes](#development-notes)
- [License](#license)

---

## Features

### User Management
- User registration with email confirmation
- Account activation via email link
- Login and logout using JWT with HttpOnly cookies
- Password reset via secure email link

### Authentication
- JWT-based authentication using `djangorestframework-simplejwt`
- Access and refresh tokens stored securely in HttpOnly cookies
- Token refresh endpoint for session extension

### Video Management
- Authenticated users can upload and list videos
- Videos are transcoded asynchronously into HLS segments (360p, 720p, 1080p)
- Automatic thumbnail extraction
- Streaming via HLS (`.m3u8` playlists and `.ts` segments)

### System Architecture
- Django and Django REST Framework
- PostgreSQL (Docker)
- Redis for caching and task queues
- Django RQ for background processing
- MailHog for development email testing

### Testing and Quality
- Automated tests using `pytest` and `pytest-django`
- Over 80% test coverage
- Separate SQLite configuration for isolated test environments

---

## Technology Stack

| Component | Technology |
|------------|-------------|
| Framework | Django 5.2 + Django REST Framework |
| Authentication | SimpleJWT with HttpOnly cookies |
| Task Queue | Redis + Django-RQ |
| Database | PostgreSQL (SQLite for testing) |
| Email | MailHog |
| Testing | pytest, pytest-django, pytest-cov |
| Deployment | Docker Compose + Gunicorn |

---

## Setup Scenarios

The project can be set up in two ways:

---

### Scenario A: Local Development (venv)

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/videoflix-backend.git
   cd videoflix-backend
Create and activate a virtual environment

bash
Code kopieren
python -m venv venv
.\venv\Scripts\activate
Install dependencies

bash
Code kopieren
pip install -r requirements.txt
Create a .env file

bash
Code kopieren
cp .env.template .env
Adjust database settings if necessary (for example, use SQLite for local tests).

Run migrations and start the server

bash
Code kopieren
python manage.py migrate
python manage.py runserver
The backend will be available at:
http://127.0.0.1:8000

Scenario B: Docker Compose (recommended)
This setup runs all required services automatically (PostgreSQL, Redis, Mailhog, web application, worker).

Create a .env file

bash
Code kopieren
cp .env.template .env
Build and start all services

bash
Code kopieren
docker compose up --build
The startup process:

Waits for PostgreSQL

Applies migrations automatically

Creates a superuser (admin@example.com / adminpassword)

Starts Django web and worker services

Access the running services

Service	URL	Description
Backend	http://localhost:8000	Django REST API and Admin interface
Mailhog	http://localhost:8025	Test mail server (for activation and reset emails)
Redis	internal only	Background queue and caching
PostgreSQL	internal only	Database

Admin credentials:

Email: admin@example.com

Password: adminpassword

Environment Variables
All configuration values are read from the .env file.

Variable	Description	Example
SECRET_KEY	Django secret key	django-insecure-xyz...
DEBUG	Enable debug mode	True
ALLOWED_HOSTS	Allowed domains	localhost,127.0.0.1
DB_NAME	Database name	videoflix
DB_USER	Database user	postgres
DB_PASSWORD	Database password	postgres
DB_HOST	Database host	db
DB_PORT	Database port	5432
REDIS_LOCATION	Redis connection URL	redis://redis:6379/1
EMAIL_HOST	Email server host	mailhog
EMAIL_PORT	Email server port	1025
DEFAULT_FROM_EMAIL	Default sender	Videoflix <info@videoflix.com>
FRONTEND_BASE_URL	Frontend base URL	http://127.0.0.1:5500
BACKEND_BASE_URL	Backend base URL	http://127.0.0.1:8000

Running Tests
Option 1: Local (venv)
Run all tests directly:

bash
Code kopieren
pytest -v
Option 2: Inside Docker
Ensure all services are running:

bash
Code kopieren
docker compose up -d
Then execute:

bash
Code kopieren
docker compose exec web pytest -v
Expected output:

diff
Code kopieren
============================= test session starts =============================
collected XX items
============================= XX passed in YYs ================================
To generate coverage:

bash
Code kopieren
pytest --cov=.
API Overview
Authentication Endpoints
Method	Endpoint	Description
POST	/api/register/	Register new user and send activation email
GET	/api/activate/<uidb64>/<token>/	Activate a new user account
POST	/api/login/	Log in and receive JWT cookies
POST	/api/logout/	Log out and clear tokens
POST	/api/password_reset/	Request password reset email
POST	/api/password_confirm/<uidb64>/<token>/	Confirm new password

Video Endpoints
Method	Endpoint	Description
GET	/api/video/	List all available videos
POST	/api/video/upload/	Upload a new video (authenticated)
GET	/api/video/<id>/<resolution>/index.m3u8	Retrieve video manifest
GET	/api/video/<id>/<resolution>/<segment>/	Retrieve video segment

Video Streaming
Uploaded videos are transcoded into multiple HLS renditions using ffmpeg in a background task executed by Django-RQ workers.

Each video has its own directory under:

php-template
Code kopieren
/media/hls/<video_id>/<resolution>/
Available resolutions:

360p

720p

1080p

HLS manifests and segments are served dynamically through the Django API.

Development Notes
Static files are served using WhiteNoise (no nginx required)

Email delivery is simulated via Mailhog during development

CSRF protection is disabled for /api/ routes only (JWT-secured endpoints)

Redis handles both caching and background jobs

Post-save signals automatically trigger transcoding tasks

License
MIT License © 2025 – Developed for educational purposes.

Quick Verification Checklist
Step	Action	Expected Result
1	Run docker compose up --build	All services start successfully
2	Open http://localhost:8000/admin	Django admin is accessible
3	Open http://localhost:8025	Mailhog interface is visible
4	Register via /api/register/	Activation email appears in Mailhog
5	Run docker compose exec web pytest -v	All tests pass successfully