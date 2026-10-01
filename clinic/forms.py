import datetime

from django import forms
from django.utils import timezone

from .models import Appointment, ContactMessage, Prescription

MAX_BOOKING_DAYS_AHEAD = 60


class AppointmentForm(forms.ModelForm):
    time = forms.TypedChoiceField(
        coerce=lambda v: datetime.datetime.strptime(v, '%H:%M').time(),
        widget=forms.RadioSelect,
        label='Available slots',
    )

    class Meta:
        model = Appointment
        fields = ('date', 'time', 'mode', 'symptoms')
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'mode': forms.RadioSelect,
            'symptoms': forms.Textarea(
                attrs={'rows': 3, 'placeholder': 'Briefly describe your symptoms or reason for visit'}
            ),
        }

    def __init__(self, *args, doctor, date, **kwargs):
        super().__init__(*args, **kwargs)
        self.doctor = doctor
        today = timezone.localdate()
        self.fields['date'].widget.attrs.update(
            min=today.isoformat(),
            max=(today + datetime.timedelta(days=MAX_BOOKING_DAYS_AHEAD)).isoformat(),
        )
        self.fields['time'].choices = [
            (slot.strftime('%H:%M'), slot.strftime('%I:%M %p')) for slot in doctor.free_slots(date)
        ]

    def clean_date(self):
        date = self.cleaned_data['date']
        today = timezone.localdate()
        if date < today:
            raise forms.ValidationError('Please choose a date in the future.')
        if date > today + datetime.timedelta(days=MAX_BOOKING_DAYS_AHEAD):
            raise forms.ValidationError(f'Bookings open only {MAX_BOOKING_DAYS_AHEAD} days ahead.')
        return date

    def clean(self):
        cleaned = super().clean()
        date, time = cleaned.get('date'), cleaned.get('time')
        if date and time and time not in self.doctor.free_slots(date):
            self.add_error('time', 'That slot was just taken. Please pick another one.')
        return cleaned


class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ('diagnosis', 'medicines', 'advice', 'follow_up_date')
        widgets = {
            'diagnosis': forms.Textarea(attrs={'rows': 2}),
            'medicines': forms.Textarea(
                attrs={'rows': 5, 'placeholder': 'Paracetamol 500mg — 1-0-1 — 5 days\nCetirizine 10mg — 0-0-1 — 3 days'}
            ),
            'advice': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Rest, fluids, diet, tests…'}),
            'follow_up_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ('name', 'email', 'subject', 'message')
        widgets = {'message': forms.Textarea(attrs={'rows': 4})}
