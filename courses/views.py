"""
Views for course management.

This module contains views for:
- Student-facing course browsing and learning
- Author course creation and management
- AJAX endpoints for course building
"""
import json
import uuid

from django.contrib import messages
from django.db.models import Count, Max, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from users.models import User

from .forms import CourseForm, CourseModuleForm, LessonForm
from .models import (
    Category,
    Course,
    CourseEnrollment,
    CourseModule,
    CourseStatus,
    Lesson,
    LessonProgress,
)


# ==================== Student-Facing Views ====================

def course_list_view(request):
    """
    Browse all published courses with filtering options.
    """
    # Get base queryset of published courses
    courses = Course.objects.filter(
        status=CourseStatus.PUBLISHED
    ).select_related('author').prefetch_related('categories')
    
    # Filter by category
    category_slug = request.GET.get('category')
    selected_category = None
    if category_slug:
        selected_category = Category.objects.filter(slug=category_slug).first()
        if selected_category:
            courses = courses.filter(categories=selected_category)
    
    # Filter by level
    level = request.GET.get('level')
    if level:
        courses = courses.filter(level=level)
    
    # Filter by price range
    price_filter = request.GET.get('price')
    if price_filter == 'free':
        courses = courses.filter(price=0)
    elif price_filter == 'paid':
        courses = courses.filter(price__gt=0)
    
    # Search
    search_query = request.GET.get('q')
    if search_query:
        courses = courses.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(author__first_name__icontains=search_query) |
            Q(author__last_name__icontains=search_query)
        )
    
    # Sorting
    sort_by = request.GET.get('sort', '-created_at')
    valid_sorts = {
        'newest': '-created_at',
        'oldest': 'created_at',
        'price_low': 'price',
        'price_high': '-price',
        'rating': '-average_rating',
        'popular': '-enrollment_count',
    }
    sort_field = valid_sorts.get(sort_by, '-created_at')
    courses = courses.order_by(sort_field)
    
    # Get all categories for filter sidebar
    categories = Category.objects.filter(parent=None).annotate(
        course_count=Count('courses', filter=Q(courses__status=CourseStatus.PUBLISHED))
    )
    
    context = {
        'courses': courses,
        'categories': categories,
        'selected_category': selected_category,
        'selected_level': level,
        'selected_price': price_filter,
        'search_query': search_query,
        'sort_by': sort_by,
    }
    
    return render(request, 'courses/course_list.html', context)


def course_detail_view(request, slug):
    """
    Course detail page with curriculum and reviews.
    """
    course = get_object_or_404(
        Course.objects.select_related('author').prefetch_related(
            'categories',
            'modules__lessons',
            'reviews__student'
        ),
        slug=slug,
        status=CourseStatus.PUBLISHED
    )
    
    # Check if user is enrolled (for demo, use session)
    is_enrolled = False
    enrollment = None
    
    # Get demo student from session or create one
    demo_student_id = request.session.get('demo_student_id')
    if demo_student_id:
        try:
            demo_student = User.objects.get(id=demo_student_id)
            enrollment = CourseEnrollment.objects.filter(
                course=course,
                student=demo_student
            ).first()
            is_enrolled = enrollment is not None
        except User.DoesNotExist:
            pass
    
    # Get modules with lessons
    modules = course.modules.prefetch_related('lessons').order_by('order')
    
    # Calculate total lessons and duration
    total_lessons = sum(module.lessons.count() for module in modules)
    total_duration = sum(
        lesson.duration_minutes 
        for module in modules 
        for lesson in module.lessons.all()
    )
    
    # Get reviews
    reviews = course.reviews.select_related('student').order_by('-created_at')[:10]
    
    # Rating distribution
    rating_distribution = {}
    for i in range(1, 6):
        rating_distribution[i] = course.reviews.filter(rating=i).count()
    
    context = {
        'course': course,
        'modules': modules,
        'total_lessons': total_lessons,
        'total_duration': total_duration,
        'is_enrolled': is_enrolled,
        'enrollment': enrollment,
        'reviews': reviews,
        'rating_distribution': rating_distribution,
    }
    
    return render(request, 'courses/course_detail.html', context)


