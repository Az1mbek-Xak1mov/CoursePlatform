"""
Payment models for IlmSpace platform.
Handles transactions, payment gateways, and financial operations.
"""
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from users.base import BaseModel
from decimal import Decimal


class PaymentGateway(models.TextChoices):
    """Available payment gateways in Uzbekistan."""
    CLICK = 'CLICK', _('Click')
    PAYME = 'PAYME', _('Payme')
    UZUM = 'UZUM', _('Uzum Pay')


class TransactionStatus(models.TextChoices):
    """Transaction status choices."""
    PENDING = 'PENDING', _('Pending')
    SUCCESS = 'SUCCESS', _('Success')
    FAILED = 'FAILED', _('Failed')
    REFUNDED = 'REFUNDED', _('Refunded')
    CANCELLED = 'CANCELLED', _('Cancelled')


class TransactionType(models.TextChoices):
    """Transaction type choices."""
    COURSE_PURCHASE = 'COURSE_PURCHASE', _('Course Purchase')
    REFUND = 'REFUND', _('Refund')
    AUTHOR_PAYOUT = 'AUTHOR_PAYOUT', _('Author Payout')


class Transaction(BaseModel):
    """
    All financial transactions in the platform.
    Follows SRP - manages transaction records only.
    Dependency Inversion - doesn't depend on specific payment gateway implementations.
    """
    
    transaction_id = models.CharField(
        _('transaction ID'),
        max_length=100,
        unique=True,
        db_index=True,
        help_text=_('Unique transaction identifier')
    )
    
    transaction_type = models.CharField(
        _('transaction type'),
        max_length=20,
        choices=TransactionType.choices,
        default=TransactionType.COURSE_PURCHASE,
        help_text=_('Type of transaction')
    )
    
    # Parties involved
    payer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='payments_made',
        verbose_name=_('payer'),
        help_text=_('User who made the payment')
    )
    
    payee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='payments_received',
        verbose_name=_('payee'),
        help_text=_('User receiving the payment (author or platform)')
    )
    
    # Financial details
    amount = models.DecimalField(
        _('amount'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text=_('Transaction amount in UZS')
    )
    
    currency = models.CharField(
        _('currency'),
        max_length=3,
        default='UZS',
        help_text=_('Currency code')
    )
    
    # Payment gateway
    gateway = models.CharField(
        _('payment gateway'),
        max_length=20,
        choices=PaymentGateway.choices,
        help_text=_('Payment gateway used')
    )
    
    gateway_transaction_id = models.CharField(
        _('gateway transaction ID'),
        max_length=255,
        blank=True,
        help_text=_('Transaction ID from payment gateway')
    )
    
    # Status tracking
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=TransactionStatus.choices,
        default=TransactionStatus.PENDING,
        help_text=_('Transaction status')
    )
    
    # Related objects
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name=_('course'),
        help_text=_('Course being purchased (if applicable)')
    )
    
    enrollment = models.ForeignKey(
        'courses.CourseEnrollment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name=_('enrollment'),
        help_text=_('Related enrollment record')
    )
    
    # Additional data
    metadata = models.JSONField(
        _('metadata'),
        default=dict,
        blank=True,
        help_text=_('Additional transaction data from gateway')
    )
    
    error_message = models.TextField(
        _('error message'),
        blank=True,
        help_text=_('Error message if transaction failed')
    )
    
    completed_at = models.DateTimeField(
        _('completed at'),
        null=True,
        blank=True,
        help_text=_('When transaction completed successfully')
    )
    
    class Meta:
        verbose_name = _('transaction')
        verbose_name_plural = _('transactions')
        db_table = 'transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['payer', '-created_at']),
            models.Index(fields=['payee', '-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['gateway']),
            models.Index(fields=['course']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.transaction_id} - {self.amount} {self.currency} ({self.status})"
    
    def save(self, *args, **kwargs):
        if not self.transaction_id:
            # Generate unique transaction ID
            import uuid
            from django.utils import timezone
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            self.transaction_id = f"TXN-{timestamp}-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)


class PaymentGatewayConfig(BaseModel):
    """
    Configuration for payment gateways.
    Follows Open/Closed - easy to add new gateways.
    """
    
    gateway = models.CharField(
        _('gateway'),
        max_length=20,
        choices=PaymentGateway.choices,
        unique=True,
        help_text=_('Payment gateway name')
    )
    
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_('Whether this gateway is currently active')
    )
    
    # Credentials (should be encrypted in production)
    merchant_id = models.CharField(
        _('merchant ID'),
        max_length=255,
        blank=True,
        help_text=_('Merchant/Vendor ID')
    )
    
    secret_key = models.CharField(
        _('secret key'),
        max_length=255,
        blank=True,
        help_text=_('API secret key (encrypt in production!)')
    )
    
    api_url = models.URLField(
        _('API URL'),
        blank=True,
        help_text=_('Payment gateway API endpoint')
    )
    
    # Configuration
    config = models.JSONField(
        _('configuration'),
        default=dict,
        blank=True,
        help_text=_('Additional gateway-specific settings')
    )
    
    # Commission
    commission_percentage = models.DecimalField(
        _('commission percentage'),
        max_digits=5,
        decimal_places=2,
        default=Decimal('2.00'),
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))],
        help_text=_('Gateway commission percentage')
    )
    
    class Meta:
        verbose_name = _('payment gateway config')
        verbose_name_plural = _('payment gateway configs')
        db_table = 'payment_gateway_configs'
        indexes = [
            models.Index(fields=['gateway']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.gateway} ({'Active' if self.is_active else 'Inactive'})"


class PlatformCommission(BaseModel):
    """
    Platform commission rates for courses.
    Follows SRP - manages commission calculation rules.
    """
    
    # Commission can be set per course, category, or globally
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='commission_rules',
        verbose_name=_('course'),
        help_text=_('Specific course (optional)')
    )
    
    category = models.ForeignKey(
        'courses.Category',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='commission_rules',
        verbose_name=_('category'),
        help_text=_('Specific category (optional)')
    )
    
    commission_percentage = models.DecimalField(
        _('commission percentage'),
        max_digits=5,
        decimal_places=2,
        default=Decimal('30.00'),
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))],
        help_text=_('Platform commission percentage')
    )
    
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_('Whether this commission rule is active')
    )
    
    effective_from = models.DateTimeField(
        _('effective from'),
        help_text=_('When this commission rate becomes effective')
    )
    
    effective_until = models.DateTimeField(
        _('effective until'),
        null=True,
        blank=True,
        help_text=_('When this commission rate expires (null = no expiry)')
    )
    
    notes = models.TextField(
        _('notes'),
        blank=True,
        help_text=_('Internal notes about this commission rule')
    )
    
    class Meta:
        verbose_name = _('platform commission')
        verbose_name_plural = _('platform commissions')
        db_table = 'platform_commissions'
        ordering = ['-effective_from']
        indexes = [
            models.Index(fields=['course', 'is_active']),
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['effective_from']),
        ]
    
    def __str__(self):
        if self.course:
            return f"{self.course.title} - {self.commission_percentage}%"
        elif self.category:
            return f"{self.category.name} - {self.commission_percentage}%"
        else:
            return f"Default - {self.commission_percentage}%"


