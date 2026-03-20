from django.contrib import admin
from django.utils import timezone

from .models import ApiKey, Company, InviteCode


class ApiKeyInline(admin.StackedInline):
    model = ApiKey
    readonly_fields = ('key', 'created_at')
    extra = 0
    can_delete = False

    def has_add_permission(self, request, obj=None):
        # ApiKey создаётся автоматически при создании компании
        return False


class InviteCodeInline(admin.TabularInline):
    model = InviteCode
    readonly_fields = ('code', 'is_used', 'used_by_telegram_id', 'created_by', 'created_at', 'used_at')
    extra = 0
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at', 'get_api_key', 'get_active_invite_codes')
    list_filter = ('is_active',)
    search_fields = ('name',)
    inlines = [ApiKeyInline, InviteCodeInline]
    actions = ['generate_invite_code', 'regenerate_api_key']

    def get_api_key(self, obj):
        try:
            return f'{obj.api_key.key[:8]}...'
        except ApiKey.DoesNotExist:
            return '—'
    get_api_key.short_description = 'API ключ'

    def get_active_invite_codes(self, obj):
        count = obj.invite_codes.filter(is_used=False).count()
        return count
    get_active_invite_codes.short_description = 'Активных кодов'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(id__in=request.user.companies.all())

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Автоматически создаём ApiKey при создании компании
        if not change:
            ApiKey.objects.get_or_create(company=obj)

    @admin.action(description='Сгенерировать пригласительный код')
    def generate_invite_code(self, request, queryset):
        if not self._can_manage_invites(request):
            self.message_user(request, 'Недостаточно прав.', level='error')
            return

        created = 0
        for company in queryset:
            if not request.user.is_superuser:
                if not request.user.companies.filter(id=company.id).exists():
                    continue
            InviteCode.objects.create(company=company, created_by=request.user)
            created += 1

        self.message_user(request, f'Создано кодов: {created}.')

    @admin.action(description='Перегенерировать API ключ')
    def regenerate_api_key(self, request, queryset):
        if not request.user.is_superuser:
            self.message_user(request, 'Недостаточно прав.', level='error')
            return

        for company in queryset:
            ApiKey.objects.filter(company=company).delete()
            ApiKey.objects.create(company=company)

        self.message_user(request, f'API ключи обновлены: {queryset.count()}.')

    def _can_manage_invites(self, request):
        if request.user.is_superuser:
            return True
        user_groups = request.user.groups.values_list('name', flat=True)
        return 'Администраторы компаний' in user_groups or 'Суперадмины' in user_groups

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return True
        return request.user.companies.filter(id=obj.id).exists()


@admin.register(InviteCode)
class InviteCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'company', 'is_used', 'created_by', 'created_at', 'used_at')
    list_filter = ('is_used', 'company')
    readonly_fields = ('code', 'is_used', 'used_by_telegram_id', 'created_by', 'created_at', 'used_at')
    actions = ['generate_invite_code']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(company__in=request.user.companies.all())

    @admin.action(description='Сгенерировать пригласительный код')
    def generate_invite_code(self, request, queryset):
        if not self._can_manage_invites(request):
            self.message_user(request, 'Недостаточно прав.', level='error')
            return

        companies = queryset.values_list('company', flat=True).distinct()
        for company_id in companies:
            InviteCode.objects.create(
                company_id=company_id,
                created_by=request.user,
            )
        self.message_user(request, f'Создано кодов: {companies.count()}.')

    def _can_manage_invites(self, request):
        if request.user.is_superuser:
            return True
        user_groups = request.user.groups.values_list('name', flat=True)
        return 'Администраторы компаний' in user_groups or 'Суперадмины' in user_groups

    def has_add_permission(self, request):
        return self._can_manage_invites(request)

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return False