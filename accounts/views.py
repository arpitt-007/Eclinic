from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import (
    DoctorProfileForm,
    DoctorSignupForm,
    PatientProfileForm,
    PatientSignupForm,
    UserUpdateForm,
)


def signup(request, role='patient'):
    form_class = DoctorSignupForm if role == 'doctor' else PatientSignupForm
    form = form_class(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, f'Welcome to E-Clinic, {user.first_name}!')
        return redirect('dashboard')
    return render(request, 'accounts/signup.html', {'form': form, 'role': role})


@login_required
def profile(request):
    user = request.user
    if user.is_doctor:
        extra_instance, extra_class = user.doctor_profile, DoctorProfileForm
    else:
        extra_instance, extra_class = user.patient_profile, PatientProfileForm

    user_form = UserUpdateForm(request.POST or None, instance=user)
    extra_form = extra_class(request.POST or None, request.FILES or None, instance=extra_instance)
    if request.method == 'POST' and user_form.is_valid() and extra_form.is_valid():
        user_form.save()
        extra_form.save()
        messages.success(request, 'Profile updated.')
        return redirect('profile')
    return render(request, 'accounts/profile.html', {'user_form': user_form, 'extra_form': extra_form})
