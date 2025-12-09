"""
Admin configuration for Users app.
Comprehensive admin interface using Django Jazzmin.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import User, UserRole


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User admin with phone-based authentication."""
    
    list_display = (
        'phone_number', 
        'first_name', 
        'last_name', 
        'email', 
        'role_badge',
        'is_active', 
        'is_staff',
        'date_joined',
    )
    
    list_filter = (
        'role', 
        'is_active', 
        'is_staff', 
        'is_superuser',
        'date_joined',
    )
    
    search_fields = (
        'phone_number', 
        'first_name', 
        'last_name', 
        'email',
    )
    
    ordering = ('-date_joined',)
    
    readonly_fields = ('date_joined', 'last_login', 'created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('phone_number', 'password')
        }),
        (_('Personal Info'), {
            'fields': ('first_name', 'last_name', 'email')
        }),
        (_('Role & Permissions'), {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',),
        }),
        (_('Social Auth'), {
            'fields': ('google_id', 'telegram_id'),
            'classes': ('collapse',),
        }),
        (_('Important Dates'), {
            'fields': ('last_login', 'date_joined', 'created_at', 'updated_at'),
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone_number', 'password1', 'password2', 'role'),
        }),
        (_('Personal Info'), {
            'fields': ('first_name', 'last_name', 'email'),
        }),
    )
    
    list_per_page = 25
    
    actions = ['activate_users', 'deactivate_users', 'make_author', 'make_student']
    
    def role_badge(self, obj):
        """Display role with colored badge."""
        colors = {
            UserRole.ADMIN: 'danger',
            UserRole.AUTHOR: 'primary',
            UserRole.STUDENT: 'success',
        }
        color = colors.get(obj.role, 'secondary')
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color,
            obj.get_role_display()
        )
    role_badge.short_description = _('Role')
    role_badge.admin_order_field = 'role'
    
    @admin.action(description=_('Activate selected users'))
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} users activated.')
    
    @admin.action(description=_('Deactivate selected users'))
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} users deactivated.')
    
    @admin.action(description=_('Change role to Author'))
    def make_author(self, request, queryset):
        updated = queryset.update(role=UserRole.AUTHOR)
        self.message_user(request, f'{updated} users changed to Author role.')
    
    @admin.action(description=_('Change role to Student'))
    def make_student(self, request, queryset):
        updated = queryset.update(role=UserRole.STUDENT)
        self.message_user(request, f'{updated} users changed to Student role.')
