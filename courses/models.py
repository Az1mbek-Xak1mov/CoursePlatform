"""
Course models for IlmSpace educational marketplace.
Handles course structure, content, enrollments, and student interactions.
"""
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from users.base import BaseModel, TimestampedModel
from decimal import Decimal


class Category(BaseModel):
    
    name = models.CharField(
        _('name'),
        max_length=100,
        help_text=_('Category name (e.g., IT, Languages, Hobby)')
    )
    
    slug = models.SlugField(
        _('slug'),
        max_length=120,
        unique=True,
        help_text=_('URL-friendly version of the name')
    )
    
    description = models.TextField(
        _('description'),
        blank=True,
        help_text=_('Category description')
    )
    
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories',
        verbose_name=_('parent category'),
        help_text=_('Parent category for hierarchical structure')
    )
    
    icon = models.CharField(
        _('icon'),
        max_length=50,
        blank=True,
        help_text=_('Icon class or emoji for display')
    )
    
    order = models.PositiveIntegerField(
        _('display order'),
        default=0,
        help_text=_('Order for displaying categories')
    )
    
    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')
        db_table = 'categories'
        ordering = ['order', 'name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['parent']),
        ]
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class CourseStatus(models.TextChoices):
    """Course publication status."""
    DRAFT = 'DRAFT', _('Draft')
    PENDING = 'PENDING', _('Pending Review')
    PUBLISHED = 'PUBLISHED', _('Published')
    REJECTED = 'REJECTED', _('Rejected')
    ARCHIVED = 'ARCHIVED', _('Archived')


class Course(BaseModel):
    """
    Main course model containing all course information.
    Follows SRP - manages course data and metadata.
    """
    
    title = models.CharField(
        _('title'),
        max_length=255,
        help_text=_('Course title')
    )
    
    slug = models.SlugField(
        _('slug'),
        max_length=280,
        unique=True,
        help_text=_('URL-friendly course identifier')
    )
    
    description = models.TextField(
        _('description'),
        help_text=_('Detailed course description')
    )
    
    short_description = models.CharField(
        _('short description'),
        max_length=500,
        blank=True,
        help_text=_('Brief course summary for cards')
    )
    
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='courses',
        verbose_name=_('author'),
        limit_choices_to={'role': 'AUTHOR'}
    )
    
    categories = models.ManyToManyField(
        Category,
        related_name='courses',
        verbose_name=_('categories'),
        help_text=_('Course categories')
    )
    
    thumbnail = models.ImageField(
        _('thumbnail'),
        upload_to='courses/thumbnails/',
        blank=True,
        null=True,
        help_text=_('Course thumbnail image')
    )
    
    trailer_url = models.URLField(
        _('trailer URL'),
        blank=True,
        help_text=_('Free preview video URL (Vimeo/BunnyCDN)')
    )
    
    price = models.DecimalField(
        _('price'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text=_('Course price in UZS')
    )
    
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=CourseStatus.choices,
        default=CourseStatus.DRAFT,
        help_text=_('Publication status')
    )
    
    # Course metadata
    level = models.CharField(
        _('level'),
        max_length=50,
        choices=[
            ('BEGINNER', _('Beginner')),
            ('INTERMEDIATE', _('Intermediate')),
            ('ADVANCED', _('Advanced')),
        ],
        default='BEGINNER',
        help_text=_('Course difficulty level')
    )
    
    language = models.CharField(
        _('language'),
        max_length=10,
        default='uz',
        help_text=_('Course language code')
    )
    
    requirements = models.TextField(
        _('requirements'),
        blank=True,
        help_text=_('What students need to know before taking this course')
    )
    
    what_you_will_learn = models.TextField(
        _('what you will learn'),
        blank=True,
        help_text=_('Key learning outcomes')
    )
    
    # Statistics (denormalized for performance)
    enrollment_count = models.PositiveIntegerField(
        _('enrollment count'),
        default=0,
        help_text=_('Total number of enrolled students')
    )
    
    average_rating = models.DecimalField(
        _('average rating'),
        max_digits=3,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('5.00'))],
        help_text=_('Average course rating')
    )
    
    review_count = models.PositiveIntegerField(
        _('review count'),
        default=0,
        help_text=_('Total number of reviews')
    )
    
    total_duration_minutes = models.PositiveIntegerField(
        _('total duration'),
        default=0,
        help_text=_('Total course duration in minutes')
    )
    
    published_at = models.DateTimeField(
        _('published at'),
        null=True,
        blank=True,
        help_text=_('When the course was published')
    )
    
    class Meta:
        verbose_name = _('course')
        verbose_name_plural = _('courses')
        db_table = 'courses'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['author']),
            models.Index(fields=['status']),
            models.Index(fields=['-average_rating']),
            models.Index(fields=['-enrollment_count']),
            models.Index(fields=['published_at']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class CourseModule(BaseModel):
    """
    Course modules for organizing lessons into sections.
    Follows SRP - handles module organization.
    """
    
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='modules',
        verbose_name=_('course')
    )
    
    title = models.CharField(
        _('title'),
        max_length=255,
        help_text=_('Module title')
    )
    
    description = models.TextField(
        _('description'),
        blank=True,
        help_text=_('Module description')
    )
    
    order = models.PositiveIntegerField(
        _('order'),
        default=0,
        help_text=_('Module display order within course')
    )
    
    class Meta:
        verbose_name = _('course module')
        verbose_name_plural = _('course modules')
        db_table = 'course_modules'
        ordering = ['course', 'order']
        unique_together = [['course', 'order']]
        indexes = [
            models.Index(fields=['course', 'order']),
        ]
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"


