from django.db import models


class Lead(models.Model):

    class Status(models.TextChoices):
        NEW = 'new', 'Новая'
        IN_PROGRESS = 'in_progress', 'В работе'
        CLOSED = 'closed', 'Закрыта'

    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='leads',
        verbose_name='Компания',
    )
    name = models.CharField(max_length=255, verbose_name='Имя')
    phone = models.CharField(max_length=32, blank=True, verbose_name='Телефон')
    email = models.EmailField(blank=True, verbose_name='Email')
    message = models.TextField(blank=True, verbose_name='Сообщение')
    extra_data = models.JSONField(default=dict, blank=True, verbose_name='Доп. данные')
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.NEW,
        verbose_name='Статус',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Заявка'
        verbose_name_plural = 'Заявки'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} — {self.company.name} ({self.get_status_display()})'