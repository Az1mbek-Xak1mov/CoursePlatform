"""
URL configuration for courses app.
"""
from django.urls import path
from . import views

urlpatterns = [
    # Student-facing course pages
    path('', views.course_list_view, name='course_list'),
    path('browse/', views.course_list_view, name='course_browse'),
    path('detail/<slug:slug>/', views.course_detail_view, name='course_detail'),
    path('learn/<slug:slug>/', views.course_learn_view, name='course_learn'),
    path('learn/<slug:slug>/lesson/<int:lesson_id>/', views.course_learn_view, name='course_lesson'),
    path('enroll/<slug:slug>/', views.enroll_course_view, name='course_enroll'),
    
    # Course creation and editing (Author)
    path('create/', views.create_course_view, name='course_create'),
    path('<int:course_id>/edit/', views.edit_course_view, name='course_edit'),
    path('<int:course_id>/builder/', views.course_builder_view, name='course_builder'),
    path('<int:course_id>/publish/', views.publish_course_view, name='course_publish'),
    
    # Module management (AJAX)
    path('<int:course_id>/modules/add/', views.add_module_view, name='add_module'),
    path('modules/<int:module_id>/edit/', views.edit_module_view, name='edit_module'),
    path('modules/<int:module_id>/delete/', views.delete_module_view, name='delete_module'),
    
    # Lesson management (AJAX)
    path('modules/<int:module_id>/lessons/add/', views.add_lesson_view, name='add_lesson'),
    path('lessons/<int:lesson_id>/edit/', views.edit_lesson_view, name='edit_lesson'),
    path('lessons/<int:lesson_id>/delete/', views.delete_lesson_view, name='delete_lesson'),
    
    # AJAX endpoints for lesson progress
    path('api/lesson/<int:lesson_id>/progress/', views.update_lesson_progress, name='update_lesson_progress'),
    path('api/lesson/<int:lesson_id>/complete/', views.mark_lesson_complete, name='mark_lesson_complete'),
]