class Lesson(BaseModel):
    """
    Individual lesson within a course module.
    Follows SRP - manages lesson content and metadata.
    """
    
    module = models.ForeignKey(
        CourseModule,
        on_delete=models.CASCADE,
        related_name='lessons',
        verbose_name=_('module')
    )
    
    title = models.CharField(
        _('title'),
        max_length=255,
        help_text=_('Lesson title')
    )
    
    description = models.TextField(
        _('description'),
        blank=True,
        help_text=_('Lesson description')
    )
    
    video_url = models.URLField(
        _('video URL'),
        blank=True,
        help_text=_('Video URL from streaming service (YouTube/Vimeo/BunnyCDN)')
    )
    
    video_file = models.FileField(
        _('video file'),
        upload_to='lessons/videos/',
        blank=True,
        null=True,
        help_text=_('Upload video file directly (MP4 recommended)')
    )
    
    duration_minutes = models.PositiveIntegerField(
        _('duration'),
        default=0,
        help_text=_('Lesson duration in minutes')
    )
    
    text_content = models.TextField(
        _('text content'),
        blank=True,
        help_text=_('Additional text materials displayed under video')
    )
    
    attachments = models.FileField(
        _('attachments'),
        upload_to='lessons/attachments/',
        blank=True,
        null=True,
        help_text=_('Downloadable materials (PDF, etc.)')
    )
    
    is_preview = models.BooleanField(
        _('free preview'),
        default=False,
        help_text=_('Allow non-enrolled students to watch this lesson')
    )
    
    order = models.PositiveIntegerField(
        _('order'),
        default=0,
        help_text=_('Lesson display order within module')
    )
    
    class Meta:
        verbose_name = _('lesson')
        verbose_name_plural = _('lessons')
        db_table = 'lessons'
        ordering = ['module', 'order']
        unique_together = [['module', 'order']]
        indexes = [
            models.Index(fields=['module', 'order']),
            models.Index(fields=['is_preview']),
        ]
    
    def __str__(self):
        return f"{self.module.title} - {self.title}"


class HomeworkAssignment(BaseModel):
    """
    Homework assignments associated with lessons.
    Follows SRP - manages assignment definition.
    """
    
    lesson = models.OneToOneField(
        Lesson,
        on_delete=models.CASCADE,
        related_name='homework',
        verbose_name=_('lesson')
    )
    
    title = models.CharField(
        _('title'),
        max_length=255,
        help_text=_('Assignment title')
    )
    
    description = models.TextField(
        _('description'),
        help_text=_('Assignment instructions')
    )
    
    attachment = models.FileField(
        _('attachment'),
        upload_to='homework/assignments/',
        blank=True,
        null=True,
        help_text=_('Assignment files or templates')
    )
    
    class Meta:
        verbose_name = _('homework assignment')
        verbose_name_plural = _('homework assignments')
        db_table = 'homework_assignments'
    
    def __str__(self):
        return f"{self.lesson.title} - {self.title}"


