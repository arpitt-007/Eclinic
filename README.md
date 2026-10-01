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

## Deploying to Render (no external database)

`render.yaml` deploys a single free web service. There is no database server: on every start the app creates a fresh SQLite file and loads the accounts defined in `clinic/management/commands/seed_demo.py`.

1. Push this repo to GitHub.
2. In Render: **New → Blueprint** → pick the repo → **Apply**.
3. The admin username is `admin`; its password is the generated `ADMIN_PASSWORD` under the service's **Environment** tab.

To add or change accounts, edit the `DOCTORS` list (or the patient block) in `seed_demo.py` and push.

> Bookings, sign-ups and profile edits made on the live site are **lost whenever the server restarts** (each deploy, and after ~15 min of inactivity on the free plan). Use a real database if you need data to persist.
