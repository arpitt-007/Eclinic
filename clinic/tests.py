import datetime

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User

from .models import Appointment, Doctor, Patient, Specialization


class ClinicFlowTests(TestCase):
    def setUp(self):
        spec = Specialization.objects.create(name='General Physician')
        doc_user = User.objects.create_user('doc', password='pw12345!x', role=User.Role.DOCTOR, first_name='Ana')
        self.doctor = Doctor.objects.create(user=doc_user, specialization=spec, qualification='MBBS')
        pat_user = User.objects.create_user('pat', password='pw12345!x', role=User.Role.PATIENT)
        self.patient = Patient.objects.create(user=pat_user)
        self.tomorrow = timezone.localdate() + datetime.timedelta(days=1)

    def book(self, time='10:00'):
        return self.client.post(
            reverse('book_appointment', args=[self.doctor.pk]),
            {'date': self.tomorrow.isoformat(), 'time': time, 'mode': 'video', 'symptoms': 'Headache'},
        )

    def test_public_pages_load(self):
        for name in ('home', 'doctor_list', 'about', 'contact', 'login', 'signup', 'signup_doctor'):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)
        self.assertEqual(self.client.get(reverse('doctor_detail', args=[self.doctor.pk])).status_code, 200)

    def test_patient_signup_creates_profile(self):
        resp = self.client.post(reverse('signup'), {
            'username': 'newbie', 'first_name': 'New', 'last_name': 'Bie', 'email': 'n@example.com',
            'password1': 'Str0ng-pass-123', 'password2': 'Str0ng-pass-123',
        })
        self.assertRedirects(resp, reverse('dashboard'))
        self.assertTrue(Patient.objects.filter(user__username='newbie').exists())

    def test_booking_and_double_booking(self):
        self.client.login(username='pat', password='pw12345!x')
        resp = self.book()
        appt = Appointment.objects.get()
        self.assertRedirects(resp, appt.get_absolute_url())
        self.assertNotIn(datetime.time(10, 0), self.doctor.free_slots(self.tomorrow))

        resp = self.book()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Appointment.objects.count(), 1)

    def test_doctor_cannot_book(self):
        self.client.login(username='doc', password='pw12345!x')
        self.assertEqual(self.book().status_code, 403)

    def test_confirm_prescribe_flow(self):
        self.client.login(username='pat', password='pw12345!x')
        self.book()
        appt = Appointment.objects.get()

        self.client.login(username='doc', password='pw12345!x')
        self.client.post(reverse('appointment_action', args=[appt.pk, 'confirm']))
        appt.refresh_from_db()
        self.assertEqual(appt.status, Appointment.Status.CONFIRMED)
        self.assertTrue(appt.meeting_link.startswith('https://meet.jit.si/'))

        self.client.post(reverse('write_prescription', args=[appt.pk]), {
            'diagnosis': 'Tension headache', 'medicines': 'Paracetamol 500mg', 'advice': '',
        })
        appt.refresh_from_db()
        self.assertEqual(appt.status, Appointment.Status.COMPLETED)
        self.assertEqual(appt.prescription.diagnosis, 'Tension headache')

    def test_patient_cannot_confirm_and_strangers_cannot_view(self):
        self.client.login(username='pat', password='pw12345!x')
        self.book()
        appt = Appointment.objects.get()
        resp = self.client.post(reverse('appointment_action', args=[appt.pk, 'confirm']))
        self.assertEqual(resp.status_code, 403)

        User.objects.create_user('other', password='pw12345!x')
        self.client.login(username='other', password='pw12345!x')
        self.assertEqual(self.client.get(appt.get_absolute_url()).status_code, 403)

    def test_cancel_frees_slot(self):
        self.client.login(username='pat', password='pw12345!x')
        self.book()
        appt = Appointment.objects.get()
        self.client.post(reverse('appointment_action', args=[appt.pk, 'cancel']))
        appt.refresh_from_db()
        self.assertEqual(appt.status, Appointment.Status.CANCELLED)
        self.assertIn(datetime.time(10, 0), self.doctor.free_slots(self.tomorrow))
        # The freed slot can be booked again despite the unique constraint.
        self.book()
        self.assertEqual(Appointment.objects.filter(status='pending').count(), 1)
