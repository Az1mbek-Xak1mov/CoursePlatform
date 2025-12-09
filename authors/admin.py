"""
Admin configuration for Authors app.
Comprehensive admin interface using Django Jazzmin.
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import (
    AuthorProfile, 
    AuthorBalance, 
    AuthorPayout,
    PayoutStatus,
)


@admin.register(AuthorProfile)
class AuthorProfileAdmin(admin.ModelAdmin):
    """Author profile admin with detailed author management."""
    
    list_display = (
        'user_display',
        'is_verified_badge',
        'total_courses',
        'total_students',
        'average_rating_display',
        'created_at',
    )
    
    list_filter = ('is_verified', 'created_at')
    
    search_fields = (
        'user__first_name',
        'user__last_name',
        'user__phone_number',
        'user__email',
        'expertise',
    )
    
    raw_id_fields = ('user',)
    readonly_fields = (
        'total_students',
        'total_courses',
        'average_rating',
        'verified_at',
        'created_at',
        'updated_at',
    )
    
    list_per_page = 25
    
    fieldsets = (
        (_('User Information'), {
            'fields': ('user',)
        }),
        (_('Profile'), {
            'fields': ('bio', 'profile_picture', 'expertise')
        }),
        (_('Social Links'), {
            'fields': ('website', 'linkedin_url', 'telegram_username', 'youtube_url'),
            'classes': ('collapse',),
        }),
        (_('Verification'), {
            'fields': ('is_verified', 'verified_at')
        }),
        (_('Statistics'), {
            'fields': ('total_students', 'total_courses', 'average_rating'),
            'classes': ('collapse',),
        }),
        (_('Dates'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    actions = ['verify_authors', 'unverify_authors']
    
    def user_display(self, obj):
        """Display user with link."""
        return format_html(
            '<a href="/admin/users/user/{}/change/">{}</a>',
            obj.user.id,
            obj.user.get_full_name() or obj.user.phone_number
        )
    user_display.short_description = _('Author')
    user_display.admin_order_field = 'user__first_name'
    
    def is_verified_badge(self, obj):
        """Display verification status with badge."""
        if obj.is_verified:
            return format_html('<span class="badge badge-success">{}</span>', '✓ Verified')
        return format_html('<span class="badge badge-secondary">{}</span>', 'Not Verified')
    is_verified_badge.short_description = _('Verified')
    is_verified_badge.admin_order_field = 'is_verified'
    
    def average_rating_display(self, obj):
        """Display rating with stars."""
        if obj.average_rating > 0:
            stars = '★' * int(obj.average_rating) + '☆' * (5 - int(obj.average_rating))
            return f"{obj.average_rating:.2f} {stars}"
        return _('No ratings')
    average_rating_display.short_description = _('Rating')
    average_rating_display.admin_order_field = 'average_rating'
    
    @admin.action(description=_('Verify selected authors'))
    def verify_authors(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(is_verified=True, verified_at=timezone.now())
        self.message_user(request, f'{updated} authors verified.')
    
    @admin.action(description=_('Remove verification from selected authors'))
    def unverify_authors(self, request, queryset):
        updated = queryset.update(is_verified=False, verified_at=None)
        self.message_user(request, f'{updated} authors unverified.')


@admin.register(AuthorBalance)
class AuthorBalanceAdmin(admin.ModelAdmin):
    """Author balance admin for financial tracking."""
    
    list_display = (
        'author_display',
        'available_balance_display',
        'pending_balance_display',
        'lifetime_earnings_display',
        'total_withdrawn_display',
    )
    
    search_fields = (
        'author__first_name',
        'author__last_name',
        'author__phone_number',
    )
    
    raw_id_fields = ('author',)
    readonly_fields = (
        'lifetime_earnings',
        'total_withdrawn',
        'created_at',
        'updated_at',
    )
    
    list_per_page = 25
    
    def author_display(self, obj):
        return format_html(
            '<a href="/admin/users/user/{}/change/">{}</a>',
            obj.author.id,
            obj.author.get_full_name() or obj.author.phone_number
        )
    author_display.short_description = _('Author')
    
    def available_balance_display(self, obj):
        return format_html('<strong style="color: green;">{} UZS</strong>', f"{obj.available_balance:,.0f}")
    available_balance_display.short_description = _('Available')
    available_balance_display.admin_order_field = 'available_balance'
    
    def pending_balance_display(self, obj):
        return format_html('<span style="color: orange;">{} UZS</span>', f"{obj.pending_balance:,.0f}")
    pending_balance_display.short_description = _('Pending')
    pending_balance_display.admin_order_field = 'pending_balance'
    
    def lifetime_earnings_display(self, obj):
        return f"{obj.lifetime_earnings:,.0f} UZS"
    lifetime_earnings_display.short_description = _('Lifetime')
    lifetime_earnings_display.admin_order_field = 'lifetime_earnings'
    
    def total_withdrawn_display(self, obj):
        return f"{obj.total_withdrawn:,.0f} UZS"
    total_withdrawn_display.short_description = _('Withdrawn')
    total_withdrawn_display.admin_order_field = 'total_withdrawn'


@admin.register(AuthorPayout)
class AuthorPayoutAdmin(admin.ModelAdmin):
    """Author payout admin for payment processing."""
    
    list_display = (
        'author_display',
        'amount_display',
        'method',
        'status_badge',
        'processed_by',
        'created_at',
    )
    
    list_filter = ('status', 'method', 'created_at')
    
    search_fields = (
        'author__first_name',
        'author__last_name',
        'author__phone_number',
    )
    
    raw_id_fields = ('author', 'processed_by')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    
    list_per_page = 25
    
    fieldsets = (
        (_('Payout Request'), {
            'fields': ('author', 'amount', 'method', 'status')
        }),
        (_('Payment Details'), {
            'fields': ('payment_details',),
            'classes': ('collapse',),
        }),
        (_('Processing'), {
            'fields': ('processed_by', 'created_at', 'updated_at')
        }),
    )
    
    actions = ['approve_payouts', 'reject_payouts', 'mark_completed']
    
    def author_display(self, obj):
        return format_html(
            '<a href="/admin/users/user/{}/change/">{}</a>',
            obj.author.id,
            obj.author.get_full_name() or obj.author.phone_number
        )
    author_display.short_description = _('Author')
    
    def amount_display(self, obj):
        return format_html('<strong>{:,.0f} UZS</strong>', obj.amount)
    amount_display.short_description = _('Amount')
    amount_display.admin_order_field = 'amount'
    
    def status_badge(self, obj):
        """Display status with colored badge."""
        colors = {
            PayoutStatus.PENDING: 'warning',
            PayoutStatus.PROCESSING: 'info',
            PayoutStatus.COMPLETED: 'success',
            PayoutStatus.FAILED: 'danger',
            PayoutStatus.REJECTED: 'dark',
        }
        color = colors.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = _('Status')
    status_badge.admin_order_field = 'status'
    
    @admin.action(description=_('Approve selected payouts'))
    def approve_payouts(self, request, queryset):
        updated = queryset.filter(status=PayoutStatus.PENDING).update(
            status=PayoutStatus.PROCESSING,
            processed_by=request.user
        )
        self.message_user(request, f'{updated} payouts approved for processing.')
    
    @admin.action(description=_('Reject selected payouts'))
    def reject_payouts(self, request, queryset):
        updated = queryset.filter(status=PayoutStatus.PENDING).update(
            status=PayoutStatus.REJECTED,
            processed_by=request.user
        )
        self.message_user(request, f'{updated} payouts rejected.')
    
    @admin.action(description=_('Mark as completed'))
    def mark_completed(self, request, queryset):
        updated = queryset.filter(status=PayoutStatus.PROCESSING).update(
            status=PayoutStatus.COMPLETED
        )
        self.message_user(request, f'{updated} payouts marked as completed.')
