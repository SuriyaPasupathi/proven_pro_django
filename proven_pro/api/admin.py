from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from .models import Users, ProfileShare, Review

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
            if user.gov_id_document:
                user.gov_id_verified = True
                user.save()
                updated += 1
        
        if updated:
            self.message_user(
                request, 
                f"Successfully approved government ID for {updated} user(s). Verification status updated.",
                messages.SUCCESS
            )
        else:
            self.message_user(
                request,
                "No users with government ID documents were found.",
                messages.WARNING
            )
    approve_gov_id.short_description = "Approve Government ID"
    
    def approve_address_proof(self, request, queryset):
        updated = 0
        for user in queryset:
            if user.address_document:
                user.address_verified = True
                user.save()
                updated += 1
        
        if updated:
            self.message_user(
                request, 
                f"Successfully approved address proof for {updated} user(s). Verification status updated.",
                messages.SUCCESS
            )
        else:
            self.message_user(
                request,
                "No users with address proof documents were found.",
                messages.WARNING
            )
    approve_address_proof.short_description = "Approve Address Proof"
    
    def reject_gov_id(self, request, queryset):
        updated = 0
        for user in queryset:
            if user.gov_id_verified:
                user.gov_id_verified = False
                user.save()
                updated += 1
        
        if updated:
            self.message_user(
                request, 
                f"Successfully rejected government ID for {updated} user(s). Verification status updated.",
                messages.SUCCESS
            )
        else:
            self.message_user(
                request,
                "No users with verified government ID were found.",
                messages.WARNING
            )
    reject_gov_id.short_description = "Reject Government ID"
    
    def reject_address_proof(self, request, queryset):
        updated = 0
        for user in queryset:
            if user.address_verified:
                user.address_verified = False
                user.save()
                updated += 1
        
        if updated:
            self.message_user(
                request, 
                f"Successfully rejected address proof for {updated} user(s). Verification status updated.",
                messages.SUCCESS
            )
        else:
            self.message_user(
                request,
                "No users with verified address proof were found.",
                messages.WARNING
            )
    reject_address_proof.short_description = "Reject Address Proof"

admin.site.register(Users, UsersAdmin)
admin.site.register(ProfileShare)
admin.site.register(Review)
