"""
Admin configuration for Payments app.
Comprehensive admin interface using Django Jazzmin.
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import (
    Transaction,
    TransactionStatus,
    TransactionType,
    PaymentGatewayConfig,
    PlatformCommission,
    RefundRequest,
    RefundStatus,
)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """Transaction admin with comprehensive financial tracking."""
    
    list_display = (
        'transaction_id',
        'transaction_type',
        'payer_link',
        'payee_link',
        'amount_display',
        'gateway',
        'status_badge',
        'created_at',
    )
    
    list_filter = (
        'status',
        'transaction_type',
        'gateway',
        'created_at',
    )
    
    search_fields = (
        'transaction_id',
        'gateway_transaction_id',
        'payer__first_name',
        'payer__last_name',
        'payer__phone_number',
        'payee__first_name',
        'payee__last_name',
        'course__title',
    )
    
    raw_id_fields = ('payer', 'payee', 'course', 'enrollment')
    readonly_fields = (
        'transaction_id',
        'created_at',
        'updated_at',
        'completed_at',
    )
    date_hierarchy = 'created_at'
    
    list_per_page = 30
    
    fieldsets = (
        (_('Transaction Info'), {
            'fields': ('transaction_id', 'transaction_type', 'status')
        }),
        (_('Parties'), {
            'fields': ('payer', 'payee')
        }),
        (_('Financial'), {
            'fields': ('amount', 'currency', 'gateway', 'gateway_transaction_id')
        }),
        (_('Related'), {
            'fields': ('course', 'enrollment'),
            'classes': ('collapse',),
        }),
        (_('Additional'), {
            'fields': ('metadata', 'error_message'),
            'classes': ('collapse',),
        }),
        (_('Dates'), {
            'fields': ('completed_at', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    actions = ['mark_success', 'mark_failed']
    
    def payer_link(self, obj):
        if obj.payer:
            return format_html(
                '<a href="/admin/users/user/{}/change/">{}</a>',
                obj.payer.id,
                obj.payer.get_full_name() or obj.payer.phone_number
            )
        return '-'
    payer_link.short_description = _('Payer')
    
    def payee_link(self, obj):
        if obj.payee:
            return format_html(
                '<a href="/admin/users/user/{}/change/">{}</a>',
                obj.payee.id,
                obj.payee.get_full_name() or obj.payee.phone_number
            )
        return '-'
    payee_link.short_description = _('Payee')
    
    def amount_display(self, obj):
        color = 'green' if obj.status == TransactionStatus.SUCCESS else 'inherit'
        return format_html(
            '<strong style="color: {};">{:,.0f} {}</strong>',
            color,
            obj.amount,
            obj.currency
        )
    amount_display.short_description = _('Amount')
    amount_display.admin_order_field = 'amount'
    
    def status_badge(self, obj):
        """Display status with colored badge."""
        colors = {
            TransactionStatus.PENDING: 'warning',
            TransactionStatus.SUCCESS: 'success',
            TransactionStatus.FAILED: 'danger',
            TransactionStatus.REFUNDED: 'info',
            TransactionStatus.CANCELLED: 'dark',
        }
        color = colors.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = _('Status')
    status_badge.admin_order_field = 'status'
    
    @admin.action(description=_('Mark as Success'))
    def mark_success(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(status=TransactionStatus.PENDING).update(
            status=TransactionStatus.SUCCESS,
            completed_at=timezone.now()
        )
        self.message_user(request, f'{updated} transactions marked as success.')
    
    @admin.action(description=_('Mark as Failed'))
    def mark_failed(self, request, queryset):
        updated = queryset.filter(status=TransactionStatus.PENDING).update(
            status=TransactionStatus.FAILED
        )
        self.message_user(request, f'{updated} transactions marked as failed.')


@admin.register(PaymentGatewayConfig)
class PaymentGatewayConfigAdmin(admin.ModelAdmin):
    """Payment gateway configuration admin."""
    
    list_display = (
        'gateway',
        'is_active_badge',
        'merchant_id',
        'commission_percentage_display',
        'updated_at',
    )
    
    list_filter = ('is_active', 'gateway')
    search_fields = ('gateway', 'merchant_id')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (_('Gateway'), {
            'fields': ('gateway', 'is_active')
        }),
        (_('Credentials'), {
            'fields': ('merchant_id', 'secret_key', 'api_url'),
            'classes': ('collapse',),
        }),
        (_('Configuration'), {
            'fields': ('config', 'commission_percentage')
        }),
        (_('Dates'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span class="badge badge-success">{}</span>', 'Active')
        return format_html('<span class="badge badge-danger">{}</span>', 'Inactive')
    is_active_badge.short_description = _('Status')
    is_active_badge.admin_order_field = 'is_active'
    
    def commission_percentage_display(self, obj):
        return f"{obj.commission_percentage:.2f}%"
    commission_percentage_display.short_description = _('Commission')


@admin.register(PlatformCommission)
class PlatformCommissionAdmin(admin.ModelAdmin):
    """Platform commission admin."""
    
    list_display = (
        '__str__',
        'commission_percentage_display',
        'is_active_badge',
        'effective_from',
        'effective_until',
    )
    
    list_filter = ('is_active', 'effective_from')
    search_fields = ('course__title', 'category__name', 'notes')
    raw_id_fields = ('course', 'category')
    readonly_fields = ('created_at', 'updated_at')
    
    def commission_percentage_display(self, obj):
        return format_html(
            '<strong style="color: #007bff;">{}%</strong>',
            f"{obj.commission_percentage:.2f}"
        )
    commission_percentage_display.short_description = _('Commission')
    
    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span class="badge badge-success">{}</span>', 'Active')
        return format_html('<span class="badge badge-secondary">{}</span>', 'Inactive')
    is_active_badge.short_description = _('Status')


@admin.register(RefundRequest)
class RefundRequestAdmin(admin.ModelAdmin):
    """Refund request admin with approval workflow."""
    
    list_display = (
        'student_display',
        'course_display',
        'amount_display',
        'status_badge',
        'reviewed_by',
        'created_at',
    )
    
    list_filter = ('status', 'created_at', 'reviewed_at')
    
    search_fields = (
        'student__first_name',
        'student__last_name',
        'student__phone_number',
        'enrollment__course__title',
        'reason',
    )
    
    raw_id_fields = ('enrollment', 'student', 'original_transaction', 'reviewed_by', 'refund_transaction')
    readonly_fields = ('created_at', 'updated_at', 'reviewed_at')
    date_hierarchy = 'created_at'
    
    list_per_page = 25
    
    fieldsets = (
        (_('Request Details'), {
            'fields': ('enrollment', 'student', 'amount', 'reason')
        }),
        (_('Status'), {
            'fields': ('status',)
        }),
        (_('Review'), {
            'fields': ('reviewed_by', 'reviewed_at', 'admin_notes')
        }),
        (_('Transactions'), {
            'fields': ('original_transaction', 'refund_transaction'),
            'classes': ('collapse',),
        }),
        (_('Dates'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    actions = ['approve_refunds', 'reject_refunds']
    
    def student_display(self, obj):
        return format_html(
            '<a href="/admin/users/user/{}/change/">{}</a>',
            obj.student.id,
            obj.student.get_full_name() or obj.student.phone_number
        )
    student_display.short_description = _('Student')
    
    def course_display(self, obj):
        return format_html(
            '<a href="/admin/courses/course/{}/change/">{}</a>',
            obj.enrollment.course.id,
            obj.enrollment.course.title[:30] + '...' if len(obj.enrollment.course.title) > 30 else obj.enrollment.course.title
        )
    course_display.short_description = _('Course')
    
    def amount_display(self, obj):
        return format_html('<strong>{:,.0f} UZS</strong>', obj.amount)
    amount_display.short_description = _('Amount')
    amount_display.admin_order_field = 'amount'
    
    def status_badge(self, obj):
        """Display status with colored badge."""
        colors = {
            RefundStatus.PENDING: 'warning',
            RefundStatus.APPROVED: 'info',
            RefundStatus.REJECTED: 'danger',
            RefundStatus.COMPLETED: 'success',
        }
        color = colors.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = _('Status')
    status_badge.admin_order_field = 'status'
    
    @admin.action(description=_('Approve selected refunds'))
    def approve_refunds(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(status=RefundStatus.PENDING).update(
            status=RefundStatus.APPROVED,
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f'{updated} refunds approved.')
    
    @admin.action(description=_('Reject selected refunds'))
    def reject_refunds(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(status=RefundStatus.PENDING).update(
            status=RefundStatus.REJECTED,
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f'{updated} refunds rejected.')
