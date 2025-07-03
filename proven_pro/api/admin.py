from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from .models import Users, PendingUsers, ProfileShare, Review, ToolsSkillsCategory,JobPosition,Service_drop_down,Skill
from django.db import models
from django.db.models import Q
import json
from django import forms
from django.contrib import admin
from .models import PlanDetails

class SkillInline(admin.TabularInline):
    model = Skill
    extra = 1

@admin.register(ToolsSkillsCategory)
class ToolsSkillsCategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    inlines = [SkillInline]

class UsersAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'gov_id_verified', 'address_verified')
    search_fields = ('email', 'first_name', 'last_name')
    list_filter = ('is_verified', 'gov_id_verified', 'address_verified')
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
                ('gov_id_document', 'view_gov_id', 'gov_id_status'),
                ('address_document', 'view_address_doc', 'address_status'),
                ('mobile', 'mobile_status')
            )
        }),
    )

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
            if user.gov_id_document and user.gov_id_status != 'approved':
                user.gov_id_status = 'approved'
                user.save()
                user.send_verification_status_email('gov_id', True)
                updated += 1
        self._notify_result(request, updated, "approved", "government ID")

    def approve_address_proof(self, request, queryset):
        updated = 0
        for user in queryset:
            if user.address_document and user.address_status != 'approved':
                user.address_status = 'approved'
                user.save()
                user.send_verification_status_email('address', True)
                updated += 1
        self._notify_result(request, updated, "approved", "address proof")

    def reject_gov_id(self, request, queryset):
        updated = 0
        for user in queryset:
            if user.gov_id_status != 'rejected':
                user.gov_id_status = 'rejected'
                user.save()
                user.send_verification_status_email('gov_id', False)
                updated += 1
        self._notify_result(request, updated, "rejected", "government ID")

    def reject_address_proof(self, request, queryset):
        updated = 0
        for user in queryset:
            if user.address_status != 'rejected':
                user.address_status = 'rejected'
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

class PlanDetailsForm(forms.ModelForm):
    class Meta:
        model = PlanDetails
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Show raw text from includes content — no assumptions
        if self.instance and self.instance.includes:
            try:
                data = json.loads(self.instance.includes)
                if isinstance(data, list) and data and isinstance(data[0], dict):
                    titles = data[0].get("title", {})
                    if isinstance(titles, dict):
                        self.fields['includes'].initial = "\n".join(titles.values())
            except Exception:
                self.fields['includes'].initial = self.instance.includes

    def clean_includes(self):
        raw = self.cleaned_data['includes']

        # Try parsing raw input as JSON
        try:
            parsed = json.loads(raw)

            # Already in the expected format
            if (
                isinstance(parsed, list) and len(parsed) == 1 and
                isinstance(parsed[0], dict) and isinstance(parsed[0].get("title"), dict)
            ):
                return json.dumps(parsed, indent=2)

            # If it's a flat list of strings (["A", "B", ...])
            if isinstance(parsed, list) and all(isinstance(x, str) for x in parsed):
                return json.dumps([{"title": {str(i+1): x for i, x in enumerate(parsed)}}], indent=2)

            # If it's just a dict like {"1": "Feature A", ...}
            if isinstance(parsed, dict) and all(isinstance(k, str) and isinstance(v, str) for k, v in parsed.items()):
                return json.dumps([{"title": parsed}], indent=2)

        except Exception:
            pass  # fallback to line-based text

        # Treat as plain multiline text input
        lines = [line.strip() for line in raw.splitlines() if line.strip()]
        title_dict = {str(i+1): line for i, line in enumerate(lines)}
        return json.dumps([{"title": title_dict}], indent=2)
    
class PlanDetailsAdmin(admin.ModelAdmin):
    form = PlanDetailsForm

admin.site.register(PlanDetails, PlanDetailsAdmin)


admin.site.register(PendingUsers, PendingUsersAdmin)

# Register other models
admin.site.register(Users, UsersAdmin)
admin.site.register(ProfileShare)
admin.site.register(Review)
admin.site.register(Skill)
admin.site.register(JobPosition)
admin.site.register(Service_drop_down)