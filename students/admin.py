"""
Admin configuration for Students app.
Comprehensive admin interface using Django Jazzmin.
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import (
    StudentProfile,
    WatchHistory,
    Certificate,
)


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    """Student profile admin with detailed student management."""
    
    list_display = (
        'user_display',
        'enrolled_courses_count',
        'completed_courses_count',
        'total_watch_time_display',
        'certificates_earned',
        'created_at',
    )
    
    list_filter = ('created_at',)
    
    search_fields = (
        'user__first_name',
        'user__last_name',
        'user__phone_number',
        'user__email',
    )
    
    raw_id_fields = ('user',)
    filter_horizontal = ('interested_categories',)
    readonly_fields = (
        'enrolled_courses_count',
        'completed_courses_count',
        'total_watch_time_hours',
        'certificates_earned',
        'created_at',
        'updated_at',
    )
    
    list_per_page = 25
    
    fieldsets = (
        (_('User Information'), {
            'fields': ('user',)
        }),
        (_('Profile'), {
            'fields': ('profile_picture', 'bio')
        }),
        (_('Preferences'), {
            'fields': ('interested_categories',),
        }),
        (_('Statistics'), {
            'fields': (
                'enrolled_courses_count',
                'completed_courses_count',
                'total_watch_time_hours',
                'certificates_earned'
            ),
            'classes': ('collapse',),
        }),
        (_('Dates'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def user_display(self, obj):
        """Display user with link."""
        return format_html(
            '<a href="/admin/users/user/{}/change/">{}</a>',
            obj.user.id,
            obj.user.get_full_name() or obj.user.phone_number
        )
    user_display.short_description = _('Student')
    user_display.admin_order_field = 'user__first_name'
    
    def total_watch_time_display(self, obj):
        """Display watch time in human readable format."""
        hours = obj.total_watch_time_hours
        if hours >= 24:
            days = hours // 24
            remaining_hours = hours % 24
            return f"{days}d {remaining_hours}h"
        return f"{hours}h"
    total_watch_time_display.short_description = _('Watch Time')
    total_watch_time_display.admin_order_field = 'total_watch_time_hours'


@admin.register(WatchHistory)
class WatchHistoryAdmin(admin.ModelAdmin):
    """Watch history admin for analytics."""
    
    list_display = (
        'student_display',
        'course',
        'lesson',
        'watch_duration_display',
        'percentage_watched',
        'device_type',
        'created_at',
    )
    
    list_filter = ('device_type', 'created_at')
    
    search_fields = (
        'student__first_name',
        'student__last_name',
        'course__title',
        'lesson__title',
    )
    
    raw_id_fields = ('student', 'course', 'lesson')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    
    list_per_page = 50
    
    def student_display(self, obj):
        return format_html(
            '<a href="/admin/users/user/{}/change/">{}</a>',
            obj.student.id,
            obj.student.get_full_name() or obj.student.phone_number
        )
    student_display.short_description = _('Student')
    
    def watch_duration_display(self, obj):
        """Display duration in human readable format."""
        seconds = obj.watch_duration_seconds
        if seconds >= 3600:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"
        elif seconds >= 60:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}m {secs}s"
        return f"{seconds}s"
    watch_duration_display.short_description = _('Duration')


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    """Certificate admin for managing course completion certificates."""
    
    list_display = (
        'certificate_id',
        'student_display',
        'course',
        'issued_at',
        'verification_url',
    )
    
    list_filter = ('issued_at', 'course')
    
    search_fields = (
        'certificate_id',
        'student__first_name',
        'student__last_name',
        'student__phone_number',
        'course__title',
    )
    
    raw_id_fields = ('student', 'course', 'enrollment')
    readonly_fields = ('certificate_id', 'issued_at', 'created_at', 'updated_at')
    
    list_per_page = 30
    
    fieldsets = (
        (_('Certificate Info'), {
            'fields': ('certificate_id', 'student', 'course', 'enrollment')
        }),
        (_('Files'), {
            'fields': ('certificate_file', 'verification_url'),
        }),
        (_('Dates'), {
            'fields': ('issued_at', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def student_display(self, obj):
        return format_html(
            '<a href="/admin/users/user/{}/change/">{}</a>',
            obj.student.id,
            obj.student.get_full_name() or obj.student.phone_number
        )
    student_display.short_description = _('Student')
