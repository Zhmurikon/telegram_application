from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    companies = models.ManyToManyField(
        'companies.Company',
        blank=True,
        related_name='users',
        verbose_name='Компании',
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class TelegramSubscriber(models.Model):
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='telegram_subscribers',
        verbose_name='Компания',
    )
    telegram_id = models.BigIntegerField(unique=True, verbose_name='Telegram ID')
    username = models.CharField(max_length=255, blank=True, verbose_name='Username')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Подписчик бота'
        verbose_name_plural = 'Подписчики бота'

    def __str__(self):
        return f'@{self.username or self.telegram_id} — {self.company.name}'