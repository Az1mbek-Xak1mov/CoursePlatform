"""
Views for role-based home pages and user registration.
"""
from django.shortcuts import render, redirect
from django.db.models import Sum, Avg, Count, Q
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from decimal import Decimal
import uuid

from courses.models import Course, CourseEnrollment, Category
from authors.models import AuthorBalance
from payments.models import Transaction
from .models import User, UserRole
from .forms import (
    PhoneRegistrationForm, 
    OTPVerificationForm, 
    UserDetailsForm,
    EmailRegistrationForm,
    PhoneLoginForm,
    ProfileUpdateForm,
    UserRegistrationForm
)

# Try to import OTP service (may not be available if Redis not configured)
try:
    from utils import OtpService, generate_code
    OTP_AVAILABLE = True
except Exception:
    OTP_AVAILABLE = False


def landing_view(request):
    """
    Landing page with role selection.
    If user is authenticated, redirect to student dashboard.
    """
    if request.user.is_authenticated:
        request.session['selected_role'] = request.user.role or 'STUDENT'
        return redirect('student_home')
    return render(request, 'landing.html')


def select_role_view(request, role):
    """
    Set the selected role in session and redirect to appropriate dashboard.
    Requires login for author/admin roles.
    """
    if not request.user.is_authenticated:
        return redirect('account_login')
    
    # Store role in session
    request.session['selected_role'] = role.upper()
    
    # Redirect to appropriate dashboard
    if role == 'student':
        return redirect('student_home')
    elif role == 'author':
        # Update user role to AUTHOR if switching
        if request.user.role != 'AUTHOR':
            request.user.role = 'AUTHOR'
            request.user.save()
        return redirect('author_home')
    elif role == 'admin':
        if request.user.is_staff:
            return redirect('admin_home')
        else:
            return redirect('student_home')
    else:
        return redirect('landing')


@login_required
def student_dashboard_view(request):
    """
    Student dashboard with enrolled courses, progress, and recommendations.
    Requires authentication.
    """
    # Set session role
    request.session['selected_role'] = 'STUDENT'
    
    # Get user's enrolled courses
    user_enrollments = CourseEnrollment.objects.filter(
        student=request.user
    ).select_related('course', 'course__author')
    
    enrolled_count = user_enrollments.count()
    completed_count = user_enrollments.filter(progress_percentage=100).count()
    
    # Calculate total watch time (approximate)
    total_hours = sum([e.course.total_duration_minutes for e in user_enrollments]) // 60
    
    # Get in-progress courses
    in_progress_courses = user_enrollments.filter(
        progress_percentage__lt=100
    ).order_by('-last_accessed')[:3]
    
    # Get categories
    categories = Category.objects.filter(
        parent=None
    ).annotate(
        course_count=Count('courses', filter=Q(courses__status='PUBLISHED'))
    )[:8]
    
    # Get recommended courses (not enrolled)
    enrolled_course_ids = user_enrollments.values_list('course_id', flat=True)
    recommended_courses = Course.objects.filter(
        status='PUBLISHED'
    ).exclude(
        id__in=enrolled_course_ids
    ).order_by('-average_rating', '-enrollment_count')[:8]
    
    context = {
        'enrolled_count': enrolled_count,
        'completed_count': completed_count,
        'total_hours': total_hours,
        'certificates_count': completed_count,  # Certificates = completed courses
        'in_progress_courses': in_progress_courses,
        'recommended_courses': recommended_courses,
        'categories': categories,
    }
    
    return render(request, 'student_home.html', context)


@login_required
def author_dashboard_view(request):
    """
    Author dashboard with courses, earnings, and analytics.
    Requires authentication.
    """
    # Set session role
    request.session['selected_role'] = 'AUTHOR'
    
    # Update user role to AUTHOR if not already
    if request.user.role != 'AUTHOR':
        request.user.role = 'AUTHOR'
        request.user.save()
    
    # Get author's courses
    all_courses = Course.objects.filter(
        author=request.user
    ).order_by('-created_at')
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
        price_paid__gt=0,
        course__author=request.user
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


@login_required
def admin_dashboard_view(request):
    """
    Admin dashboard with platform statistics and moderation queue.
    Requires staff access.
    """
    if not request.user.is_staff:
        return redirect('student_home')
    
    request.session['selected_role'] = 'ADMIN'
    
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


