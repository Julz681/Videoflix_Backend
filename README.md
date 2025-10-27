# Videoflix Backend

Videoflix is a Django-based backend for a streaming platform that allows users to register, log in, and stream videos using HTTP Live Streaming (HLS).  
It provides secure JWT authentication with HttpOnly cookies, email-based account activation and password reset, background processing with Redis and Django-RQ, and REST API endpoints for managing video content.

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

## **Features**

### **User Management**
- Registration with email confirmation  
- Account activation via secure link  
- Login & logout with JWT (HttpOnly cookies)  
- Password reset via email link  

### **Authentication**
- JWT authentication using `djangorestframework-simplejwt`  
- Tokens stored securely in HttpOnly cookies  
- Access & refresh token rotation  

### **Video Management**
- Authenticated users can upload and browse videos  
- Automatic thumbnail generation  
- Asynchronous transcoding to multiple HLS resolutions (360p, 720p, 1080p)  
- Video streaming via HLS (`.m3u8` and `.ts`)  

### **System Architecture**
- Django + DRF  
- PostgreSQL (Docker)  
- Redis for background jobs and caching  
- Django-RQ for asynchronous processing  
- MailHog for email testing  

### **Testing and Quality**
- Test suite using `pytest` + `pytest-django`  
- Over 80 % coverage  
- Isolated SQLite config for testing  

---

## **Technology Stack**

| Component | Technology |
|------------|-------------|
| Framework | Django 5.2 + Django REST Framework |
| Authentication | SimpleJWT + HttpOnly cookies |
| Task Queue | Redis + Django-RQ |
| Database | PostgreSQL (Docker) / SQLite (tests) |
| Email | MailHog |
| Testing | pytest, pytest-django, pytest-cov |
| Deployment | Docker Compose + Gunicorn |

---

## **Setup Scenarios**

You can set up the project in two different ways:

---

### **Scenario A: Local Development (venv)**

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/videoflix-backend.git
   cd videoflix-backend
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create the `.env` file**
   ```bash
   cp .env.template .env
   ```
   *(You can use SQLite locally by adjusting the database settings if desired.)*

5. **Run migrations and start the development server**
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

   **Backend available at:** [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

### **Scenario B: Docker Compose (recommended)**

This setup automatically runs all required services (PostgreSQL, Redis, Mailhog, Django web & worker).

1. **Create the `.env` file**
   ```bash
   cp .env.template .env
   ```

2. **Build and start all services**
   ```bash
   docker compose up --build
   ```

   During startup:
   - Waits for PostgreSQL to become ready  
   - Applies migrations automatically  
   - Creates a superuser (`admin@example.com / adminpassword`)  
   - Starts the Django web server and background worker  

3. **Access the running services**

| Service | URL | Description |
|----------|-----|-------------|
| Backend | [http://localhost:8000](http://localhost:8000) | Django REST API + Admin |
| Mailhog | [http://localhost:8025](http://localhost:8025) | Local email testing |
| Redis | internal only | Caching + RQ tasks |
| PostgreSQL | internal only | Application database |

**Default admin credentials**

| Key | Value |
|-----|-------|
| Email | `admin@example.com` |
| Password | `adminpassword` |

---

## **Environment Variables**

All settings are loaded from `.env`.  
The template is fully compatible with `docker-compose.yml` so no manual edits are required.

| Variable | Description | Example |
|-----------|--------------|----------|
| `SECRET_KEY` | Django secret key | `django-insecure-example-key` |
| `DEBUG` | Enable debug mode | `True` |
| `ALLOWED_HOSTS` | Allowed hosts | `localhost,127.0.0.1` |
| `DB_NAME` | Database name | `videoflix` |
| `DB_USER` | Database user | `postgres` |
| `DB_PASSWORD` | Database password | `postgres` |
| `DB_HOST` | Database host | `db` |
| `DB_PORT` | Database port | `5432` |
| `REDIS_LOCATION` | Redis URL | `redis://redis:6379/1` |
| `EMAIL_HOST` | Mail server | `mailhog` |
| `EMAIL_PORT` | Mail port | `1025` |
| `DEFAULT_FROM_EMAIL` | Sender address | `Videoflix <info@videoflix.local>` |
| `FRONTEND_BASE_URL` | Frontend URL | `http://127.0.0.1:5500` |
| `BACKEND_BASE_URL` | Backend URL | `http://127.0.0.1:8000` |
| `DJANGO_SUPERUSER_EMAIL` | Admin email | `admin@example.com` |
| `DJANGO_SUPERUSER_PASSWORD` | Admin password | `adminpassword` |

---

## **Running Tests**

### **Option 1: Local (venv)**
   ```bash
   pytest -v
   ```

### **Option 2: Inside Docker**
   ```bash
   docker compose up -d
   docker compose exec web pytest -v
   ```

Expected output:
```
============================= test session starts =============================
collected XX items
============================= XX passed in YYs ================================
```

Generate coverage report:
   ```bash
   pytest --cov=.
   ```

---

## **API Overview**

### **Authentication Endpoints**

| Method | Endpoint | Description |
|--------|-----------|-------------|
| POST | `/api/register/` | Register new user and send activation email |
| GET | `/api/activate/<uidb64>/<token>/` | Activate a user account |
| POST | `/api/login/` | Log in and receive JWT cookies |
| POST | `/api/logout/` | Log out and clear cookies |
| POST | `/api/password_reset/` | Request password reset email |
| POST | `/api/password_confirm/<uidb64>/<token>/` | Confirm and set new password |

### **Video Endpoints**

| Method | Endpoint | Description |
|--------|-----------|-------------|
| GET | `/api/video/` | List all available videos |
| POST | `/api/video/upload/` | Upload a new video (auth required) |
| GET | `/api/video/<id>/<resolution>/index.m3u8` | Retrieve video manifest |
| GET | `/api/video/<id>/<resolution>/<segment>/` | Retrieve video segment |

---

## **Video Streaming**

Uploaded videos are transcoded into multiple HLS renditions using `ffmpeg` in background tasks executed by Django-RQ workers.  

Each video is stored under:
```
/media/hls/<video_id>/<resolution>/
```

Supported resolutions:
- 360p  
- 720p  
- 1080p  

HLS manifests and segments are served dynamically via Django file responses.

---

## **Development Notes**
- Static files served via WhiteNoise (no nginx required)  
- Email delivery simulated via MailHog  
- CSRF protection disabled only for `/api/` routes (JWT-secured)  
- Redis handles both caching and background tasks  
- Post-save signals trigger automatic video transcoding  

---

## **License**

MIT License © 2025 – Developed for educational use.

---

## **Quick Verification Checklist**

| Step | Action | Expected Result |
|------|---------|----------------|
| 1 | `docker compose up --build` | All services start successfully |
| 2 | Open `http://localhost:8000/admin` | Django Admin accessible |
| 3 | Open `http://localhost:8025` | MailHog available |
| 4 | Register via `/api/register/` | Activation email appears in MailHog |
| 5 | `docker compose exec web pytest -v` | All tests pass successfully |