class HomeworkSubmission(BaseModel):
    """
    Student homework submissions.
    Follows SRP - manages submission data and grading.
    """
    
    assignment = models.ForeignKey(
        HomeworkAssignment,
        on_delete=models.CASCADE,
        related_name='submissions',
        verbose_name=_('assignment')
    )
    
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='homework_submissions',
        verbose_name=_('student'),
        limit_choices_to={'role': 'STUDENT'}
    )
    
    content = models.TextField(
        _('submission content'),
        help_text=_('Student answer or submission text')
    )
    
    attachment = models.FileField(
        _('attachment'),
        upload_to='homework/submissions/',
        blank=True,
        null=True,
        help_text=_('Submitted files')
    )
    
    grade = models.DecimalField(
        _('grade'),
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))],
        help_text=_('Grade out of 100')
    )
    
    feedback = models.TextField(
        _('feedback'),
        blank=True,
        help_text=_('Teacher feedback on submission')
    )
    
    graded_at = models.DateTimeField(
        _('graded at'),
        null=True,
        blank=True,
        help_text=_('When the submission was graded')
    )
    
    class Meta:
        verbose_name = _('homework submission')
        verbose_name_plural = _('homework submissions')
        db_table = 'homework_submissions'
        ordering = ['-created_at']
        unique_together = [['assignment', 'student']]
        indexes = [
            models.Index(fields=['assignment', 'student']),
            models.Index(fields=['student', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.assignment.title}"


class CourseEnrollment(BaseModel):
    """
    Student enrollment in courses (represents purchase).
    Follows SRP - manages enrollment status and progress.
    """
    
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name=_('course')
    )
    
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name=_('student'),
        limit_choices_to={'role': 'STUDENT'}
    )
    
    price_paid = models.DecimalField(
        _('price paid'),
        max_digits=10,
        decimal_places=2,
        help_text=_('Amount paid for the course in UZS')
    )
    
    progress_percentage = models.DecimalField(
        _('progress'),
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))],
        help_text=_('Course completion percentage')
    )
    
    completed = models.BooleanField(
        _('completed'),
        default=False,
        help_text=_('Whether student completed the course')
    )
    
    completed_at = models.DateTimeField(
        _('completed at'),
        null=True,
        blank=True,
        help_text=_('When the course was completed')
    )
    
    certificate_issued = models.BooleanField(
        _('certificate issued'),
        default=False,
        help_text=_('Whether completion certificate was issued')
    )
    
    last_accessed = models.DateTimeField(
        _('last accessed'),
        auto_now=True,
        help_text=_('Last time student accessed the course')
    )
    
    class Meta:
        verbose_name = _('course enrollment')
        verbose_name_plural = _('course enrollments')
        db_table = 'course_enrollments'
        ordering = ['-created_at']
        unique_together = [['course', 'student']]
        indexes = [
            models.Index(fields=['student', '-created_at']),
            models.Index(fields=['course', '-created_at']),
            models.Index(fields=['completed']),
        ]
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.course.title}"


class LessonProgress(BaseModel):
    """
    Track student progress on individual lessons.
    Follows SRP - manages lesson completion and watch data.
    """
    
    enrollment = models.ForeignKey(
        CourseEnrollment,
        on_delete=models.CASCADE,
        related_name='lesson_progress',
        verbose_name=_('enrollment')
    )
    
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='progress_records',
        verbose_name=_('lesson')
    )
    
    completed = models.BooleanField(
        _('completed'),
        default=False,
        help_text=_('Whether lesson is marked as complete')
    )
    
    watch_percentage = models.DecimalField(
        _('watch percentage'),
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))],
        help_text=_('How much of the video was watched')
    )
    
    last_position_seconds = models.PositiveIntegerField(
        _('last position'),
        default=0,
        help_text=_('Last watched position in seconds (for resume)')
    )
    
    watch_time_seconds = models.PositiveIntegerField(
        _('total watch time'),
        default=0,
        help_text=_('Total time spent watching (may exceed video length)')
    )
    
    completed_at = models.DateTimeField(
        _('completed at'),
        null=True,
        blank=True,
        help_text=_('When the lesson was marked complete')
    )
    
    class Meta:
        verbose_name = _('lesson progress')
        verbose_name_plural = _('lesson progress records')
        db_table = 'lesson_progress'
        ordering = ['enrollment', 'lesson']
        unique_together = [['enrollment', 'lesson']]
        indexes = [
            models.Index(fields=['enrollment', 'lesson']),
            models.Index(fields=['completed']),
        ]
    
    def __str__(self):
        return f"{self.enrollment.student.get_full_name()} - {self.lesson.title}"


class CourseReview(BaseModel):
    """
    Student reviews and ratings for courses.
    Follows SRP - manages review content and rating.
    """
    
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name=_('course')
    )
    
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='course_reviews',
        verbose_name=_('student'),
        limit_choices_to={'role': 'STUDENT'}
    )
    
    rating = models.PositiveSmallIntegerField(
        _('rating'),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text=_('Rating from 1 to 5 stars')
    )
    
    comment = models.TextField(
        _('comment'),
        blank=True,
        help_text=_('Review text')
    )
    
    is_verified_purchase = models.BooleanField(
        _('verified purchase'),
        default=False,
        help_text=_('Whether student actually purchased the course')
    )
    
    helpful_count = models.PositiveIntegerField(
        _('helpful count'),
        default=0,
        help_text=_('Number of users who found this review helpful')
    )
    
    class Meta:
        verbose_name = _('course review')
        verbose_name_plural = _('course reviews')
        db_table = 'course_reviews'
        ordering = ['-created_at']
        unique_together = [['course', 'student']]
        indexes = [
            models.Index(fields=['course', '-created_at']),
            models.Index(fields=['rating']),
            models.Index(fields=['is_verified_purchase']),
        ]
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.course.title} ({self.rating}★)"
