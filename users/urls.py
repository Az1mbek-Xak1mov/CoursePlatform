"""
URL configuration for users app.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_view, name='landing'),
    path('select-role/<str:role>/', views.select_role_view, name='select_role'),
    path('student/', views.student_dashboard_view, name='student_home'),
    path('author/', views.author_dashboard_view, name='author_home'),
    path('admin/dashboard/', views.admin_dashboard_view, name='admin_home'),
]
