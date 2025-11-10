"""Сервис для отправки уведомлений через Telegram Bot API"""
import asyncio
import logging
import socket
import threading
from typing import Optional

from django.conf import settings
from telegram import Bot
from telegram.error import TelegramError
from telegram.request import HTTPXRequest

logger = logging.getLogger(__name__)


class TelegramService:
    """Сервис для работы с Telegram Bot API"""

    _bot_instance: Optional[Bot] = None
    _bot_lock = threading.Lock()

    @classmethod
    def get_bot(cls, force_new: bool = False) -> Optional[Bot]:
        """
        Получает экземпляр бота Telegram
        
        Args:
            force_new: Если True, создает новый экземпляр бота
        
        Returns:
            Bot: Экземпляр бота или None, если токен не настроен
        """
        if not getattr(settings, 'TELEGRAM_BOT_TOKEN', None):
            logger.warning("TELEGRAM_BOT_TOKEN не настроен в settings")
            return None

        # Если требуется новый экземпляр или его нет, создаем
        if force_new or cls._bot_instance is None:
            try:
                # Настройка HTTP клиента с увеличенными таймаутами и размером пула
                # Используем HTTPXRequest с правильными параметрами
                request = HTTPXRequest(
                    connection_pool_size=10,  # Увеличенный размер пула соединений
                    read_timeout=30.0,         # Таймаут чтения
                    write_timeout=15.0,        # Таймаут записи
                    connect_timeout=15.0,      # Таймаут подключения
                    pool_timeout=10.0,          # Таймаут пула соединений
                    media_write_timeout=30.0   # Таймаут записи медиа
                )
                cls._bot_instance = Bot(token=settings.TELEGRAM_BOT_TOKEN, request=request)
                logger.debug("Бот создан с увеличенными таймаутами и размером пула")
                    
            except Exception as e:
                logger.error(f"Ошибка при создании экземпляра бота: {e}")
                # Fallback на стандартный клиент
                try:
                    cls._bot_instance = Bot(token=settings.TELEGRAM_BOT_TOKEN)
                    logger.warning("Используется стандартный клиент без увеличенных таймаутов")
                except Exception as fallback_error:
                    logger.error(f"Ошибка при создании стандартного бота: {fallback_error}")
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

        # Создаем новый экземпляр бота для каждой отправки, чтобы избежать проблем с event loop
        bot = cls.get_bot(force_new=True)
        if not bot:
            return False

        # Retry логика: до 3 попыток с экспоненциальной задержкой
        max_retries = 3
        retry_delay = 1.0  # Начальная задержка в секундах
        
        for attempt in range(1, max_retries + 1):
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
                error_msg = str(e).lower()
                # Проверяем, стоит ли повторять попытку
                if any(keyword in error_msg for keyword in ['timeout', 'connection', 'network', 'temporary']):
                    if attempt < max_retries:
                        logger.warning(
                            f"Ошибка Telegram API (попытка {attempt}/{max_retries}) при отправке в {chat_id}: {e}. "
                            f"Повтор через {retry_delay} сек..."
                        )
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2  # Экспоненциальная задержка
                        continue
                    else:
                        logger.error(f"Ошибка Telegram API после {max_retries} попыток при отправке в {chat_id}: {e}")
                        return False
                else:
                    # Критическая ошибка, не повторяем
                    logger.error(f"Критическая ошибка Telegram API при отправке в {chat_id}: {e}")
                    return False
                    
            except Exception as e:
                error_msg = str(e).lower()
                if any(keyword in error_msg for keyword in ['timeout', 'connection', 'network']):
                    if attempt < max_retries:
                        logger.warning(
                            f"Сетевая ошибка (попытка {attempt}/{max_retries}) при отправке в {chat_id}: {e}. "
                            f"Повтор через {retry_delay} сек..."
                        )
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2
                        continue
                    else:
                        logger.error(f"Сетевая ошибка после {max_retries} попыток при отправке в {chat_id}: {e}")
                        return False
                else:
                    logger.error(f"Неожиданная ошибка при отправке Telegram сообщения в {chat_id}: {e}")
                    return False
        
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
                loop = asyncio.get_running_loop()
                # Если event loop уже запущен, создаем новый в отдельном потоке
                import concurrent.futures
                import threading
                
                result_container = {'value': False, 'exception': None}
                
                def run_in_new_loop():
                    """Создает новый event loop в отдельном потоке"""
                    # Создаем новый event loop для этого потока
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        # Выполняем асинхронную функцию
                        task = new_loop.create_task(
                            cls._send_message_async(chat_id, title, message)
                        )
                        result = new_loop.run_until_complete(task)
                        result_container['value'] = result
                        return result
                    except Exception as e:
                        result_container['exception'] = e
                        logger.error(f"Ошибка в новом event loop: {e}")
                        import traceback
                        logger.debug(traceback.format_exc())
                        return False
                    finally:
                        # Даем время на завершение всех задач перед закрытием
                        try:
                            # Получаем все задачи, кроме завершенных
                            pending = [t for t in asyncio.all_tasks(new_loop) if not t.done()]
                            # Отменяем все оставшиеся задачи
                            for task in pending:
                                task.cancel()
                            # Ждем завершения отмененных задач с таймаутом
                            if pending:
                                try:
                                    new_loop.run_until_complete(
                                        asyncio.wait_for(
                                            asyncio.gather(*pending, return_exceptions=True),
                                            timeout=2.0
                                        )
                                    )
                                except asyncio.TimeoutError:
                                    logger.warning("Таймаут при ожидании завершения задач")
                                    # Принудительно закрываем незавершенные задачи
                                    for task in pending:
                                        if not task.done():
                                            task.cancel()
                        except Exception as cleanup_error:
                            logger.debug(f"Ошибка при очистке задач: {cleanup_error}")
                        finally:
                            # Даем небольшую задержку перед закрытием
                            import time
                            time.sleep(0.1)
                            # Закрываем loop только после завершения всех операций
                            try:
                                new_loop.close()
                            except Exception as close_error:
                                logger.debug(f"Ошибка при закрытии loop: {close_error}")
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_in_new_loop)
                    try:
                        # Увеличенный таймаут для ThreadPoolExecutor (с учетом retry)
                        result = future.result(timeout=60)
                        return result
                    except concurrent.futures.TimeoutError:
                        logger.error("Таймаут при отправке Telegram сообщения")
                        return False
                    except Exception as e:
                        if result_container['exception']:
                            logger.error(f"Ошибка при отправке: {result_container['exception']}")
                        else:
                            logger.error(f"Ошибка в executor: {e}")
                        return False
                        
            except RuntimeError:
                # Event loop не запущен, можно использовать asyncio.run()
                try:
                    return asyncio.run(cls._send_message_async(chat_id, title, message))
                except RuntimeError as e:
                    # Если asyncio.run() не работает, создаем новый loop вручную
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        result = loop.run_until_complete(
                            cls._send_message_async(chat_id, title, message)
                        )
                        return result
                    finally:
                        # Даем время на завершение всех задач
                        try:
                            pending = asyncio.all_tasks(loop)
                            for task in pending:
                                task.cancel()
                            if pending:
                                loop.run_until_complete(
                                    asyncio.gather(*pending, return_exceptions=True)
                                )
                        except Exception:
                            pass
                        finally:
                            loop.close()
        except Exception as e:
            logger.error(f"Ошибка при выполнении синхронной отправки Telegram сообщения: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return False

