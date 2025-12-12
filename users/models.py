"""
User models for IlmSpace platform.
Implements phone-based authentication with optional email and social auth.
"""
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.core.validators import RegexValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from .base import TimestampedModel, BaseModel


class UserRole(models.TextChoices):
    """User role choices following SRP - single responsibility for role definition."""
    STUDENT = 'STUDENT', _('Student')
    AUTHOR = 'AUTHOR', _('Author')
    ADMIN = 'ADMIN', _('Admin')


class UserManager(BaseUserManager):
    """
    Custom user manager for phone-based authentication.
    Implements Factory pattern for user creation.
    """
    
    def create_user(self, phone_number, password=None, **extra_fields):
        """Create and save a regular user with the given phone number and password."""
        if not phone_number:
            raise ValueError(_('The Phone Number field must be set'))
        
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, phone_number, password=None, **extra_fields):
        """Create and save a superuser with the given phone number and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', UserRole.ADMIN)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        
        return self.create_user(phone_number, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, TimestampedModel):
    """
    Custom User model with phone number as primary identifier.
    Supports multiple authentication methods (phone, Google, Telegram).
    Follows SRP - handles only user authentication and basic info.
    """
    
    # Phone validator for Uzbekistan format
    phone_regex = RegexValidator(
        regex=r'^\+998[0-9]{9}$',
        message=_("Phone number must be in format: '+998XXXXXXXXX'")
    )
    
    phone_number = models.CharField(
        _('phone number'),
        max_length=13,
        unique=True,
        validators=[phone_regex],
        help_text=_('Required. Format: +998XXXXXXXXX')
    )
    
    email = models.EmailField(
        _('email address'),
        blank=True,
        null=True,
        unique=True,
        help_text=_('Optional email address for login and notifications')
    )
    
    first_name = models.CharField(_('first name'), max_length=150, blank=True)
    last_name = models.CharField(_('last name'), max_length=150, blank=True)
    
    age = models.PositiveIntegerField(
        _('age'),
        null=True,
        blank=True,
        help_text=_('User age')
    )
    
    telegram_id = models.BigIntegerField(
        _('telegram ID'),
        null=True,
        blank=True,
        unique=True,
        help_text=_('Telegram user ID for bot notifications')
    )
    
    role = models.CharField(
        _('role'),
        max_length=10,
        choices=UserRole.choices,
        default=UserRole.STUDENT,
        help_text=_('User role in the platform')
    )
    
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into admin site.')
    )
    
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_('Designates whether this user should be treated as active.')
    )
    
    phone_verified = models.BooleanField(
        _('phone verified'),
        default=False,
        help_text=_('Designates whether phone number has been verified.')
    )
    
    email_verified = models.BooleanField(
        _('email verified'),
        default=False,
        help_text=_('Designates whether email has been verified.')
    )
    
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    last_login = models.DateTimeField(_('last login'), blank=True, null=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []  # No additional required fields for createsuperuser
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        db_table = 'users'
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['phone_number']),
            models.Index(fields=['email']),
            models.Index(fields=['role']),
        ]
    
    def __str__(self):
        return self.phone_number
    
    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        full_name = f'{self.first_name} {self.last_name}'.strip()
        return full_name or self.phone_number
    
    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name or self.phone_number


class PhoneVerification(BaseModel):
    """
    OTP verification for phone numbers.
    Follows SRP - handles only phone verification logic.
    Dependency Inversion - doesn't depend on specific SMS provider.
    """
    
    phone_number = models.CharField(
        _('phone number'),
        max_length=13,
        validators=[User.phone_regex],
        db_index=True
    )
    
    otp_code = models.CharField(
        _('OTP code'),
        max_length=6,
        help_text=_('6-digit verification code')
    )
    
    is_verified = models.BooleanField(
        _('verified'),
        default=False,
        help_text=_('Whether the OTP has been successfully verified')
    )
    
    expires_at = models.DateTimeField(
        _('expires at'),
        help_text=_('When this OTP expires')
    )
    
    attempts = models.PositiveSmallIntegerField(
        _('verification attempts'),
        default=0,
        help_text=_('Number of verification attempts made')
    )
    
    MAX_ATTEMPTS = 3
    OTP_VALIDITY_MINUTES = 5
    
    class Meta:
        verbose_name = _('phone verification')
        verbose_name_plural = _('phone verifications')
        db_table = 'phone_verifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['phone_number', '-created_at']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"{self.phone_number} - {self.otp_code}"
    
    def is_valid(self):
        """Check if OTP is still valid (not expired and not max attempts)."""
        return (
            not self.is_verified and
            self.attempts < self.MAX_ATTEMPTS and
            timezone.now() < self.expires_at and
            not self.is_deleted
        )
    
    def verify(self, code):
        """Verify the OTP code."""
        self.attempts += 1
        self.save()
        
        if not self.is_valid():
            return False
        
        if self.otp_code == code:
            self.is_verified = True
            self.save()
            return True
        
        return False


class SocialAuthProvider(models.TextChoices):
    """Social authentication provider choices."""
    GOOGLE = 'GOOGLE', _('Google')
    TELEGRAM = 'TELEGRAM', _('Telegram')


class SocialAuth(BaseModel):
    """
    Links social authentication providers to users.
    Allows multiple providers per user.
    Follows Open/Closed Principle - easy to add new providers.
    """
    
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='social_auths',
        verbose_name=_('user')
    )
    
    provider = models.CharField(
        _('provider'),
        max_length=20,
        choices=SocialAuthProvider.choices,
        help_text=_('Social authentication provider')
    )
    
    provider_user_id = models.CharField(
        _('provider user ID'),
        max_length=255,
        help_text=_('Unique user ID from the provider')
    )
    
    access_token = models.TextField(
        _('access token'),
        blank=True,
        help_text=_('OAuth access token (encrypted in production)')
    )
    
    refresh_token = models.TextField(
        _('refresh token'),
        blank=True,
        help_text=_('OAuth refresh token (encrypted in production)')
    )
    
    token_expires_at = models.DateTimeField(
        _('token expires at'),
        null=True,
        blank=True,
        help_text=_('When the access token expires')
    )
    
    extra_data = models.JSONField(
        _('extra data'),
        default=dict,
        blank=True,
        help_text=_('Additional data from provider (profile info, etc.)')
    )
    
    class Meta:
        verbose_name = _('social authentication')
        verbose_name_plural = _('social authentications')
        db_table = 'social_auths'
        unique_together = [['provider', 'provider_user_id']]
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'provider']),
            models.Index(fields=['provider', 'provider_user_id']),
        ]
    
    def __str__(self):
        return f"{self.user.phone_number} - {self.provider}"