@login_required
def switch_to_instructor_view(request):
    """
    Switch user role from student to instructor/author.
    """
    if request.method == 'POST':
        request.user.role = 'AUTHOR'
        request.user.save()
        request.session['selected_role'] = 'AUTHOR'
        return redirect('author_home')
    return redirect('student_home')


# =============================================================================
# REGISTRATION VIEWS
# =============================================================================

def register_choice_view(request):
    """
    Registration method selection page.
    User chooses between phone OTP or email registration.
    """
    if request.user.is_authenticated:
        return redirect('student_home')
    return render(request, 'account/register_choice.html', {
        'otp_available': OTP_AVAILABLE
    })


def register_phone_view(request):
    """
    Phone registration - Step 1: Enter details and phone number.
    """
    if request.user.is_authenticated:
        return redirect('student_home')
    
    if not OTP_AVAILABLE:
        messages.error(request, "Phone registration is currently unavailable.")
        return redirect('register_choice')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data['phone_number']
            # Strip + for Redis key consistency with Bot
            phone_key = phone.replace('+', '')
            
            # Generate and store OTP and User Data
            otp_service = OtpService()
            
            # Save temp user data
            success, ttl = otp_service.save_user_temp(phone_key, form.cleaned_data)
            if not success:
                 messages.error(request, f"Please try again after {ttl} seconds.")
                 return render(request, 'account/register_phone.html', {'form': form})

            code = generate_code(6)
            otp_service.send_otp(phone_key, code, purpose='register')
            
            # Store phone in session for next step
            request.session['registration_phone'] = phone
            
            messages.success(request, f"OTP code sent to your Telegram. Please check your bot.")
            return redirect('register_verify_otp')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'account/register_phone.html', {'form': form})


def register_verify_otp_view(request):
    """
    Phone registration - Step 2: Verify OTP code and Create User.
    """
    if request.user.is_authenticated:
        return redirect('student_home')
    
    phone = request.session.get('registration_phone')
    if not phone:
        messages.error(request, "Please enter your details first.")
        return redirect('register_phone')
    
    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['otp_code']
            phone_key = phone.replace('+', '')
            
            # Verify OTP
            otp_service = OtpService()
            is_valid, user_data = otp_service.verify_otp(phone_key, code, purpose='register')
            
            if is_valid and user_data:
                # Create user
                try:
                    user = User.objects.create_user(
                        phone_number=user_data['phone_number'],
                        password=user_data['password1'],
                        first_name=user_data['first_name'],
                        last_name=user_data['last_name'],
                        age=user_data['age'],
                        phone_verified=True,
                        role=UserRole.STUDENT
                    )
                    
                    # Clean up session
                    if 'registration_phone' in request.session:
                        del request.session['registration_phone']
                    
                    # Clean up OTP
                    otp_service.delete_otp(phone_key, purpose='register')
                    
                    # Log the user in
                    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                    request.session['selected_role'] = 'STUDENT'
                    
                    messages.success(request, f"Welcome to IlmSpace, {user.first_name}!")
                    return redirect('student_home')
                except Exception as e:
                    messages.error(request, f"Error creating user: {e}")
            else:
                messages.error(request, "Invalid or expired OTP code. Please try again.")
    else:
        form = OTPVerificationForm()
    
    return render(request, 'account/register_verify_otp.html', {
        'form': form,
        'phone': phone
    })


