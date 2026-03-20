from django.contrib import admin

from .models import Lead


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'company', 'status', 'created_at')
    list_filter = ('status', 'company')
    search_fields = ('name', 'phone', 'email')
    readonly_fields = ('company', 'name', 'phone', 'email', 'message', 'extra_data', 'created_at', 'updated_at')
    list_editable = ('status',)

    fieldsets = (
        ('Контакт', {
            'fields': ('name', 'phone', 'email', 'message')
        }),
        ('Доп. данные', {
            'fields': ('extra_data',),
            'classes': ('collapse',),
        }),
        ('Служебное', {
            'fields': ('company', 'status', 'created_at', 'updated_at')
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(company__in=request.user.companies.all())

    def has_add_permission(self, request):
        # Заявки создаются только через API
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return True
        # Все группы могут менять статус, но только своих компаний
        return request.user.companies.filter(id=obj.company_id).exists()

    def get_readonly_fields(self, request, obj=None):
        # Для всех кроме суперпользователя статус тоже редактируемый,
        # но все остальные поля — только чтение
        if request.user.is_superuser:
            return ('created_at', 'updated_at')
        return ('company', 'name', 'phone', 'email', 'message', 'extra_data', 'created_at', 'updated_at')