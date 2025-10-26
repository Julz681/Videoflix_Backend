#!/usr/bin/env python
"""
Django's command-line utility for administrative tasks.

This script serves as the main entry point for Django management commands.
It ensures that the correct settings module is loaded and then delegates
execution to Django's internal command system (e.g., runserver, migrate, shell).
"""

import os
import sys


def main():
    """
    Run administrative tasks.

    This function sets the default settings module for Django,
    imports Django's management command executor, and executes
    any command-line arguments passed to the script.
    """
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Make sure it's installed and available "
            "on your PYTHONPATH environment variable. "
            "Did you forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
