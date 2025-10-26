#!/bin/sh
set -e
# Exit immediately if a command exits with a non-zero status.

echo "Waiting for PostgreSQL at $DB_HOST:$DB_PORT..."
# Wait until PostgreSQL is reachable using pg_isready
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" >/dev/null 2>&1; do
    echo "PostgreSQL not ready yet - sleeping for 1 second"
    sleep 1
done
echo "PostgreSQL is ready - continuing..."
echo ""

# =====================================================
# Main role dispatcher: WEB vs WORKER container
# =====================================================
if [ "$ROLE" = "web" ]; then
    echo "== WEB ROLE: executing setup steps =="

    # -------------------------------------------------
    # Collect all static files into STATIC_ROOT
    # -------------------------------------------------
    python manage.py collectstatic --noinput

    # -------------------------------------------------
    # Generate migrations for local apps if needed
    # (ignore errors if already exist)
    # -------------------------------------------------
    python manage.py makemigrations accounts --noinput || true
    python manage.py makemigrations videos --noinput || true

    # -------------------------------------------------
    # Apply all migrations to the database
    # -------------------------------------------------
    python manage.py migrate --noinput

    # -------------------------------------------------
    # Ensure a Django superuser exists (for admin login)
    # -------------------------------------------------
    echo "Checking if superuser exists..."
    python manage.py shell << 'EOF'
import os
from django.contrib.auth import get_user_model
User = get_user_model()

email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "admin@example.com")
password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "adminpassword")

if not User.objects.filter(email=email).exists():
    print(f"Creating superuser {email}")
    User.objects.create_superuser(
        email=email,
        password=password,
        is_active=True,
    )
else:
    print(f"Superuser {email} already exists.")
EOF
    echo ""

    # -------------------------------------------------
    # Start Django development server
    # -------------------------------------------------
    echo "Starting Django Development Server on 0.0.0.0:8000 ..."
    exec python manage.py runserver 0.0.0.0:8000

else
    # =================================================
    # Worker container (RQ task queue)
    # =================================================
    echo "== WORKER ROLE: starting rqworker =="

    # No migrations or static collection here.
    # Start the Redis Queue worker directly.
    exec python manage.py rqworker default
fi
