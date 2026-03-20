from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

from .models import CustomUser, TelegramSubscriber


class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_active', 'get_groups')
    list_filter = ('is_active', 'groups')
    filter_horizontal = ('companies',)

    def get_groups(self, obj):
        return ', '.join(obj.groups.values_list('name', flat=True))
    get_groups.short_description = 'Группы'

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if request.user.is_superuser:
            return fieldsets + (
                ('Компании', {'fields': ('companies',)}),
            )
        return (
            (None, {'fields': ('username', 'password')}),
            ('Личные данные', {'fields': ('first_name', 'last_name', 'email')}),
            ('Компании', {'fields': ('companies',)}),
            ('Доступ', {'fields': ('is_active', 'groups')}),
        )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Показываем только пользователей своих компаний
        user_companies = request.user.companies.all()
        return qs.filter(companies__in=user_companies).distinct()

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # После сохранения ограничиваем компании — только из компаний текущего юзера
        if not request.user.is_superuser:
            allowed = request.user.companies.all()
            obj.companies.set(obj.companies.filter(id__in=allowed))

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        # Ограничиваем выбор компаний
        if db_field.name == 'companies' and not request.user.is_superuser:
            kwargs['queryset'] = request.user.companies.all()
        # Ограничиваем выбор групп — нельзя назначить группу выше своей
        if db_field.name == 'groups' and not request.user.is_superuser:
            kwargs['queryset'] = self._get_allowed_groups(request.user)
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def _get_allowed_groups(self, user):
        user_groups = user.groups.values_list('name', flat=True)
        if 'Суперадмины' in user_groups:
            allowed = ['Суперадмины', 'Администраторы компаний', 'Менеджеры']
        elif 'Администраторы компаний' in user_groups:
            allowed = ['Администраторы компаний', 'Менеджеры']
        else:
            allowed = []
        return Group.objects.filter(name__in=allowed)

    def has_add_permission(self, request):
        if request.user.is_superuser:
            return True
        user_groups = request.user.groups.values_list('name', flat=True)
        # Менеджеры не могут создавать пользователей
        return 'Менеджеры' not in user_groups or 'Администраторы компаний' in user_groups

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return True
        # Нельзя редактировать пользователей не из своих компаний
        user_companies = set(request.user.companies.values_list('id', flat=True))
        obj_companies = set(obj.companies.values_list('id', flat=True))
        return bool(user_companies & obj_companies)

    def has_delete_permission(self, request, obj=None):
        return self.has_change_permission(request, obj)


@admin.register(TelegramSubscriber)
class TelegramSubscriberAdmin(admin.ModelAdmin):
    list_display = ('telegram_id', 'username', 'company', 'created_at')
    list_filter = ('company',)
    readonly_fields = ('telegram_id', 'username', 'company', 'created_at')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(company__in=request.user.companies.all())

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return False


admin.site.register(CustomUser, CustomUserAdmin)