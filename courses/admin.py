"""
Admin configuration for Courses app.
Comprehensive admin interface using Django Jazzmin.
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.db.models import Count, Avg
from .models import (
    Category, 
    Course, 
    CourseStatus,
    CourseModule, 
    Lesson, 
    HomeworkAssignment,
    HomeworkSubmission,
    CourseEnrollment, 
    LessonProgress,
    CourseReview,
)


class SubcategoryInline(admin.TabularInline):
    """Inline for subcategories."""
    model = Category
    fk_name = 'parent'
    extra = 0
    fields = ('name', 'slug', 'icon', 'order')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Category admin with hierarchy support."""
    
    list_display = ('name', 'parent', 'slug', 'order', 'course_count')
    list_filter = ('parent',)
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('order', 'name')
    inlines = [SubcategoryInline]
    
    list_per_page = 25
    
    def course_count(self, obj):
        return obj.courses.count()
    course_count.short_description = _('Courses')


class CourseModuleInline(admin.TabularInline):
    """Inline for course modules."""
    model = CourseModule
    extra = 0
    fields = ('title', 'order', 'description')
    ordering = ('order',)


class LessonInline(admin.TabularInline):
    """Inline for lessons within a module."""
    model = Lesson
    extra = 0
    fields = ('title', 'order', 'duration_minutes', 'is_preview')
    ordering = ('order',)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """Course admin with comprehensive management features."""
    
    list_display = (
        'title',
        'author_link',
        'status_badge',
        'price_display',
        'enrollment_count',
        'average_rating_display',
        'created_at',
    )
    
    list_filter = (
        'status',
        'level',
        'categories',
        'language',
        'created_at',
    )
    
    search_fields = (
        'title',
        'slug',
        'description',
        'author__first_name',
        'author__last_name',
        'author__phone_number',
    )
    
    prepopulated_fields = {'slug': ('title',)}
    
    readonly_fields = (
        'enrollment_count',
        'average_rating',
        'review_count',
        'total_duration_minutes',
        'published_at',
        'created_at',
        'updated_at',
    )
    
    raw_id_fields = ('author',)
    filter_horizontal = ('categories',)
    
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    inlines = [CourseModuleInline]
    
    list_per_page = 20
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('title', 'slug', 'author', 'status', 'categories')
        }),
        (_('Content'), {
            'fields': ('description', 'short_description', 'thumbnail', 'trailer_url')
        }),
        (_('Course Details'), {
            'fields': ('price', 'level', 'language', 'requirements', 'what_you_will_learn')
        }),
        (_('Statistics'), {
            'fields': ('enrollment_count', 'average_rating', 'review_count', 'total_duration_minutes'),
            'classes': ('collapse',),
        }),
        (_('Dates'), {
            'fields': ('published_at', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    actions = ['publish_courses', 'archive_courses', 'mark_pending']
    
    def author_link(self, obj):
        """Link to author profile."""
        return format_html(
            '<a href="/admin/users/user/{}/change/">{}</a>',
            obj.author.id,
            obj.author.get_full_name() or obj.author.phone_number
        )
    author_link.short_description = _('Author')
    author_link.admin_order_field = 'author__first_name'
    
    def status_badge(self, obj):
        """Display status with colored badge."""
        colors = {
            CourseStatus.DRAFT: 'secondary',
            CourseStatus.PENDING: 'warning',
            CourseStatus.PUBLISHED: 'success',
            CourseStatus.REJECTED: 'danger',
            CourseStatus.ARCHIVED: 'dark',
        }
        color = colors.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = _('Status')
    status_badge.admin_order_field = 'status'
    
    def price_display(self, obj):
        """Format price with currency."""
        return f"{obj.price:,.0f} UZS"
    price_display.short_description = _('Price')
    price_display.admin_order_field = 'price'
    
    def average_rating_display(self, obj):
        """Display rating with stars."""
        if obj.average_rating > 0:
            stars = '★' * int(obj.average_rating) + '☆' * (5 - int(obj.average_rating))
            return f"{obj.average_rating:.1f} {stars}"
        return _('No ratings')
    average_rating_display.short_description = _('Rating')
    average_rating_display.admin_order_field = 'average_rating'
    
    @admin.action(description=_('Publish selected courses'))
    def publish_courses(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(status=CourseStatus.PENDING).update(
            status=CourseStatus.PUBLISHED,
            published_at=timezone.now()
        )
        self.message_user(request, f'{updated} courses published.')
    
    @admin.action(description=_('Archive selected courses'))
    def archive_courses(self, request, queryset):
        updated = queryset.update(status=CourseStatus.ARCHIVED)
        self.message_user(request, f'{updated} courses archived.')
    
    @admin.action(description=_('Mark as pending review'))
    def mark_pending(self, request, queryset):
        updated = queryset.update(status=CourseStatus.PENDING)
        self.message_user(request, f'{updated} courses marked as pending.')


@admin.register(CourseModule)
class CourseModuleAdmin(admin.ModelAdmin):
    """Course module admin."""
    
    list_display = ('title', 'course', 'order', 'lesson_count')
    list_filter = ('course',)
    search_fields = ('title', 'course__title')
    ordering = ('course', 'order')
    inlines = [LessonInline]
    raw_id_fields = ('course',)
    
    def lesson_count(self, obj):
        return obj.lessons.count()
    lesson_count.short_description = _('Lessons')


class HomeworkAssignmentInline(admin.StackedInline):
    """Inline for homework assignment."""
    model = HomeworkAssignment
    extra = 0


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    """Lesson admin with detailed management."""
    
    list_display = (
        'title',
        'module',
        'order',
        'duration_display',
        'is_preview',
        'has_homework',
    )
    
    list_filter = ('is_preview', 'module__course')
    search_fields = ('title', 'module__title', 'module__course__title')
    ordering = ('module', 'order')
    raw_id_fields = ('module',)
    inlines = [HomeworkAssignmentInline]
    
    list_per_page = 30
    
    def duration_display(self, obj):
        """Display duration in human readable format."""
        if obj.duration_minutes >= 60:
            hours = obj.duration_minutes // 60
            minutes = obj.duration_minutes % 60
            return f"{hours}h {minutes}m"
        return f"{obj.duration_minutes}m"
    duration_display.short_description = _('Duration')
    duration_display.admin_order_field = 'duration_minutes'
    
    def has_homework(self, obj):
        """Check if lesson has homework."""
        return hasattr(obj, 'homework') and obj.homework is not None
    has_homework.short_description = _('Homework')
    has_homework.boolean = True


@admin.register(HomeworkAssignment)
class HomeworkAssignmentAdmin(admin.ModelAdmin):
    """Homework assignment admin."""
    
    list_display = ('title', 'lesson', 'submission_count')
    search_fields = ('title', 'lesson__title')
    raw_id_fields = ('lesson',)
    
    def submission_count(self, obj):
        return obj.submissions.count()
    submission_count.short_description = _('Submissions')


@admin.register(HomeworkSubmission)
class HomeworkSubmissionAdmin(admin.ModelAdmin):
    """Homework submission admin with grading features."""
    
    list_display = (
        'student',
        'assignment',
        'grade_display',
        'graded_at',
        'created_at',
    )
    
    list_filter = ('graded_at', 'created_at')
    search_fields = (
        'student__first_name',
        'student__last_name',
        'assignment__title',
    )
    
    raw_id_fields = ('student', 'assignment')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (_('Submission'), {
            'fields': ('assignment', 'student', 'content', 'attachment')
        }),
        (_('Grading'), {
            'fields': ('grade', 'feedback', 'graded_at')
        }),
        (_('Dates'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def grade_display(self, obj):
        """Display grade with color coding."""
        if obj.grade is None:
            return format_html('<span class="badge badge-warning">{}</span>', 'Not graded')
        elif obj.grade >= 80:
            color = 'success'
        elif obj.grade >= 60:
            color = 'info'
        elif obj.grade >= 40:
            color = 'warning'
        else:
            color = 'danger'
        return format_html(
            '<span class="badge badge-{}">{}/100</span>',
            color,
            int(obj.grade)
        )
    grade_display.short_description = _('Grade')
    grade_display.admin_order_field = 'grade'


@admin.register(CourseEnrollment)
class CourseEnrollmentAdmin(admin.ModelAdmin):
    """Course enrollment admin."""
    
    list_display = (
        'student',
        'course',
        'price_paid_display',
        'progress_bar',
        'completed',
        'certificate_issued',
        'created_at',
    )
    
    list_filter = ('completed', 'certificate_issued', 'created_at')
    search_fields = (
        'student__first_name',
        'student__last_name',
        'student__phone_number',
        'course__title',
    )
    
    raw_id_fields = ('student', 'course')
    readonly_fields = ('created_at', 'updated_at', 'last_accessed')
    date_hierarchy = 'created_at'
    
    list_per_page = 30
    
    def price_paid_display(self, obj):
        return f"{obj.price_paid:,.0f} UZS"
    price_paid_display.short_description = _('Price Paid')
    price_paid_display.admin_order_field = 'price_paid'
    
    def progress_bar(self, obj):
        """Display progress as a progress bar."""
        progress = float(obj.progress_percentage)
        if progress >= 80:
            color = 'success'
        elif progress >= 50:
            color = 'info'
        elif progress >= 25:
            color = 'warning'
        else:
            color = 'danger'
        return format_html(
            '<div class="progress" style="width: 100px; height: 20px;">'
            '<div class="progress-bar bg-{}" role="progressbar" style="width: {}%">'
            '{:.0f}%</div></div>',
            color, progress, progress
        )
    progress_bar.short_description = _('Progress')


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    """Lesson progress admin."""
    
    list_display = ('enrollment', 'lesson', 'completed', 'watch_percentage', 'updated_at')
    list_filter = ('completed',)
    search_fields = ('enrollment__student__first_name', 'lesson__title')
    raw_id_fields = ('enrollment', 'lesson')


@admin.register(CourseReview)
class CourseReviewAdmin(admin.ModelAdmin):
    """Course review admin with moderation features."""
    
    list_display = (
        'student',
        'course',
        'rating_stars',
        'is_verified_purchase',
        'helpful_count',
        'created_at',
    )
    
    list_filter = ('rating', 'is_verified_purchase', 'created_at')
    search_fields = (
        'student__first_name',
        'student__last_name',
        'course__title',
        'comment',
    )
    
    raw_id_fields = ('student', 'course')
    readonly_fields = ('created_at', 'updated_at', 'is_verified_purchase')
    date_hierarchy = 'created_at'
    
    list_per_page = 25
    
    def rating_stars(self, obj):
        """Display rating as stars."""
        stars = '★' * obj.rating + '☆' * (5 - obj.rating)
        return format_html('<span style="color: gold;">{}</span>', stars)
    rating_stars.short_description = _('Rating')
    rating_stars.admin_order_field = 'rating'
