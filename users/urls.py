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
    path('become-instructor/', views.switch_to_instructor_view, name='become_instructor'),
    
    # Registration URLs
    path('register/', views.register_choice_view, name='register_choice'),
    path('register/phone/', views.register_phone_view, name='register_phone'),
    path('register/verify-otp/', views.register_verify_otp_view, name='register_verify_otp'),
    path('register/details/', views.register_details_view, name='register_details'),
    path('register/email/', views.register_email_view, name='register_email'),
    
    # Phone login URLs
    path('login/phone/', views.login_phone_view, name='login_phone'),
    path('login/verify-otp/', views.login_verify_otp_view, name='login_verify_otp'),
    
    # Profile URLs
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
]
