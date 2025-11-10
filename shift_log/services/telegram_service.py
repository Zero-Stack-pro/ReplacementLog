"""Сервис для отправки уведомлений через Telegram Bot API"""
import asyncio
import logging
from typing import Optional

from django.conf import settings
from telegram import Bot
from telegram.error import TelegramError

logger = logging.getLogger(__name__)


class TelegramService:
    """Сервис для работы с Telegram Bot API"""

    _bot_instance: Optional[Bot] = None

    @classmethod
    def get_bot(cls) -> Optional[Bot]:
        """
        Получает экземпляр бота Telegram
        
        Returns:
            Bot: Экземпляр бота или None, если токен не настроен
        """
        if not getattr(settings, 'TELEGRAM_BOT_TOKEN', None):
            logger.warning("TELEGRAM_BOT_TOKEN не настроен в settings")
            return None

        if cls._bot_instance is None:
            try:
                cls._bot_instance = Bot(token=settings.TELEGRAM_BOT_TOKEN)
            except Exception as e:
                logger.error(f"Ошибка при создании экземпляра бота: {e}")
                return None

        return cls._bot_instance

    @classmethod
    async def _send_message_async(
        cls,
        chat_id: str,
        title: str,
        message: str
    ) -> bool:
        """
        Асинхронная отправка сообщения в Telegram
        
        Args:
            chat_id: ID чата (telegram_id сотрудника)
            title: Заголовок уведомления
            message: Текст сообщения
            
        Returns:
            bool: True если сообщение отправлено успешно, False в противном случае
        """
        if not getattr(settings, 'TELEGRAM_NOTIFICATIONS_ENABLED', True):
            logger.debug("Telegram уведомления отключены в настройках")
            return False

        if not chat_id:
            logger.warning("chat_id не указан для отправки Telegram уведомления")
            return False

        bot = cls.get_bot()
        if not bot:
            return False

        try:
            # Форматируем сообщение: заголовок жирным, затем текст
            formatted_message = f"*{title}*\n\n{message}"
            
            # Отправляем сообщение асинхронно
            await bot.send_message(
                chat_id=chat_id,
                text=formatted_message,
                parse_mode='Markdown'
            )
            
            logger.info(f"Telegram уведомление отправлено в чат {chat_id}: {title}")
            return True

        except TelegramError as e:
            logger.error(f"Ошибка Telegram API при отправке сообщения в {chat_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Неожиданная ошибка при отправке Telegram сообщения в {chat_id}: {e}")
            return False

    @classmethod
    def send_message(
        cls,
        chat_id: str,
        title: str,
        message: str
    ) -> bool:
        """
        Отправляет сообщение в Telegram (синхронный wrapper)
        
        Args:
            chat_id: ID чата (telegram_id сотрудника)
            title: Заголовок уведомления
            message: Текст сообщения
            
        Returns:
            bool: True если сообщение отправлено успешно, False в противном случае
        """
        try:
            # Проверяем, есть ли уже запущенный event loop
            try:
                asyncio.get_running_loop()
                # Если event loop уже запущен, создаем новый в отдельном потоке
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        lambda: asyncio.run(cls._send_message_async(chat_id, title, message))
                    )
                    return future.result(timeout=10)
            except RuntimeError:
                # Event loop не запущен, можно использовать asyncio.run()
                return asyncio.run(cls._send_message_async(chat_id, title, message))
        except Exception as e:
            logger.error(f"Ошибка при выполнении синхронной отправки Telegram сообщения: {e}")
            return False

