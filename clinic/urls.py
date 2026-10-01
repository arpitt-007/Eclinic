from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('doctors/', views.doctor_list, name='doctor_list'),
    path('doctors/<int:pk>/', views.doctor_detail, name='doctor_detail'),
    path('doctors/<int:pk>/book/', views.book_appointment, name='book_appointment'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('appointments/<int:pk>/', views.appointment_detail, name='appointment_detail'),
    path('appointments/<int:pk>/prescription/', views.write_prescription, name='write_prescription'),
    path(
        'appointments/<int:pk>/<str:action>/',
        views.appointment_action,
        name='appointment_action',
    ),
]
