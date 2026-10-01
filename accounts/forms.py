from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction

from clinic.models import Doctor, Patient, Specialization

from .models import User


class BaseSignupForm(UserCreationForm):
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    email = forms.EmailField()
    phone = forms.CharField(max_length=20, required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'phone')


class PatientSignupForm(BaseSignupForm):
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    gender = forms.ChoiceField(choices=[('', '---------')] + Patient.Gender.choices, required=False)

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.PATIENT
        user.save()
        Patient.objects.create(
            user=user,
            date_of_birth=self.cleaned_data.get('date_of_birth'),
            gender=self.cleaned_data.get('gender', ''),
        )
        return user


class DoctorSignupForm(BaseSignupForm):
    specialization = forms.ModelChoiceField(queryset=Specialization.objects.all())
    qualification = forms.CharField(max_length=200)
    experience_years = forms.IntegerField(min_value=0, label='Years of experience')
    consultation_fee = forms.DecimalField(min_value=0, decimal_places=2, initial=500)

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.DOCTOR
        user.save()
        Doctor.objects.create(
            user=user,
            specialization=self.cleaned_data['specialization'],
            qualification=self.cleaned_data['qualification'],
            experience_years=self.cleaned_data['experience_years'],
            consultation_fee=self.cleaned_data['consultation_fee'],
        )
        return user


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone')


class PatientProfileForm(forms.ModelForm):
    class Meta:
        model = Patient
        exclude = ('user',)
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'address': forms.Textarea(attrs={'rows': 2}),
            'medical_history': forms.Textarea(attrs={'rows': 3}),
        }


class DoctorProfileForm(forms.ModelForm):
    class Meta:
        model = Doctor
        exclude = ('user',)
        widgets = {
            'available_from': forms.TimeInput(attrs={'type': 'time'}, format='%H:%M'),
            'available_to': forms.TimeInput(attrs={'type': 'time'}, format='%H:%M'),
            'bio': forms.Textarea(attrs={'rows': 3}),
        }

    def clean(self):
        cleaned = super().clean()
        start, end = cleaned.get('available_from'), cleaned.get('available_to')
        if start and end and start >= end:
            raise forms.ValidationError('"Available to" must be later than "Available from".')
        return cleaned
