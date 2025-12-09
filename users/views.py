"""
Views for role-based home pages.
"""
from django.shortcuts import render, redirect
from django.db.models import Sum, Avg, Count, Q
from decimal import Decimal

from courses.models import Course, CourseEnrollment, Category
from authors.models import AuthorBalance
from payments.models import Transaction
from .models import User, UserRole


def landing_view(request):
    """
    Landing page with role selection.
    No authentication required for now.
    """
    return render(request, 'landing.html')


def select_role_view(request, role):
    """
    Set the selected role in session and redirect to appropriate dashboard.
    """
    # Store role in session
    request.session['selected_role'] = role.upper()
    
    # Redirect to appropriate dashboard
    if role == 'student':
        return redirect('student_home')
    elif role == 'author':
        return redirect('author_home')
    elif role == 'admin':
        return redirect('admin_home')
    else:
        return redirect('landing')


def student_dashboard_view(request):
    """
    Student dashboard with enrolled courses, progress, and recommendations.
    Uses session-based role for now (no auth required).
    """
    # For demo purposes, use dummy data since we don't have real users yet
    
    # Get categories
    categories = Category.objects.filter(
        parent=None
    ).annotate(
        course_count=Count('courses', filter=Q(courses__status='PUBLISHED'))
    )[:8]
    
    # Get published courses
    recommended_courses = Course.objects.filter(
        status='PUBLISHED'
    ).order_by('-average_rating', '-enrollment_count')[:8]
    
    context = {
        'enrolled_count': 0,
        'completed_count': 0,
        'total_hours': 0,
        'certificates_count': 0,
        'in_progress_courses': [],
        'recommended_courses': recommended_courses,
        'categories': categories,
    }
    
    return render(request, 'student_home.html', context)


def author_dashboard_view(request):
    """
    Author dashboard with courses, earnings, and analytics.
    Uses session-based role for now (no auth required).
    """
    # Get all courses
    all_courses = Course.objects.all().select_related('author').order_by('-created_at')
    
    # Calculate real stats from database
    active_courses_count = all_courses.filter(status='PUBLISHED').count()
    
    # Get total students enrolled across all courses
    total_students = CourseEnrollment.objects.count()
    
    # Calculate average rating from courses that have ratings
    avg_rating_result = Course.objects.filter(
        average_rating__gt=0
    ).aggregate(avg=Avg('average_rating'))
    average_rating = avg_rating_result['avg'] or Decimal('0.0')
    
    # Calculate total earnings from enrollments (sum of price_paid)
    total_earnings_result = CourseEnrollment.objects.aggregate(
        total=Sum('price_paid')
    )
    available_balance = total_earnings_result['total'] or Decimal('0.00')
    
    # Get courses for display (limit to 6 for dashboard)
    courses = all_courses[:6]
    
    # Get recent sales (enrollments with price > 0)
    recent_sales = CourseEnrollment.objects.select_related(
        'course', 'student'
    ).filter(
        price_paid__gt=0
    ).order_by('-created_at')[:10]
    
    context = {
        'available_balance': available_balance,
        'total_students': total_students,
        'active_courses': active_courses_count,
        'average_rating': average_rating,
        'courses': courses,
        'recent_sales': recent_sales,
    }
    
    return render(request, 'author_home.html', context)


def admin_dashboard_view(request):
    """
    Admin dashboard with platform statistics and moderation queue.
    Uses session-based role for now (no auth required).
    """
    # Platform statistics
    total_users = User.objects.count()
    total_courses = Course.objects.count()
    
    # Pending moderations
    pending_moderations = Course.objects.filter(status='PENDING').count()
    pending_courses = Course.objects.filter(
        status='PENDING'
    ).select_related('author').order_by('-created_at')[:6]
    
    # Total revenue
    total_revenue = Transaction.objects.filter(
        status='SUCCESS',
        transaction_type='COURSE_PURCHASE'
    ).aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')
    
    # Recent transactions
    recent_transactions = Transaction.objects.all().order_by('-created_at')[:10]
    
    context = {
        'total_users': total_users,
        'total_courses': total_courses,
        'pending_moderations': pending_moderations,
        'total_revenue': total_revenue,
        'pending_courses': pending_courses,
        'recent_transactions': recent_transactions,
    }
    
    return render(request, 'admin_home.html', context)