def course_learn_view(request, slug, lesson_id=None):
    """
    Course learning page with video player.
    """
    course = get_object_or_404(
        Course.objects.select_related('author').prefetch_related(
            'modules__lessons'
        ),
        slug=slug,
        status=CourseStatus.PUBLISHED
    )
    
    # Get or create demo student
    demo_student = get_or_create_demo_student(request)
    
    # Check enrollment
    enrollment = CourseEnrollment.objects.filter(
        course=course,
        student=demo_student
    ).first()
    
    # Get all modules and lessons
    modules = course.modules.prefetch_related('lessons').order_by('order')
    
    # Get current lesson
    current_lesson = None
    if lesson_id:
        current_lesson = get_object_or_404(Lesson, id=lesson_id, module__course=course)
    else:
        # Get first lesson
        for module in modules:
            first_lesson = module.lessons.order_by('order').first()
            if first_lesson:
                current_lesson = first_lesson
                break
    
    # Check if user can access this lesson
    can_access = False
    if enrollment:
        can_access = True
    elif current_lesson and current_lesson.is_preview:
        can_access = True
    
    # Get lesson progress if enrolled
    lesson_progress = {}
    if enrollment:
        progress_records = LessonProgress.objects.filter(enrollment=enrollment)
        for record in progress_records:
            lesson_progress[record.lesson_id] = {
                'completed': record.completed,
                'watch_percentage': float(record.watch_percentage)
            }
    
    # Calculate next/previous lessons
    all_lessons = []
    for module in modules:
        for lesson in module.lessons.order_by('order'):
            all_lessons.append(lesson)
    
    current_index = None
    if current_lesson:
        for i, lesson in enumerate(all_lessons):
            if lesson.id == current_lesson.id:
                current_index = i
                break
    
    prev_lesson = all_lessons[current_index - 1] if current_index and current_index > 0 else None
    next_lesson = all_lessons[current_index + 1] if current_index is not None and current_index < len(all_lessons) - 1 else None
    
    context = {
        'course': course,
        'modules': modules,
        'current_lesson': current_lesson,
        'can_access': can_access,
        'is_enrolled': enrollment is not None,
        'enrollment': enrollment,
        'lesson_progress': lesson_progress,
        'prev_lesson': prev_lesson,
        'next_lesson': next_lesson,
        'all_lessons': all_lessons,
    }
    
    return render(request, 'courses/course_learn.html', context)


def enroll_course_view(request, slug):
    """
    Enroll in a course (simplified for demo - no payment).
    """
    course = get_object_or_404(Course, slug=slug, status=CourseStatus.PUBLISHED)
    
    # Get or create demo student
    demo_student = get_or_create_demo_student(request)
    
    # Check if already enrolled
    enrollment, created = CourseEnrollment.objects.get_or_create(
        course=course,
        student=demo_student,
        defaults={
            'price_paid': course.price,
        }
    )
    
    if created:
        # Update course enrollment count
        course.enrollment_count += 1
        course.save(update_fields=['enrollment_count'])
        messages.success(request, f'You have enrolled in "{course.title}"!')
    else:
        messages.info(request, 'You are already enrolled in this course.')
    
    return redirect('course_learn', slug=slug)


def get_or_create_demo_student(request):
    """
    Helper to get or create a demo student for session-based demo.
    """
    demo_student_id = request.session.get('demo_student_id')
    
    if demo_student_id:
        try:
            return User.objects.get(id=demo_student_id)
        except User.DoesNotExist:
            pass
    
    # Create demo student
    demo_student = User.objects.create_user(
        phone_number=f'+998{uuid.uuid4().hex[:9]}',
        password='demo123',
        first_name='Demo',
        last_name='Student',
        role='STUDENT'
    )
    request.session['demo_student_id'] = demo_student.id
    return demo_student


