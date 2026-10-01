import datetime
import uuid
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import AppointmentForm, ContactForm, PrescriptionForm
from .models import Appointment, Doctor, Patient, Specialization


def role_required(role):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.user.role != role:
                raise PermissionDenied
            return view(request, *args, **kwargs)
        return wrapper
    return decorator


# ---------------------------------------------------------------- public pages

def home(request):
    context = {
        'specializations': Specialization.objects.annotate(n=Count('doctors')),
        'doctors': Doctor.objects.filter(is_available=True).select_related('user', 'specialization')[:4],
        'stats': {
            'doctors': Doctor.objects.count(),
            'patients': Patient.objects.count(),
            'consultations': Appointment.objects.filter(status=Appointment.Status.COMPLETED).count(),
            'specialities': Specialization.objects.count(),
        },
    }
    return render(request, 'clinic/home.html', context)


def doctor_list(request):
    doctors = Doctor.objects.filter(is_available=True).select_related('user', 'specialization')
    q = request.GET.get('q', '').strip()
    spec = request.GET.get('specialization', '')
    if q:
        doctors = doctors.filter(
            Q(user__first_name__icontains=q)
            | Q(user__last_name__icontains=q)
            | Q(specialization__name__icontains=q)
            | Q(qualification__icontains=q)
        )
    if spec:
        doctors = doctors.filter(specialization_id=spec)
    return render(request, 'clinic/doctor_list.html', {
        'doctors': doctors,
        'specializations': Specialization.objects.all(),
        'q': q,
        'selected_spec': spec,
    })


def doctor_detail(request, pk):
    doctor = get_object_or_404(Doctor.objects.select_related('user', 'specialization'), pk=pk)
    return render(request, 'clinic/doctor_detail.html', {'doctor': doctor})


def about(request):
    return render(request, 'clinic/about.html')


def contact(request):
    form = ContactForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Thanks for reaching out! Our team will get back to you shortly.')
        return redirect('contact')
    return render(request, 'clinic/contact.html', {'form': form})


# ------------------------------------------------------------------- booking

@role_required('patient')
def book_appointment(request, pk):
    doctor = get_object_or_404(Doctor.objects.select_related('user', 'specialization'), pk=pk, is_available=True)
    today = timezone.localdate()
    raw_date = request.POST.get('date') or request.GET.get('date')
    try:
        date = datetime.date.fromisoformat(raw_date) if raw_date else today
    except ValueError:
        date = today
    date = max(date, today)
    if not raw_date:
        # Default to the first upcoming day that still has free slots.
        for _ in range(14):
            if doctor.free_slots(date):
                break
            date += datetime.timedelta(days=1)

    if request.method == 'POST':
        form = AppointmentForm(request.POST, doctor=doctor, date=date)
        if form.is_valid():
            appt = form.save(commit=False)
            appt.doctor = doctor
            appt.patient = request.user.patient_profile
            try:
                appt.save()
            except IntegrityError:
                form.add_error('time', 'That slot was just taken. Please pick another one.')
            else:
                messages.success(request, f'Appointment requested with {doctor} on {appt.date:%d %b %Y} at {appt.time:%I:%M %p}.')
                return redirect(appt)
    else:
        form = AppointmentForm(doctor=doctor, date=date, initial={'date': date, 'mode': Appointment.Mode.VIDEO})
    return render(request, 'clinic/book_appointment.html', {'doctor': doctor, 'form': form, 'date': date})


# ----------------------------------------------------------------- dashboard

@login_required
def dashboard(request):
    user = request.user
    if user.is_superuser and not hasattr(user, 'doctor_profile') and not hasattr(user, 'patient_profile'):
        return redirect('admin:index')

    today = timezone.localdate()
    if user.is_doctor:
        appts = Appointment.objects.filter(doctor=user.doctor_profile).select_related('patient__user')
        template = 'clinic/dashboard_doctor.html'
    else:
        appts = Appointment.objects.filter(patient=user.patient_profile).select_related(
            'doctor__user', 'doctor__specialization'
        )
        template = 'clinic/dashboard_patient.html'

    active = [Appointment.Status.PENDING, Appointment.Status.CONFIRMED]
    upcoming = appts.filter(date__gte=today, status__in=active).order_by('date', 'time')
    past = appts.exclude(pk__in=upcoming.values('pk')).order_by('-date', '-time')
    context = {
        'upcoming': upcoming,
        'past': past[:20],
        'today_appts': appts.filter(date=today, status__in=active).order_by('time'),
        'counts': {
            'total': appts.count(),
            'pending': appts.filter(status=Appointment.Status.PENDING).count(),
            'upcoming': upcoming.count(),
            'completed': appts.filter(status=Appointment.Status.COMPLETED).count(),
        },
    }
    return render(request, template, context)


def _get_appointment_for(user, pk):
    appt = get_object_or_404(
        Appointment.objects.select_related('doctor__user', 'doctor__specialization', 'patient__user'), pk=pk
    )
    if user.is_staff or appt.doctor.user_id == user.id or appt.patient.user_id == user.id:
        return appt
    raise PermissionDenied


@login_required
def appointment_detail(request, pk):
    appt = _get_appointment_for(request.user, pk)
    prescription = getattr(appt, 'prescription', None)
    return render(request, 'clinic/appointment_detail.html', {'appt': appt, 'prescription': prescription})


@require_POST
@login_required
def appointment_action(request, pk, action):
    appt = _get_appointment_for(request.user, pk)
    user = request.user
    S = Appointment.Status

    allowed = {
        # action: (who may do it, statuses it's valid from, new status)
        'cancel': (appt.patient.user_id == user.id, [S.PENDING, S.CONFIRMED], S.CANCELLED),
        'confirm': (appt.doctor.user_id == user.id, [S.PENDING], S.CONFIRMED),
        'reject': (appt.doctor.user_id == user.id, [S.PENDING], S.REJECTED),
    }
    if action not in allowed:
        raise PermissionDenied
    permitted, from_statuses, new_status = allowed[action]
    if not permitted:
        raise PermissionDenied
    if appt.status not in from_statuses:
        messages.error(request, f'This appointment is already {appt.get_status_display().lower()}.')
        return redirect(appt)

    appt.status = new_status
    if new_status == S.CONFIRMED and appt.mode == Appointment.Mode.VIDEO and not appt.meeting_link:
        appt.meeting_link = f'https://meet.jit.si/eclinic-{uuid.uuid4().hex[:12]}'
    appt.save()
    messages.success(request, f'Appointment {appt.get_status_display().lower()}.')
    next_url = request.POST.get('next')
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
    return redirect(appt)


@role_required('doctor')
def write_prescription(request, pk):
    appt = _get_appointment_for(request.user, pk)
    if appt.doctor.user_id != request.user.id:
        raise PermissionDenied
    if appt.status not in (Appointment.Status.CONFIRMED, Appointment.Status.COMPLETED):
        messages.error(request, 'Only confirmed appointments can receive a prescription.')
        return redirect(appt)

    instance = getattr(appt, 'prescription', None)
    form = PrescriptionForm(request.POST or None, instance=instance)
    if request.method == 'POST' and form.is_valid():
        rx = form.save(commit=False)
        rx.appointment = appt
        rx.save()
        appt.status = Appointment.Status.COMPLETED
        appt.save(update_fields=['status'])
        messages.success(request, 'Prescription saved and consultation marked as completed.')
        return redirect(appt)
    return render(request, 'clinic/prescription_form.html', {'appt': appt, 'form': form})
