#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eclinic.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    if sys.argv[1:2] == ['runserver']:
        ensure_database()
    execute_from_command_line(sys.argv)


def ensure_database():
    """On a fresh checkout (db.sqlite3 is not in git), create the tables and
    the demo accounts before the server starts, instead of failing with
    "no such table"."""
    import django
    from django.conf import settings
    from django.core.management import call_command

    django.setup()
    db_path = settings.DATABASES['default']['NAME']
    if not os.path.exists(db_path):
        print('No database found: creating it and loading demo accounts...')
        call_command('migrate', interactive=False, verbosity=0)
        call_command('seed_demo')


if __name__ == '__main__':
    main()
