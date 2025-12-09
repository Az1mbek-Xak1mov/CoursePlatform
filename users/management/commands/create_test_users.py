"""
Management command to create test users for each role.
Usage: python manage.py create_test_users
"""
from django.core.management.base import BaseCommand
from users.models import User, UserRole
from authors.models import AuthorProfile, AuthorBalance
from students.models import StudentProfile
from courses.models import Course, Category, CourseEnrollment
from decimal import Decimal


class Command(BaseCommand):
    help = 'Create test users for Student, Author, and Admin roles'

    def handle(self, *args, **options):
        self.stdout.write('Creating test users...')
        
        # Create Student
        try:
            student = User.objects.create_user(
                phone_number='+998901234567',
                password='test123',
                first_name='Student',
                last_name='Test',
                role=UserRole.STUDENT,
                phone_verified=True
            )
            StudentProfile.objects.create(user=student)
            self.stdout.write(self.style.SUCCESS(f'✓ Created student: {student.phone_number} / test123'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Student already exists or error: {e}'))
        
        # Create Author
        try:
            author = User.objects.create_user(
                phone_number='+998901234568',
                password='test123',
                first_name='Author',
                last_name='Test',
                role=UserRole.AUTHOR,
                phone_verified=True
            )
            AuthorProfile.objects.create(
                user=author,
                bio='Experienced instructor',
                is_verified=True
            )
            AuthorBalance.objects.create(
                author=author,
                available_balance=Decimal('5000000.00'),
                lifetime_earnings=Decimal('10000000.00')
            )
            self.stdout.write(self.style.SUCCESS(f'✓ Created author: {author.phone_number} / test123'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Author already exists or error: {e}'))
        
        # Create Admin
        try:
            admin = User.objects.create_superuser(
                phone_number='+998901234569',
                password='test123',
                first_name='Admin',
                last_name='Test',
                role=UserRole.ADMIN
            )
            self.stdout.write(self.style.SUCCESS(f'✓ Created admin: {admin.phone_number} / test123'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Admin already exists or error: {e}'))
        
        self.stdout.write(self.style.SUCCESS('\n=== Test Users Created ==='))
        self.stdout.write('Student: +998901234567 / test123')
        self.stdout.write('Author:  +998901234568 / test123')
        self.stdout.write('Admin:   +998901234569 / test123')
