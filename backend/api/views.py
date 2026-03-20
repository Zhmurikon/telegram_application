import logging

from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from companies.models import ApiKey, InviteCode
from leads.models import Lead

logger = logging.getLogger(__name__)


class LeadCreateView(APIView):

    def post(self, request):
        api_key = request.headers.get('X-Api-Key')

        if not api_key:
            return Response(
                {'error': 'API ключ не передан.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            key_obj = ApiKey.objects.select_related('company').get(key=api_key)
        except ApiKey.DoesNotExist:
            return Response(
                {'error': 'Неверный API ключ.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not key_obj.company.is_active:
            return Response(
                {'error': 'Компания неактивна.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        data = request.data

        name = data.get('name', '').strip()
        if not name:
            return Response(
                {'error': 'Поле name обязательно.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        phone = data.get('phone', '').strip()
        email = data.get('email', '').strip()
        message = data.get('message', '').strip()

        # Всё что не является базовыми полями — уходит в extra_data
        base_fields = {'name', 'phone', 'email', 'message'}
        extra_data = {k: v for k, v in data.items() if k not in base_fields}

        lead = Lead.objects.create(
            company=key_obj.company,
            name=name,
            phone=phone,
            email=email,
            message=message,
            extra_data=extra_data,
        )

        # Отправка в Telegram
        self._notify_telegram(lead)

        return Response(
            {'success': True, 'lead_id': lead.id},
            status=status.HTTP_201_CREATED,
        )

    def _notify_telegram(self, lead):
        try:
            from accounts.models import TelegramSubscriber
            import httpx

            subscribers = TelegramSubscriber.objects.filter(
                company=lead.company,
            ).values_list('telegram_id', flat=True)

            if not subscribers:
                return

            text = self._format_message(lead)
            token = settings.TELEGRAM_BOT_TOKEN

            for telegram_id in subscribers:
                try:
                    httpx.post(
                        f'https://api.telegram.org/bot{token}/sendMessage',
                        json={
                            'chat_id': telegram_id,
                            'text': text,
                            'parse_mode': 'HTML',
                        },
                        timeout=5,
                    )
                except Exception as e:
                    logger.error(f'Ошибка отправки в Telegram {telegram_id}: {e}')

        except Exception as e:
            logger.error(f'Ошибка уведомления Telegram: {e}')

    def _format_message(self, lead):
        lines = [
            f'🔔 <b>Новая заявка</b> — {lead.company.name}',
            '',
            f'👤 <b>Имя:</b> {lead.name}',
        ]

        if lead.phone:
            lines.append(f'📞 <b>Телефон:</b> {lead.phone}')
        if lead.email:
            lines.append(f'📧 <b>Email:</b> {lead.email}')
        if lead.message:
            lines.append(f'💬 <b>Сообщение:</b> {lead.message}')

        if lead.extra_data:
            lines.append('')
            lines.append('📋 <b>Доп. данные:</b>')
            for key, value in lead.extra_data.items():
                lines.append(f'  • {key}: {value}')

        lines.append('')
        lines.append(f'🕐 {lead.created_at.strftime("%d.%m.%Y %H:%M")}')

        return '\n'.join(lines)
    


class SubscribeView(APIView):

    def post(self, request):
        invite_code = request.data.get('invite_code', '').strip()
        telegram_id = request.data.get('telegram_id')
        username = request.data.get('username', '').strip()

        if not invite_code or not telegram_id:
            return Response(
                {'error': 'invite_code и telegram_id обязательны.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            code_obj = InviteCode.objects.select_related('company').get(
                code=invite_code,
                is_used=False,
            )
        except InviteCode.DoesNotExist:
            return Response(
                {'error': 'Код недействителен или уже использован.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not code_obj.company.is_active:
            return Response(
                {'error': 'Компания неактивна.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        from accounts.models import TelegramSubscriber
        from django.utils import timezone

        # Если уже подписан на эту компанию
        if TelegramSubscriber.objects.filter(
            telegram_id=telegram_id,
            company=code_obj.company,
        ).exists():
            return Response(
                {'error': 'Вы уже подписаны на уведомления этой компании.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        TelegramSubscriber.objects.create(
            company=code_obj.company,
            telegram_id=telegram_id,
            username=username,
        )

        # Помечаем код как использованный
        code_obj.is_used = True
        code_obj.used_by_telegram_id = telegram_id
        code_obj.used_at = timezone.now()
        code_obj.save()

        return Response(
            {'company_name': code_obj.company.name},
            status=status.HTTP_201_CREATED,
        )