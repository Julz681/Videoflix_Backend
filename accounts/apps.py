"""
Django application configuration for the 'accounts' app.

This module defines the configuration class for the accounts application.
It specifies the default primary key type for models and the internal 
application name used by Django for app registration and referencing.
"""

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """
    Configuration class for the 'accounts' Django application.

    This class defines metadata and default settings used by Django to 
    initialize and manage the 'accounts' app.
    """

    # Specifies the default auto field type for model primary keys
    default_auto_field = "django.db.models.BigAutoField"

    # Internal name of the Django app; must match the package name
    name = "accounts"
