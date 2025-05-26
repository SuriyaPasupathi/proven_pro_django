from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from .models import Users, PendingUsers, ProfileShare, Review
from django.db import models
from django.db.models import Q


class UsersAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'subscription_type', 'verification_status_display')
    search_fields = ('email', 'first_name', 'last_name')
    list_filter = ('subscription_type', 'gov_id_verified', 'address_verified', 'mobile_verified')
    readonly_fields = ('verification_percentage', 'view_gov_id', 'view_address_doc')
    actions = ['approve_gov_id', 'approve_address_proof', 'reject_gov_id', 'reject_address_proof']
    fieldsets = (
        ('Basic Info', {
            'fields': ('email', 'first_name', 'last_name', 'username', 'profile_pic')
        }),
        ('Subscription', {
            'fields': ('subscription_type', 'subscription_active', 'subscription_start_date', 'subscription_end_date')
        }),
        ('Verification', {
            'fields': (
                'verification_percentage', 
                ('gov_id_document', 'view_gov_id', 'gov_id_verified'),
                ('address_document', 'view_address_doc', 'address_verified'),
                ('mobile', 'mobile_verified')
            )
        }),
    )

    def verification_status_display(self, obj):
        percentage = obj.verification_status
        color = 'red'
        if percentage >= 75:
            color = 'green'
        elif percentage >= 50:
            color = 'orange'
        return format_html('<span style="color: {};">{}</span>', color, f"{percentage}% Verified")
    verification_status_display.short_description = 'Verification'

    def view_gov_id(self, obj):
        if obj.gov_id_document:
            return format_html('<a href="{}" target="_blank">View Document</a>', obj.gov_id_document.url)
        return "No document uploaded"
    view_gov_id.short_description = 'View Government ID'

    def view_address_doc(self, obj):
        if obj.address_document:
            return format_html('<a href="{}" target="_blank">View Document</a>', obj.address_document.url)
        return "No document uploaded"
    view_address_doc.short_description = 'View Address Proof'
    
    def approve_gov_id(self, request, queryset):
        updated = 0
        for user in queryset:
            if user.gov_id_document and not user.gov_id_verified:
                user.gov_id_verified = True
                user.save()
                user.send_verification_status_email('gov_id', True)
                updated += 1
        self._notify_result(request, updated, "approved", "government ID")

    def approve_address_proof(self, request, queryset):
        updated = 0
        for user in queryset:
            if user.address_document and not user.address_verified:
                user.address_verified = True
                user.save()
                user.send_verification_status_email('address', True)
                updated += 1
        self._notify_result(request, updated, "approved", "address proof")

    def reject_gov_id(self, request, queryset):
        updated = 0
        for user in queryset:
            if user.gov_id_verified:
                user.gov_id_verified = False
                user.save()
                user.send_verification_status_email('gov_id', False)
                updated += 1
        self._notify_result(request, updated, "rejected", "government ID")

    def reject_address_proof(self, request, queryset):
        updated = 0
        for user in queryset:
            if user.address_verified:
                user.address_verified = False
                user.save()
                user.send_verification_status_email('address', False)
                updated += 1
        self._notify_result(request, updated, "rejected", "address proof")

    def _notify_result(self, request, updated, action, doc_type):
        if updated:
            self.message_user(
                request,
                f"Successfully {action} {doc_type} for {updated} user(s). Verification status updated.",
                messages.SUCCESS
            )
        else:
            self.message_user(
                request,
                f"No users with {doc_type} matching criteria were found.",
                messages.WARNING
            )

admin.site.register(Users, UsersAdmin)

#pending status
class PendingUsersAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'pending_percentage_display')
    search_fields = ('email', 'first_name', 'last_name')
    list_filter = ('subscription_type',)
    readonly_fields = ('verification_percentage',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Include users with any pending verification (i.e. verification < 100%)
        return qs.filter(
            models.Q(verification_percentage__lt=100)
        )

    def pending_percentage_display(self, obj):
        pending = 100 - obj.verification_status
        color = 'orange' if pending > 0 else 'green'
        return format_html('<span style="color: {};">{}%</span>', color, pending)

    pending_percentage_display.short_description = 'Pending %'

admin.site.register(PendingUsers, PendingUsersAdmin)

# Register other models
admin.site.register(ProfileShare)
admin.site.register(Review)
