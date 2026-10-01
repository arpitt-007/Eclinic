from django.contrib import admin

from .models import Appointment, ContactMessage, Doctor, Patient, Prescription, Specialization


@admin.register(Specialization)
class SpecializationAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon')
    search_fields = ('name',)


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'specialization', 'experience_years', 'consultation_fee', 'is_available')
    list_filter = ('specialization', 'is_available')
    search_fields = ('user__first_name', 'user__last_name', 'user__username')


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'gender', 'blood_group', 'date_of_birth')
    search_fields = ('user__first_name', 'user__last_name', 'user__username')


class PrescriptionInline(admin.StackedInline):
    model = Prescription
    extra = 0


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'date', 'time', 'mode', 'status')
    list_filter = ('status', 'mode', 'date', 'doctor__specialization')
    search_fields = ('patient__user__first_name', 'doctor__user__first_name')
    date_hierarchy = 'date'
    inlines = [PrescriptionInline]


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('subject', 'name', 'email', 'created_at')
    readonly_fields = ('name', 'email', 'subject', 'message', 'created_at')
