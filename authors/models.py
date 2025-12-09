"""
Author models for IlmSpace platform.
Manages author profiles, earnings, and payouts.
"""
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from users.base import BaseModel
from decimal import Decimal


class AuthorProfile(BaseModel):
    """
    Extended profile for course authors.
    Follows SRP - manages author-specific information.
    """
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='author_profile',
        verbose_name=_('user'),
        limit_choices_to={'role': 'AUTHOR'}
    )
    
    bio = models.TextField(
        _('bio'),
        blank=True,
        help_text=_('Author biography and expertise')
    )
    
    profile_picture = models.ImageField(
        _('profile picture'),
        upload_to='authors/profiles/',
        blank=True,
        null=True,
        help_text=_('Author profile picture')
    )
    
    expertise = models.CharField(
        _('expertise'),
        max_length=255,
        blank=True,
        help_text=_('Areas of expertise (comma-separated)')
    )
    
    website = models.URLField(
        _('website'),
        blank=True,
        help_text=_('Personal or professional website')
    )
    
    linkedin_url = models.URLField(
        _('LinkedIn'),
        blank=True,
        help_text=_('LinkedIn profile URL')
    )
    
    telegram_username = models.CharField(
        _('Telegram username'),
        max_length=100,
        blank=True,
        help_text=_('Telegram username without @')
    )
    
    youtube_url = models.URLField(
        _('YouTube'),
        blank=True,
        help_text=_('YouTube channel URL')
    )
    
    is_verified = models.BooleanField(
        _('verified'),
        default=False,
        help_text=_('Whether author is verified by platform')
    )
    
    verified_at = models.DateTimeField(
        _('verified at'),
        null=True,
        blank=True,
        help_text=_('When author was verified')
    )
    
    # Statistics (denormalized for performance)
    total_students = models.PositiveIntegerField(
        _('total students'),
        default=0,
        help_text=_('Total students across all courses')
    )
    
    total_courses = models.PositiveIntegerField(
        _('total courses'),
        default=0,
        help_text=_('Total published courses')
    )
    
    average_rating = models.DecimalField(
        _('average rating'),
        max_digits=3,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text=_('Average rating across all courses')
    )
    
    class Meta:
        verbose_name = _('author profile')
        verbose_name_plural = _('author profiles')
        db_table = 'author_profiles'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['is_verified']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - Author Profile"


class AuthorBalance(BaseModel):
    """
    Tracks author financial balance.
    Follows SRP - manages balance tracking only.
    """
    
    author = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='author_balance',
        verbose_name=_('author'),
        limit_choices_to={'role': 'AUTHOR'}
    )
    
    available_balance = models.DecimalField(
        _('available balance'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text=_('Balance available for withdrawal in UZS')
    )
    
    pending_balance = models.DecimalField(
        _('pending balance'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text=_('Balance pending (not yet available for withdrawal) in UZS')
    )
    
    lifetime_earnings = models.DecimalField(
        _('lifetime earnings'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text=_('Total earnings all-time in UZS')
    )
    
    total_withdrawn = models.DecimalField(
        _('total withdrawn'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text=_('Total amount withdrawn in UZS')
    )
    
    class Meta:
        verbose_name = _('author balance')
        verbose_name_plural = _('author balances')
        db_table = 'author_balances'
        indexes = [
            models.Index(fields=['author']),
        ]
    
    def __str__(self):
        return f"{self.author.get_full_name()} - Balance: {self.available_balance} UZS"


class PayoutStatus(models.TextChoices):
    """Payout request status choices."""
    PENDING = 'PENDING', _('Pending')
    PROCESSING = 'PROCESSING', _('Processing')
    COMPLETED = 'COMPLETED', _('Completed')
    FAILED = 'FAILED', _('Failed')
    REJECTED = 'REJECTED', _('Rejected')


class PayoutMethod(models.TextChoices):
    """Available payout methods."""
    BANK_TRANSFER = 'BANK_TRANSFER', _('Bank Transfer')
    CLICK = 'CLICK', _('Click')
    PAYME = 'PAYME', _('Payme')
    UZUM = 'UZUM', _('Uzum Pay')


class AuthorPayout(BaseModel):
    """
    Author payout requests and history.
    Follows SRP - manages payout requests only.
    """
    
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payouts',
        verbose_name=_('author'),
        limit_choices_to={'role': 'AUTHOR'}
    )
    
    amount = models.DecimalField(
        _('amount'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text=_('Payout amount in UZS')
    )
    
    method = models.CharField(
        _('payout method'),
        max_length=20,
        choices=PayoutMethod.choices,
        help_text=_('Method for receiving payout')
    )
    
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=PayoutStatus.choices,
        default=PayoutStatus.PENDING,
        help_text=_('Payout request status')
    )
    
    # Payment details (stored as JSON for flexibility)
    payment_details = models.JSONField(
        _('payment details'),
        default=dict,
        help_text=_('Bank account, card number, or wallet info')
    )
    
    # Admin processing
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_payouts',
        verbose_name=_('processed by'),
        limit_choices_to={'role': 'ADMIN'}
    )
    
    processed_at = models.DateTimeField(
        _('processed at'),
        null=True,
        blank=True,
        help_text=_('When payout was processed')
    )
    
    transaction_id = models.CharField(
        _('transaction ID'),
        max_length=255,
        blank=True,
        help_text=_('External transaction reference')
    )
    
    notes = models.TextField(
        _('notes'),
        blank=True,
        help_text=_('Admin notes or rejection reason')
    )
    
    class Meta:
        verbose_name = _('author payout')
        verbose_name_plural = _('author payouts')
        db_table = 'author_payouts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['author', '-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.author.get_full_name()} - {self.amount} UZS ({self.status})"