@require_http_methods(["POST"])
def update_lesson_progress(request, lesson_id):
    """
    Update lesson watch progress (AJAX).
    """
    lesson = get_object_or_404(Lesson, id=lesson_id)
    
    demo_student_id = request.session.get('demo_student_id')
    if not demo_student_id:
        return JsonResponse({'success': False, 'error': 'Not logged in'}, status=401)
    
    enrollment = CourseEnrollment.objects.filter(
        course=lesson.module.course,
        student_id=demo_student_id
    ).first()
    
    if not enrollment:
        return JsonResponse({'success': False, 'error': 'Not enrolled'}, status=403)
    
    data = json.loads(request.body)
    watch_percentage = data.get('watch_percentage', 0)
    
    progress, created = LessonProgress.objects.get_or_create(
        enrollment=enrollment,
        lesson=lesson,
        defaults={'watch_percentage': watch_percentage}
    )
    
    if not created and watch_percentage > float(progress.watch_percentage):
        progress.watch_percentage = watch_percentage
        progress.save(update_fields=['watch_percentage'])
    
    return JsonResponse({'success': True, 'watch_percentage': float(progress.watch_percentage)})


@require_http_methods(["POST"])
def mark_lesson_complete(request, lesson_id):
    """
    Mark lesson as complete (AJAX).
    """
    lesson = get_object_or_404(Lesson, id=lesson_id)
    
    demo_student_id = request.session.get('demo_student_id')
    if not demo_student_id:
        return JsonResponse({'success': False, 'error': 'Not logged in'}, status=401)
    
    enrollment = CourseEnrollment.objects.filter(
        course=lesson.module.course,
        student_id=demo_student_id
    ).first()
    
    if not enrollment:
        return JsonResponse({'success': False, 'error': 'Not enrolled'}, status=403)
    
    progress, created = LessonProgress.objects.get_or_create(
        enrollment=enrollment,
        lesson=lesson,
        defaults={'completed': True, 'watch_percentage': 100}
    )
    
    if not created:
        progress.completed = True
        progress.watch_percentage = 100
        progress.save(update_fields=['completed', 'watch_percentage'])
    
    # Update course progress
    total_lessons = Lesson.objects.filter(module__course=lesson.module.course).count()
    completed_lessons = LessonProgress.objects.filter(
        enrollment=enrollment,
        completed=True
    ).count()
    
    enrollment.progress_percentage = (completed_lessons / total_lessons) * 100 if total_lessons > 0 else 0
    enrollment.save(update_fields=['progress_percentage'])
    
    return JsonResponse({
        'success': True,
        'course_progress': float(enrollment.progress_percentage)
    })


# ==================== Author-Facing Views ====================


def create_course_view(request):
    """
    Create a new course - Step 1: Basic Information
    """
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            # For now, use dummy author (session-based)
            # When auth is added, use: course.author = request.user
            # For demo, get first author or create one
            try:
                author = User.objects.filter(role='AUTHOR').first()
                if not author:
                    # Create dummy author for testing
                    author = User.objects.create_user(
                        phone_number='+998900000000',
                        password='test123',
                        first_name='Demo',
                        last_name='Author',
                        role='AUTHOR'
                    )
            except:
                author = User.objects.filter(role='AUTHOR').first()
            
            course.author = author
            course.status = CourseStatus.DRAFT
            course.save()
            form.save_m2m()  # Save many-to-many relationships (categories)
            
            messages.success(request, f'Course "{course.title}" created successfully!')
            return redirect('course_builder', course_id=course.id)
    else:
        form = CourseForm()
    
    return render(request, 'courses/course_create.html', {'form': form})


def course_builder_view(request, course_id):
    """
    Course builder interface - manage modules and lessons
    """
    course = get_object_or_404(Course, id=course_id)
    modules = course.modules.all().order_by('order')
    
    context = {
        'course': course,
        'modules': modules,
        'module_form': CourseModuleForm(),
        'lesson_form': LessonForm(),
    }
    
    return render(request, 'courses/course_builder.html', context)