class RefundStatus(models.TextChoices):
    """Refund request status."""
    PENDING = 'PENDING', _('Pending')
    APPROVED = 'APPROVED', _('Approved')
    REJECTED = 'REJECTED', _('Rejected')
    COMPLETED = 'COMPLETED', _('Completed')


class RefundRequest(BaseModel):
    """
    Student refund requests.
    Follows SRP - manages refund workflow.
    """
    
    enrollment = models.ForeignKey(
        'courses.CourseEnrollment',
        on_delete=models.CASCADE,
        related_name='refund_requests',
        verbose_name=_('enrollment')
    )
    
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='refund_requests',
        verbose_name=_('student'),
        limit_choices_to={'role': 'STUDENT'}
    )
    
    original_transaction = models.ForeignKey(
        Transaction,
        on_delete=models.SET_NULL,
        null=True,
        related_name='refund_requests',
        verbose_name=_('original transaction')
    )
    
    amount = models.DecimalField(
        _('refund amount'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text=_('Amount to refund in UZS')
    )
    
    reason = models.TextField(
        _('reason'),
        help_text=_('Student reason for requesting refund')
    )
    
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=RefundStatus.choices,
        default=RefundStatus.PENDING,
        help_text=_('Refund request status')
    )
    
    # Admin processing
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_refunds',
        verbose_name=_('reviewed by'),
        limit_choices_to={'role': 'ADMIN'}
    )
    
    reviewed_at = models.DateTimeField(
        _('reviewed at'),
        null=True,
        blank=True,
        help_text=_('When refund was reviewed')
    )
    
    admin_notes = models.TextField(
        _('admin notes'),
        blank=True,
        help_text=_('Admin notes or rejection reason')
    )
    
    refund_transaction = models.ForeignKey(
        Transaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='refund_for',
        verbose_name=_('refund transaction')
    )
    
    class Meta:
        verbose_name = _('refund request')
        verbose_name_plural = _('refund requests')
        db_table = 'refund_requests'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['student', '-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['enrollment']),
        ]
    
    def __str__(self):
        return f"Refund: {self.student.get_full_name()} - {self.enrollment.course.title}"
