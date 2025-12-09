"""
Student models for IlmSpace platform.
Manages student profiles and learning history.
"""
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from users.base import BaseModel
from decimal import Decimal


class StudentProfile(BaseModel):
    """
    Extended profile for students.
    Follows SRP - manages student-specific information.
    """
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_profile',
        verbose_name=_('user'),
        limit_choices_to={'role': 'STUDENT'}
    )
    
    profile_picture = models.ImageField(
        _('profile picture'),
        upload_to='students/profiles/',
        blank=True,
        null=True,
        help_text=_('Student profile picture')
    )
    
    bio = models.TextField(
        _('bio'),
        blank=True,
        help_text=_('Student bio or learning goals')
    )
    
    # Learning preferences
    interested_categories = models.ManyToManyField(
        'courses.Category',
        blank=True,
        related_name='interested_students',
        verbose_name=_('interested categories'),
        help_text=_('Categories student is interested in')
    )
    
    # Statistics (denormalized for performance)
    enrolled_courses_count = models.PositiveIntegerField(
        _('enrolled courses'),
        default=0,
        help_text=_('Total courses enrolled in')
    )
    
    completed_courses_count = models.PositiveIntegerField(
        _('completed courses'),
        default=0,
        help_text=_('Total courses completed')
    )
    
    total_watch_time_hours = models.PositiveIntegerField(
        _('total watch time'),
        default=0,
        help_text=_('Total video watch time in hours')
    )
    
    certificates_earned = models.PositiveIntegerField(
        _('certificates earned'),
        default=0,
        help_text=_('Number of completion certificates earned')
    )
    
    class Meta:
        verbose_name = _('student profile')
        verbose_name_plural = _('student profiles')
        db_table = 'student_profiles'
        indexes = [
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - Student Profile"


class WatchHistory(BaseModel):
    """
    Track all video watching activity for analytics and recommendations.
    Follows SRP - manages watch history only.
    """
    
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='watch_history',
        verbose_name=_('student'),
        limit_choices_to={'role': 'STUDENT'}
    )
    
    lesson = models.ForeignKey(
        'courses.Lesson',
        on_delete=models.CASCADE,
        related_name='watch_history',
        verbose_name=_('lesson')
    )
    
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        related_name='watch_history',
        verbose_name=_('course'),
        help_text=_('Denormalized for easier querying')
    )
    
    watch_duration_seconds = models.PositiveIntegerField(
        _('watch duration'),
        default=0,
        help_text=_('How long student watched in this session (seconds)')
    )
    
    percentage_watched = models.DecimalField(
        _('percentage watched'),
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text=_('Percentage of video watched in this session')
    )
    
    session_id = models.CharField(
        _('session ID'),
        max_length=100,
        blank=True,
        help_text=_('Session identifier for grouping watch events')
    )
    
    device_type = models.CharField(
        _('device type'),
        max_length=50,
        blank=True,
        help_text=_('Device used for watching (desktop, mobile, tablet)')
    )
    
    class Meta:
        verbose_name = _('watch history')
        verbose_name_plural = _('watch history')
        db_table = 'watch_history'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['student', '-created_at']),
            models.Index(fields=['course', '-created_at']),
            models.Index(fields=['lesson']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.student.get_full_name()} watched {self.lesson.title}"


class Certificate(BaseModel):
    """
    Course completion certificates.
    Follows SRP - manages certificate generation and storage.
    Optional for MVP but included for completeness.
    """
    
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='certificates',
        verbose_name=_('student'),
        limit_choices_to={'role': 'STUDENT'}
    )
    
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        related_name='certificates',
        verbose_name=_('course')
    )
    
    enrollment = models.OneToOneField(
        'courses.CourseEnrollment',
        on_delete=models.CASCADE,
        related_name='certificate',
        verbose_name=_('enrollment')
    )
    
    certificate_id = models.CharField(
        _('certificate ID'),
        max_length=100,
        unique=True,
        help_text=_('Unique certificate identifier for verification')
    )
    
    certificate_file = models.FileField(
        _('certificate file'),
        upload_to='certificates/',
        blank=True,
        null=True,
        help_text=_('Generated PDF certificate')
    )
    
    issued_at = models.DateTimeField(
        _('issued at'),
        auto_now_add=True,
        help_text=_('When certificate was issued')
    )
    
    verification_url = models.URLField(
        _('verification URL'),
        blank=True,
        help_text=_('Public URL to verify certificate authenticity')
    )
    
    class Meta:
        verbose_name = _('certificate')
        verbose_name_plural = _('certificates')
        db_table = 'certificates'
        ordering = ['-issued_at']
        unique_together = [['student', 'course']]
        indexes = [
            models.Index(fields=['certificate_id']),
            models.Index(fields=['student', '-issued_at']),
            models.Index(fields=['course']),
        ]
    
    def __str__(self):
        return f"Certificate {self.certificate_id} - {self.student.get_full_name()}"
    
    def save(self, *args, **kwargs):
        if not self.certificate_id:
            # Generate unique certificate ID
            import uuid
            self.certificate_id = f"ILMSPACE-{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)
