"""
Admin configuration for Moderation app.
Comprehensive admin interface using Django Jazzmin.
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import (
    CourseModeration,
    ModerationStatus,
    UserModeration,
    UserBanReason,
    ModerationLog,
    ActionType,
)


@admin.register(CourseModeration)
class CourseModerationAdmin(admin.ModelAdmin):
    """Course moderation admin with review workflow."""
    
    list_display = (
        'course_link',
        'status_badge',
        'reviewer_link',
        'quality_score_display',
        'checklist_display',
        'reviewed_at',
        'created_at',
    )
    
    list_filter = (
        'status',
        'content_complete',
        'video_quality_ok',
        'description_adequate',
        'pricing_appropriate',
        'created_at',
    )
    
    search_fields = (
        'course__title',
        'course__author__first_name',
        'course__author__last_name',
        'reviewer__first_name',
        'reviewer__last_name',
        'review_notes',
    )
    
    raw_id_fields = ('course', 'reviewer')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    
    list_per_page = 25
    
    fieldsets = (
        (_('Course'), {
            'fields': ('course', 'status')
        }),
        (_('Review'), {
            'fields': ('reviewer', 'review_notes', 'reviewed_at')
        }),
        (_('Rejection/Changes'), {
            'fields': ('rejection_reason', 'changes_requested'),
            'classes': ('collapse',),
        }),
        (_('Quality Checklist'), {
            'fields': (
                'quality_score',
                'content_complete',
                'video_quality_ok',
                'description_adequate',
                'pricing_appropriate'
            )
        }),
        (_('Dates'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    actions = ['approve_courses', 'reject_courses', 'request_changes']
    
    def course_link(self, obj):
        return format_html(
            '<a href="/admin/courses/course/{}/change/">{}</a>',
            obj.course.id,
            obj.course.title[:40] + '...' if len(obj.course.title) > 40 else obj.course.title
        )
    course_link.short_description = _('Course')
    course_link.admin_order_field = 'course__title'
    
    def reviewer_link(self, obj):
        if obj.reviewer:
            return format_html(
                '<a href="/admin/users/user/{}/change/">{}</a>',
                obj.reviewer.id,
                obj.reviewer.get_full_name() or obj.reviewer.phone_number
            )
        return format_html('<span class="badge badge-warning">{}</span>', 'Not Assigned')
    reviewer_link.short_description = _('Reviewer')
    
    def status_badge(self, obj):
        """Display status with colored badge."""
        colors = {
            ModerationStatus.PENDING: 'warning',
            ModerationStatus.IN_REVIEW: 'info',
            ModerationStatus.APPROVED: 'success',
            ModerationStatus.REJECTED: 'danger',
            ModerationStatus.CHANGES_REQUESTED: 'primary',
        }
        color = colors.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = _('Status')
    status_badge.admin_order_field = 'status'
    
    def quality_score_display(self, obj):
        if obj.quality_score is None:
            return '-'
        if obj.quality_score >= 80:
            color = 'success'
        elif obj.quality_score >= 60:
            color = 'info'
        elif obj.quality_score >= 40:
            color = 'warning'
        else:
            color = 'danger'
        return format_html(
            '<span class="badge badge-{}">{}/100</span>',
            color,
            obj.quality_score
        )
    quality_score_display.short_description = _('Quality')
    quality_score_display.admin_order_field = 'quality_score'
    
    def checklist_display(self, obj):
        """Display checklist status."""
        checks = [
            ('Content', obj.content_complete),
            ('Video', obj.video_quality_ok),
            ('Desc', obj.description_adequate),
            ('Price', obj.pricing_appropriate),
        ]
        result = []
        for name, status in checks:
            icon = '✓' if status else '✗'
            color = 'green' if status else 'red'
            result.append(f'<span style="color:{color}">{icon}</span>')
        return format_html(' '.join(result))
    checklist_display.short_description = _('Checklist')
    
    @admin.action(description=_('Approve selected courses'))
    def approve_courses(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(
            status=ModerationStatus.APPROVED,
            reviewer=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f'{updated} courses approved.')
    
    @admin.action(description=_('Reject selected courses'))
    def reject_courses(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(
            status=ModerationStatus.REJECTED,
            reviewer=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f'{updated} courses rejected.')
    
    @admin.action(description=_('Request changes for selected courses'))
    def request_changes(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(
            status=ModerationStatus.CHANGES_REQUESTED,
            reviewer=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f'{updated} courses marked as changes requested.')


@admin.register(UserModeration)
class UserModerationAdmin(admin.ModelAdmin):
    """User moderation admin for ban/warning management."""
    
    list_display = (
        'user_link',
        'action_badge',
        'reason_badge',
        'moderator_link',
        'is_permanent_display',
        'expires_at',
        'created_at',
    )
    
    list_filter = (
        'action',
        'reason',
        'is_permanent',
        'created_at',
    )
    
    search_fields = (
        'user__first_name',
        'user__last_name',
        'user__phone_number',
        'moderator__first_name',
        'moderator__last_name',
        'details',
    )
    
    raw_id_fields = ('user', 'moderator')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    
    list_per_page = 25
    
    fieldsets = (
        (_('User & Action'), {
            'fields': ('user', 'action', 'reason')
        }),
        (_('Details'), {
            'fields': ('details', 'evidence_urls')
        }),
        (_('Duration'), {
            'fields': ('is_permanent', 'expires_at')
        }),
        (_('Moderator'), {
            'fields': ('moderator', 'ip_address')
        }),
        (_('Dates'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def user_link(self, obj):
        return format_html(
            '<a href="/admin/users/user/{}/change/">{}</a>',
            obj.user.id,
            obj.user.get_full_name() or obj.user.phone_number
        )
    user_link.short_description = _('User')
    user_link.admin_order_field = 'user__first_name'
    
    def moderator_link(self, obj):
        if obj.moderator:
            return format_html(
                '<a href="/admin/users/user/{}/change/">{}</a>',
                obj.moderator.id,
                obj.moderator.get_full_name() or obj.moderator.phone_number
            )
        return '-'
    moderator_link.short_description = _('Moderator')
    
    def action_badge(self, obj):
        """Display action with colored badge."""
        colors = {
            'BAN': 'danger',
            'UNBAN': 'success',
            'WARNING': 'warning',
            'SUSPEND': 'info',
        }
        color = colors.get(obj.action, 'secondary')
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color,
            obj.get_action_display()
        )
    action_badge.short_description = _('Action')
    action_badge.admin_order_field = 'action'
    
    def reason_badge(self, obj):
        """Display reason with badge."""
        return format_html(
            '<span class="badge badge-secondary">{}</span>',
            obj.get_reason_display()
        )
    reason_badge.short_description = _('Reason')
    reason_badge.admin_order_field = 'reason'
    
    def is_permanent_display(self, obj):
        if obj.is_permanent:
            return format_html('<span class="badge badge-danger">{}</span>', 'Permanent')
        return format_html('<span class="badge badge-info">{}</span>', 'Temporary')
    is_permanent_display.short_description = _('Duration')
    is_permanent_display.admin_order_field = 'is_permanent'


@admin.register(ModerationLog)
class ModerationLogAdmin(admin.ModelAdmin):
    """Moderation audit log admin (read-only)."""
    
    list_display = (
        'admin_link',
        'action_type_badge',
        'description_preview',
        'affected_user_link',
        'affected_course_link',
        'created_at',
    )
    
    list_filter = ('action_type', 'created_at')
    
    search_fields = (
        'admin__first_name',
        'admin__last_name',
        'description',
        'affected_user__first_name',
        'affected_user__last_name',
        'affected_course__title',
    )
    
    date_hierarchy = 'created_at'
    
    list_per_page = 50
    
    # Make this read-only for audit purposes
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    fieldsets = (
        (_('Action'), {
            'fields': ('admin', 'action_type', 'description')
        }),
        (_('Affected Objects'), {
            'fields': ('affected_user', 'affected_course')
        }),
        (_('Technical Details'), {
            'fields': ('ip_address', 'user_agent', 'additional_data'),
            'classes': ('collapse',),
        }),
        (_('Timestamp'), {
            'fields': ('created_at',)
        }),
    )
    
    def admin_link(self, obj):
        if obj.admin:
            return format_html(
                '<a href="/admin/users/user/{}/change/">{}</a>',
                obj.admin.id,
                obj.admin.get_full_name() or obj.admin.phone_number
            )
        return 'System'
    admin_link.short_description = _('Admin')
    
    def action_type_badge(self, obj):
        """Display action type with colored badge."""
        colors = {
            ActionType.COURSE_APPROVED: 'success',
            ActionType.COURSE_REJECTED: 'danger',
            ActionType.USER_BANNED: 'danger',
            ActionType.USER_UNBANNED: 'success',
            ActionType.PAYOUT_APPROVED: 'success',
            ActionType.PAYOUT_REJECTED: 'danger',
            ActionType.REFUND_APPROVED: 'info',
            ActionType.REFUND_REJECTED: 'warning',
            ActionType.CONFIG_CHANGED: 'primary',
            ActionType.OTHER: 'secondary',
        }
        color = colors.get(obj.action_type, 'secondary')
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color,
            obj.get_action_type_display()
        )
    action_type_badge.short_description = _('Action Type')
    action_type_badge.admin_order_field = 'action_type'
    
    def description_preview(self, obj):
        if len(obj.description) > 60:
            return f"{obj.description[:60]}..."
        return obj.description
    description_preview.short_description = _('Description')
    
    def affected_user_link(self, obj):
        if obj.affected_user:
            return format_html(
                '<a href="/admin/users/user/{}/change/">{}</a>',
                obj.affected_user.id,
                obj.affected_user.get_full_name() or obj.affected_user.phone_number
            )
        return '-'
    affected_user_link.short_description = _('Affected User')
    
    def affected_course_link(self, obj):
        if obj.affected_course:
            return format_html(
                '<a href="/admin/courses/course/{}/change/">{}</a>',
                obj.affected_course.id,
                obj.affected_course.title[:30] + '...' if len(obj.affected_course.title) > 30 else obj.affected_course.title
            )
        return '-'
    affected_course_link.short_description = _('Affected Course')
