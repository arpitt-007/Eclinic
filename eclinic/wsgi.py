"""
WSGI config for eclinic project.

It exposes the WSGI callable as a module-level variable named ``application``
(and ``app``, which is the name Vercel's Python runtime looks for).
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eclinic.settings')

application = get_wsgi_application()

if os.environ.get('VERCEL'):
    # Serverless instances start with an empty temp dir: create the SQLite
    # database and the code-defined accounts on every cold start.
    from django.conf import settings
    from django.core.management import call_command

    settings.RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    call_command('migrate', interactive=False, verbosity=0)
    call_command('seed_demo', verbosity=0)

app = application
