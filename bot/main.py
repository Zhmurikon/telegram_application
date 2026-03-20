import logging
import os

import httpx
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router()
logger = logging.getLogger(__name__)

BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:8000')


@router.message(CommandStart())
async def cmd_start(message: Message):
    args = message.text.split()

    # /start без кода
    if len(args) < 2:
        await message.answer(
            '👋 Привет!\n\n'
            'Для подключения уведомлений используй пригласительную ссылку от администратора.'
        )
        return

    invite_code = args[1]

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f'{BACKEND_URL}/api/v1/subscribe/',
                json={
                    'invite_code': invite_code,
                    'telegram_id': message.from_user.id,
                    'username': message.from_user.username or '',
                },
                timeout=10,
            )

        if response.status_code == 201:
            data = response.json()
            await message.answer(
                f'✅ Вы успешно подключены к компании <b>{data["company_name"]}</b>!\n\n'
                f'Теперь вы будете получать уведомления о новых заявках.'
            )

        elif response.status_code == 400:
            data = response.json()
            await message.answer(f'❌ {data.get("error", "Неверный запрос.")}')

        elif response.status_code == 404:
            await message.answer('❌ Пригласительный код недействителен или уже использован.')

        else:
            await message.answer('⚠️ Что-то пошло не так. Попробуй позже.')

    except httpx.TimeoutException:
        logger.error('Timeout при обращении к backend')
        await message.answer('⚠️ Сервер не отвечает. Попробуй позже.')

    except Exception as e:
        logger.error(f'Ошибка при подключении: {e}')
        await message.answer('⚠️ Произошла ошибка. Попробуй позже.')
```

---

**`bot/requirements.txt`**
```
aiogram==3.7.0
httpx
python-dotenv