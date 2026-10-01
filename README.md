# E-Clinic

An online clinic built with Django: patients find doctors, book video or in-clinic appointments, and receive digital prescriptions; doctors manage requests and write prescriptions from their dashboard.

## Features

- **Patients & doctors** — separate sign-up flows and role-based dashboards (custom `User` model with a `role`).
- **Doctor directory** — search by name, speciality or qualification; filter by speciality.
- **Slot booking** — slots are generated from each doctor's working hours and slot length; booked, past and double-booked slots are excluded (enforced by a DB constraint too).
- **Appointment workflow** — `pending → confirmed → completed`, plus patient cancellation and doctor rejection.
- **Video consults** — confirming a video appointment generates a Jitsi Meet link.
- **e-Prescriptions** — doctors write diagnosis, medicines and advice; patients can print/save as PDF.
- **Profiles** — patients keep health details (DOB, blood group, history); doctors set fees and availability.
- **Admin panel** at `/admin/` for all models, plus a contact form whose messages land in the admin.

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo      # optional demo data
python manage.py createsuperuser  # optional, for /admin/
python manage.py runserver
```

Open http://127.0.0.1:8000.

### Demo accounts (from `seed_demo`)

| Role    | Username                                                      | Password    |
|---------|---------------------------------------------------------------|-------------|
| Patient | `patient`                                                     | `demo12345` |
| Doctor  | `dr_sharma`, `dr_mehta`, `dr_iyer`, `dr_khan`, `dr_reddy`, `dr_bose` | `demo12345` |

## Tests

```bash
python manage.py test
```

## Project layout

```
eclinic/      settings & root URLs
accounts/     custom User, sign-up/login/profile
clinic/       Specialization, Doctor, Patient, Appointment, Prescription, ContactMessage
templates/    Bootstrap 5 templates
static/css/   site styles
```

## Production settings

Configure via environment variables: `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0`, `DJANGO_ALLOWED_HOSTS=example.com`. Run `python manage.py collectstatic` and serve `staticfiles/` and `media/` from your web server.

## Deploying to Vercel (no external database)

The app runs as a Vercel serverless Python function (`vercel.json` → `eclinic/wsgi.py`). There is no database server: on every cold start it creates a SQLite file in `/tmp` and loads the accounts defined in `clinic/management/commands/seed_demo.py`. Logins are kept in signed cookies, and WhiteNoise serves static files straight from the source folders.

1. Push this repo to GitHub and import it at https://vercel.com/new (Framework preset: **Other**), or run `vercel --prod` from this folder.
2. In **Project → Settings → Environment Variables** add:
   - `DJANGO_SECRET_KEY` — required, a long random string
   - `ADMIN_PASSWORD` — optional, password for the built-in `admin` account
3. Redeploy so the variables take effect.

To add or change accounts, edit the `DOCTORS` list (or the patient block) in `seed_demo.py` and push.

> Bookings, sign-ups and profile edits made on the live site are **temporary**: each serverless instance has its own copy of the data, which resets on every cold start and redeploy. Uploaded doctor photos are not kept either. Use a hosted database and file storage if you need data to persist.