def register_details_view(request):
    """
    Phone registration - Step 3: Enter user details.
    """
    if request.user.is_authenticated:
        return redirect('student_home')
    
    phone = request.session.get('registration_phone')
    otp_verified = request.session.get('otp_verified')
    
    if not phone or not otp_verified:
        messages.error(request, "Please complete phone verification first.")
        return redirect('register_phone')
    
    if request.method == 'POST':
        form = UserDetailsForm(request.POST)
        if form.is_valid():
            # Create user
            user = User.objects.create_user(
                phone_number=phone,
                password=form.cleaned_data['password1'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                age=form.cleaned_data['age'],
                phone_verified=True,
                role=UserRole.STUDENT
            )
            
            # Clean up session
            del request.session['registration_phone']
            del request.session['otp_verified']
            
            # Clean up OTP
            otp_service = OtpService()
            otp_service.delete_otp(phone, purpose='register')
            
            # Log the user in
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            request.session['selected_role'] = 'STUDENT'
            
            messages.success(request, f"Welcome to IlmSpace, {user.first_name}!")
            return redirect('student_home')
    else:
        form = UserDetailsForm()
    
    return render(request, 'account/register_details.html', {'form': form})


def register_email_view(request):
    """
    Email-based registration (alternative to phone OTP).
    """
    if request.user.is_authenticated:
        return redirect('student_home')
    
    if request.method == 'POST':
        form = EmailRegistrationForm(request.POST)
        if form.is_valid():
            # Generate placeholder phone number
            placeholder_phone = f"+998{str(uuid.uuid4().int)[:9]}"
            
            # Create user
            user = User.objects.create_user(
                phone_number=placeholder_phone,
                password=form.cleaned_data['password1'],
                email=form.cleaned_data['email'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                age=form.cleaned_data['age'],
                email_verified=True,
                role=UserRole.STUDENT
            )
            
            # Log the user in
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            request.session['selected_role'] = 'STUDENT'
            
            messages.success(request, f"Welcome to IlmSpace, {user.first_name}!")
            return redirect('student_home')
    else:
        form = EmailRegistrationForm()
    
    return render(request, 'account/register_email.html', {'form': form})


def login_phone_view(request):
    """
    Phone number login - sends OTP for verification.
    """
    if request.user.is_authenticated:
        return redirect('student_home')
    
    if not OTP_AVAILABLE:
        messages.error(request, "Phone login is currently unavailable.")
        return redirect('account_login')
    
    if request.method == 'POST':
        form = PhoneLoginForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data['phone_number']
            password = form.cleaned_data['password']
            
            # Check if user exists and password is correct
            try:
                user = User.objects.get(phone_number=phone)
                if not user.check_password(password):
                    messages.error(request, "Invalid phone number or password.")
                    return render(request, 'account/login_phone.html', {'form': form})
            except User.DoesNotExist:
                messages.error(request, "No account found with this phone number.")
                return render(request, 'account/login_phone.html', {'form': form})
            
            # Generate and send OTP
            otp_service = OtpService()
            code = generate_code(6)
            phone_key = phone.replace('+', '')
            otp_service.send_otp(phone_key, code, purpose='login')
            
            # Store phone in session
            request.session['login_phone'] = phone
            
            messages.success(request, "OTP code sent to your Telegram.")
            return redirect('login_verify_otp')
    else:
        form = PhoneLoginForm()
    
    return render(request, 'account/login_phone.html', {'form': form})


def login_verify_otp_view(request):
    """
    Phone login - Step 2: Verify OTP code.
    """
    if request.user.is_authenticated:
        return redirect('student_home')
    
    phone = request.session.get('login_phone')
    if not phone:
        messages.error(request, "Please enter your phone number first.")
        return redirect('login_phone')
    
    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['otp_code']
            phone_key = phone.replace('+', '')
            
            # Verify OTP
            otp_service = OtpService()
            is_valid, _ = otp_service.verify_otp(phone_key, code, purpose='login')
            
            if is_valid:
                # Get user and log them in
                try:
                    user = User.objects.get(phone_number=phone)
                    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                    request.session['selected_role'] = user.role or 'STUDENT'
                    
                    # Clean up
                    del request.session['login_phone']
                    otp_service.delete_otp(phone_key, purpose='login')
                    
                    messages.success(request, f"Welcome back, {user.first_name or 'User'}!")
                    return redirect('student_home')
                except User.DoesNotExist:
                    messages.error(request, "User not found.")
            else:
                messages.error(request, "Invalid or expired OTP code.")
    else:
        form = OTPVerificationForm()
    
    return render(request, 'account/login_verify_otp.html', {
        'form': form,
        'phone': phone
    })


# =============================================================================
# PROFILE VIEWS
# =============================================================================

@login_required
def profile_view(request):
    """
    User profile page - view and edit personal info.
    """
    return render(request, 'account/profile.html', {
        'user': request.user
    })


@login_required
def profile_edit_view(request):
    """
    Edit user profile.
    """
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=request.user)
    
    return render(request, 'account/profile_edit.html', {'form': form})
