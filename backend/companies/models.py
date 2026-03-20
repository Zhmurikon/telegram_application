import secrets
from django.db import models


class Company(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')
    is_active = models.BooleanField(default=True, verbose_name='Активна')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Компания'
        verbose_name_plural = 'Компании'

    def __str__(self):
        return self.name


class ApiKey(models.Model):
    company = models.OneToOneField(
        Company,
        on_delete=models.CASCADE,
        related_name='api_key',
        verbose_name='Компания',
    )
    key = models.CharField(max_length=64, unique=True, editable=False, verbose_name='Ключ')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'API ключ'
        verbose_name_plural = 'API ключи'

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = secrets.token_hex(32)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.company.name} — {self.key[:8]}...'


class InviteCode(models.Model):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='invite_codes',
        verbose_name='Компания',
    )
    code = models.CharField(max_length=32, unique=True, editable=False, verbose_name='Код')
    is_used = models.BooleanField(default=False, verbose_name='Использован')
    created_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_invite_codes',
        verbose_name='Создан пользователем',
    )
    used_by_telegram_id = models.BigIntegerField(null=True, blank=True, verbose_name='Telegram ID')
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Пригласительный код'
        verbose_name_plural = 'Пригласительные коды'

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = secrets.token_urlsafe(16)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.company.name} — {self.code} ({"использован" if self.is_used else "активен"})'