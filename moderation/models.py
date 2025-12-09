"""
Moderation models for IlmSpace platform.
Handles course approval, user moderation, and audit logging.
"""
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from users.base import BaseModel


class ModerationStatus(models.TextChoices):
    """Status choices for moderation."""
    PENDING = 'PENDING', _('Pending Review')
    IN_REVIEW = 'IN_REVIEW', _('In Review')
    APPROVED = 'APPROVED', _('Approved')
    REJECTED = 'REJECTED', _('Rejected')
    CHANGES_REQUESTED = 'CHANGES_REQUESTED', _('Changes Requested')


class CourseModeration(BaseModel):
    """
    Course moderation and approval workflow.
    Follows SRP - manages course approval process only.
    """
    
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        related_name='moderation_history',
        verbose_name=_('course')
    )
    
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=ModerationStatus.choices,
        default=ModerationStatus.PENDING,
        help_text=_('Moderation status')
    )
    
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='moderation_course_reviews',
        verbose_name=_('reviewer'),
        limit_choices_to={'role': 'ADMIN'}
    )
    
    review_notes = models.TextField(
        _('review notes'),
        blank=True,
        help_text=_('Reviewer notes and feedback to author')
    )
    
    rejection_reason = models.TextField(
        _('rejection reason'),
        blank=True,
        help_text=_('Specific reason for rejection')
    )
    
    changes_requested = models.TextField(
        _('changes requested'),
        blank=True,
        help_text=_('Specific changes author needs to make')
    )
    
    reviewed_at = models.DateTimeField(
        _('reviewed at'),
        null=True,
        blank=True,
        help_text=_('When the review was completed')
    )
    
    # Quality checklist (optional but recommended)
    quality_score = models.PositiveSmallIntegerField(
        _('quality score'),
        null=True,
        blank=True,
        help_text=_('Quality score out of 100')
    )
    
    content_complete = models.BooleanField(
        _('content complete'),
        default=False,
        help_text=_('Course has all required content')
    )
    
    video_quality_ok = models.BooleanField(
        _('video quality OK'),
        default=False,
        help_text=_('Video quality meets standards')
    )
    
    description_adequate = models.BooleanField(
        _('description adequate'),
        default=False,
        help_text=_('Course description is clear and complete')
    )
    
    pricing_appropriate = models.BooleanField(
        _('pricing appropriate'),
        default=False,
        help_text=_('Course pricing is reasonable for content')
    )
    
    class Meta:
        verbose_name = _('course moderation')
        verbose_name_plural = _('course moderations')
        db_table = 'course_moderations'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['course', '-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['reviewer']),
        ]
    
    def __str__(self):
        return f"{self.course.title} - {self.status}"


class UserBanReason(models.TextChoices):
    """Reasons for user ban."""
    SPAM = 'SPAM', _('Spam/Advertising')
    HARASSMENT = 'HARASSMENT', _('Harassment')
    FRAUD = 'FRAUD', _('Fraudulent Activity')
    VIOLATION = 'VIOLATION', _('Terms Violation')
    COPYRIGHT = 'COPYRIGHT', _('Copyright Infringement')
    OTHER = 'OTHER', _('Other')


class UserModeration(BaseModel):
    """
    User ban/unban and moderation actions.
    Follows SRP - manages user access control.
    """
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='moderation_history',
        verbose_name=_('user')
    )
    
    action = models.CharField(
        _('action'),
        max_length=20,
        choices=[
            ('BAN', _('Ban')),
            ('UNBAN', _('Unban')),
            ('WARNING', _('Warning')),
            ('SUSPEND', _('Suspend')),
        ],
        help_text=_('Moderation action taken')
    )
    
    reason = models.CharField(
        _('reason'),
        max_length=20,
        choices=UserBanReason.choices,
        help_text=_('Reason for action')
    )
    
    details = models.TextField(
        _('details'),
        help_text=_('Detailed explanation of the action')
    )
    
    moderator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='moderation_actions',
        verbose_name=_('moderator'),
        limit_choices_to={'role': 'ADMIN'}
    )
    
    # Duration for temporary bans/suspensions
    is_permanent = models.BooleanField(
        _('permanent'),
        default=False,
        help_text=_('Whether action is permanent')
    )
    
    expires_at = models.DateTimeField(
        _('expires at'),
        null=True,
        blank=True,
        help_text=_('When temporary action expires (null if permanent)')
    )
    
    # Internal tracking
    ip_address = models.GenericIPAddressField(
        _('IP address'),
        null=True,
        blank=True,
        help_text=_('IP address when action was taken')
    )
    
    evidence_urls = models.JSONField(
        _('evidence URLs'),
        default=list,
        blank=True,
        help_text=_('Evidence/screenshots supporting the action')
    )
    
    class Meta:
        verbose_name = _('user moderation')
        verbose_name_plural = _('user moderations')
        db_table = 'user_moderations'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['action']),
            models.Index(fields=['moderator']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"{self.action} - {self.user.get_full_name()}"


class ActionType(models.TextChoices):
    """Types of admin actions to log."""
    COURSE_APPROVED = 'COURSE_APPROVED', _('Course Approved')
    COURSE_REJECTED = 'COURSE_REJECTED', _('Course Rejected')
    USER_BANNED = 'USER_BANNED', _('User Banned')
    USER_UNBANNED = 'USER_UNBANNED', _('User Unbanned')
    PAYOUT_APPROVED = 'PAYOUT_APPROVED', _('Payout Approved')
    PAYOUT_REJECTED = 'PAYOUT_REJECTED', _('Payout Rejected')
    REFUND_APPROVED = 'REFUND_APPROVED', _('Refund Approved')
    REFUND_REJECTED = 'REFUND_REJECTED', _('Refund Rejected')
    CONFIG_CHANGED = 'CONFIG_CHANGED', _('Configuration Changed')
    OTHER = 'OTHER', _('Other')


class ModerationLog(BaseModel):
    """
    Comprehensive audit log for all admin/moderation actions.
    Follows SRP - logging and auditability only.
    """
    
    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='admin_logs',
        verbose_name=_('admin'),
        limit_choices_to={'role': 'ADMIN'}
    )
    
    action_type = models.CharField(
        _('action type'),
        max_length=30,
        choices=ActionType.choices,
        help_text=_('Type of action performed')
    )
    
    description = models.TextField(
        _('description'),
        help_text=_('Description of what was done')
    )
    
    # Related objects (generic approach)
    affected_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='affected_in_logs',
        verbose_name=_('affected user'),
        help_text=_('User affected by this action')
    )
    
    affected_course = models.ForeignKey(
        'courses.Course',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='moderation_logs',
        verbose_name=_('affected course')
    )
    
    # Metadata
    ip_address = models.GenericIPAddressField(
        _('IP address'),
        null=True,
        blank=True,
        help_text=_('IP address of admin')
    )
    
    user_agent = models.CharField(
        _('user agent'),
        max_length=500,
        blank=True,
        help_text=_('Browser/client user agent')
    )
    
    additional_data = models.JSONField(
        _('additional data'),
        default=dict,
        blank=True,
        help_text=_('Additional context data about the action')
    )
    
    class Meta:
        verbose_name = _('moderation log')
        verbose_name_plural = _('moderation logs')
        db_table = 'moderation_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['admin', '-created_at']),
            models.Index(fields=['action_type', '-created_at']),
            models.Index(fields=['affected_user']),
            models.Index(fields=['affected_course']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        admin_name = self.admin.get_full_name() if self.admin else 'System'
        return f"{admin_name} - {self.action_type}"