def edit_course_view(request, course_id):
    """
    Edit course basic information
    """
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, 'Course updated successfully!')
            return redirect('course_builder', course_id=course.id)
    else:
        form = CourseForm(instance=course)
    
    return render(request, 'courses/course_edit.html', {'form': form, 'course': course})


@require_http_methods(["POST"])
def add_module_view(request, course_id):
    """
    Add a new module to course (AJAX)
    """
    course = get_object_or_404(Course, id=course_id)
    form = CourseModuleForm(request.POST)
    
    if form.is_valid():
        module = form.save(commit=False)
        module.course = course
        # Auto-increment order
        max_order = course.modules.aggregate(Max('order'))['order__max'] or 0
        module.order = max_order + 1
        module.save()
        
        return JsonResponse({
            'success': True,
            'module': {
                'id': module.id,
                'title': module.title,
                'description': module.description,
                'order': module.order,
            }
        })
    else:
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)


@require_http_methods(["POST"])
def edit_module_view(request, module_id):
    """
    Edit module (AJAX)
    """
    module = get_object_or_404(CourseModule, id=module_id)
    form = CourseModuleForm(request.POST, instance=module)
    
    if form.is_valid():
        form.save()
        return JsonResponse({
            'success': True,
            'module': {
                'id': module.id,
                'title': module.title,
                'description': module.description,
            }
        })
    else:
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)


@require_http_methods(["POST"])
def delete_module_view(request, module_id):
    """
    Delete module (AJAX - soft delete)
    """
    module = get_object_or_404(CourseModule, id=module_id)
    module.delete()  # Soft delete from BaseModel
    
    return JsonResponse({'success': True})


@require_http_methods(["POST"])
def add_lesson_view(request, module_id):
    """
    Add a new lesson to module (AJAX)
    """
    module = get_object_or_404(CourseModule, id=module_id)
    form = LessonForm(request.POST, request.FILES)
    
    if form.is_valid():
        lesson = form.save(commit=False)
        lesson.module = module
        # Auto-increment order
        max_order = module.lessons.aggregate(Max('order'))['order__max'] or 0
        lesson.order = max_order + 1
        lesson.save()
        
        return JsonResponse({
            'success': True,
            'lesson': {
                'id': lesson.id,
                'title': lesson.title,
                'duration_minutes': lesson.duration_minutes,
                'is_preview': lesson.is_preview,
                'order': lesson.order,
            }
        })
    else:
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)


@require_http_methods(["POST"])
def edit_lesson_view(request, lesson_id):
    """
    Edit lesson (AJAX)
    """
    lesson = get_object_or_404(Lesson, id=lesson_id)
    form = LessonForm(request.POST, request.FILES, instance=lesson)
    
    if form.is_valid():
        form.save()
        return JsonResponse({
            'success': True,
            'lesson': {
                'id': lesson.id,
                'title': lesson.title,
                'duration_minutes': lesson.duration_minutes,
                'is_preview': lesson.is_preview,
            }
        })
    else:
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)


@require_http_methods(["POST"])
def delete_lesson_view(request, lesson_id):
    """
    Delete lesson (AJAX - soft delete)
    """
    lesson = get_object_or_404(Lesson, id=lesson_id)
    lesson.delete()  # Soft delete from BaseModel
    
    return JsonResponse({'success': True})


@require_http_methods(["POST"])
def publish_course_view(request, course_id):
    """
    Submit course for review (change status to PENDING)
    """
    course = get_object_or_404(Course, id=course_id)
    
    # Validation: Check if course has at least 1 module with lessons
    if not course.modules.exists():
        messages.error(request, 'Course must have at least one module before publishing.')
        return redirect('course_builder', course_id=course.id)
    
    has_lessons = any(module.lessons.exists() for module in course.modules.all())
    if not has_lessons:
        messages.error(request, 'Course modules must have at least one lesson before publishing.')
        return redirect('course_builder', course_id=course.id)
    
    # Change status
    course.status = CourseStatus.PENDING
    course.save()
    
    messages.success(request, f'Course "{course.title}" submitted for review!')
    return redirect('author_home')
