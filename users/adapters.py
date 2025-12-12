"""
Custom adapters for django-allauth to work with our custom User model.
"""
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
import uuid


class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Custom account adapter to handle user creation with phone-based User model.
    """
    
    def populate_user(self, request, sociallogin, data):
        """
        Populate user instance with data from social login.
        Override to handle our custom User model without username.
        """
        user = super().populate_user(request, sociallogin, data)
        # Generate a placeholder phone number
        user.phone_number = f"+998{str(uuid.uuid4().int)[:9]}"
        return user
    
    def save_user(self, request, user, form, commit=True):
        """
        Save a new user from signup form.
        Generate a placeholder phone number for email-based signups.
        """
        user = super().save_user(request, user, form, commit=False)
        
        # Generate a placeholder phone number if not provided
        if not user.phone_number:
            # Generate unique placeholder phone number
            user.phone_number = f"+998{str(uuid.uuid4().int)[:9]}"
        
        # Set email as verified since they signed up with email
        user.email_verified = True
        
        # Set default role to STUDENT
        user.role = 'STUDENT'
        
        if commit:
            user.save()
        
        return user
    
    def get_login_redirect_url(self, request):
        """
        Return URL to redirect to after login.
        Always redirect to student dashboard after login.
        """
        # Set session role to STUDENT by default
        request.session['selected_role'] = 'STUDENT'
        return '/student/'


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom social account adapter for Google OAuth.
    """
    
    def populate_user(self, request, sociallogin, data):
        """
        Populate user instance with data from social login.
        Override to handle our custom User model without username.
        """
        user = sociallogin.user
        # Set user data from social account
        user.email = data.get('email', '')
        user.first_name = data.get('first_name', '')
        user.last_name = data.get('last_name', '')
        # Generate a placeholder phone number
        user.phone_number = f"+998{str(uuid.uuid4().int)[:9]}"
        # Set default role to STUDENT
        user.role = 'STUDENT'
        return user
    
    def save_user(self, request, sociallogin, form=None):
        """
        Save a new user from social login (Google).
        """
        user = sociallogin.user
        
        # Ensure phone number is set
        if not user.phone_number:
            user.phone_number = f"+998{str(uuid.uuid4().int)[:9]}"
        
        # Set default role to STUDENT
        user.role = 'STUDENT'
        
        # Set email as verified for Google signups
        if sociallogin.account.provider == 'google':
            user.email_verified = True
        
        user.save()
        sociallogin.save(request)
        
        # Set session role to STUDENT
        request.session['selected_role'] = 'STUDENT'
        
        return user
    
    def pre_social_login(self, request, sociallogin):
        """
        Hook called before social login is processed.
        Link social account to existing user if email matches.
        """
        # Check if email already exists
        email = sociallogin.account.extra_data.get('email')
        if email:
            from users.models import User
            try:
                existing_user = User.objects.get(email=email)
                # Connect social account to existing user
                sociallogin.connect(request, existing_user)
                # Set session role
                request.session['selected_role'] = existing_user.role or 'STUDENT'
            except User.DoesNotExist:
                pass
    
    def get_login_redirect_url(self, request, socialaccount):
        """
        Return URL to redirect to after social login.
        """
        request.session['selected_role'] = 'STUDENT'
        return '/student/'
    
    def get_connect_redirect_url(self, request, socialaccount):
        """
        Return URL to redirect to after connecting social account.
        """
        return '/student/'
