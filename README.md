# Videoflix Backend

Videoflix is a Django-based backend for a streaming platform that allows users to register, log in, and stream videos using HTTP Live Streaming (HLS).  
It includes secure JWT authentication with HttpOnly cookies, email-based account activation and password reset, background processing with Redis and Django-RQ, and REST API endpoints for managing video content.

---

## Table of Contents

- [Features](#features)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Installation and Setup](#installation-and-setup)
- [Environment Variables](#environment-variables)
- [Running the Server](#running-the-server)
- [Testing](#testing)
- [Test Coverage](#test-coverage)
- [API Overview](#api-overview)
- [Video Streaming](#video-streaming)
- [Background Tasks](#background-tasks)
- [Development Notes](#development-notes)
- [License](#license)

---

## Features

**User Management**
- User registration with email and password
- Account activation via email link
- Login and logout using JWT with HttpOnly cookies
- Password reset via secure email link

**Authentication**
- JWT-based authentication using `djangorestframework-simplejwt`
- Access and refresh tokens stored securely in HttpOnly cookies
- Token refresh via cookie endpoint

**Video Management**
- Authenticated users can view a list of all available videos
- Videos are streamed using HLS (`.m3u8` playlists and `.ts` segments)
- Automatic thumbnail generation on upload
- Asynchronous video transcoding using `django-rq`

**System Architecture**
- Django and Django REST Framework
- PostgreSQL as database (SQLite for testing)
- Redis for caching and background queues
- Django RQ for asynchronous task handling

**Security**
- CSRF protection disabled for `/api/` routes only
- JWT stored in HttpOnly cookies (no localStorage exposure)
- Directory traversal prevention for video files

**Testing and Quality**
- More than 87% test coverage using `pytest` and `pytest-cov`
- Unit tests for all major API endpoints (authentication and videos)
- Isolated test settings using SQLite

---

## Technology Stack

| Component | Technology |
|------------|-------------|
| Framework | Django 5.2 + Django REST Framework |
| Authentication | SimpleJWT with HttpOnly cookies |
| Background Queue | Redis + Django-RQ |
| Database | PostgreSQL (SQLite for tests) |
| Testing | pytest, pytest-django, coverage |
| Email | MailHog (local development) |
| Deployment | Gunicorn + Whitenoise |

---

## Project Structure

videoflix_backend/
│
├── accounts/ # User registration, login, password reset
│ ├── authentication.py
│ ├── serializers.py
│ ├── views.py
│ ├── utils.py
│ ├── models.py
│ └── test_accounts_api.py
│
├── videos/ # Video models, API endpoints, transcoding
│ ├── models.py
│ ├── views.py
│ ├── serializers.py
│ ├── tasks.py
│ └── test_videos_api.py
│
├── core/ # Global configuration and middleware
│ ├── settings.py
│ ├── settings_test.py
│ ├── middleware.py
│ ├── urls.py
│ ├── wsgi.py
│ └── asgi.py
│
├── manage.py
├── requirements.txt
└── README.md

yaml
Code kopieren

---

## Installation and Setup

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/videoflix-backend.git
2. Create and Activate Virtual Environment
3. Install Dependencies
4. Apply Migrations
5. Create Superuser (optional)
6. Run the Development Server

The backend will be available at:
http://127.0.0.1:8000

Environment Variables
Create a .env file in the root directory. Example:

env
Code kopieren
SECRET_KEY=your_django_secret_key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=videoflix_db
DB_USER=videoflix_user
DB_PASSWORD=supersecretpassword
DB_HOST=db
DB_PORT=5432

# Email
EMAIL_HOST=mailhog
EMAIL_PORT=1025
DEFAULT_FROM_EMAIL=no-reply@videoflix.local

FRONTEND_BASE_URL=http://127.0.0.1:5500
BACKEND_BASE_URL=http://127.0.0.1:8000

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_LOCATION=redis://redis:6379/1
Running the Server
bash
Code kopieren
python manage.py runserver
Testing
Local tests use core/settings_test.py which switches the database to SQLite for easier local execution.

Uncovered modules include setup files (manage.py, wsgi.py, tasks.py), which are excluded from functional test scope.

API Overview
Authentication Endpoints
Method	Endpoint	Description
POST	/api/register/	Register new user and send activation email
GET	/api/activate/<uidb64>/<token>/	Activate user account
POST	/api/login/	Login and receive JWT cookies
POST	/api/logout/	Logout and clear cookies
POST	/api/token/refresh/	Refresh JWT access token
POST	/api/password_reset/	Request password reset email
POST	/api/password_confirm/<uidb64>/<token>/	Confirm and set new password

Video Endpoints
Method	Endpoint	Description
GET	/api/video/	List all available videos (auth required)
POST	/api/video/upload/	Upload new video (auth required)
GET	/api/video/<movie_id>/<resolution>/index.m3u8	Get video manifest
GET	/api/video/<movie_id>/<resolution>/<segment>/	Get video segment

Video Streaming
Videos are transcoded into multiple resolutions using ffmpeg (through Django-RQ workers).

HLS manifests and segments are stored in /media/hls/<id>/<resolution>/.

Supported resolutions: 360p, 720p, 1080p.

