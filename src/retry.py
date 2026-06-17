"""
Retry с экспоненциальным backoff для внешних подключении.

Параметры - из config/config.ini секция [retry]:
    count - количество попыток (по умолчанию 3)
    delay - начальная задержка в секундах (по умолчанию 2)
    max_delay - максимальная задержка (30 сек)

Не retry: 401, 403, 400, 422
Retry: 5xx, ConnectionError, TimeoutError, OperationalError

Использование:
    from src.retry import retry
    result = retry(lambda: requests.get(url), config, [requests.Timeout])
"""

import logging
import time
from collections.abc import Callable
from configparser import ConfigParser
from typing import Any, TypeVar

from src.localization import t

T = TypeVar("T")

NON_RETRYABLE_HTTP_CODES: frozenset[int] = frozenset({401, 403, 400, 422})


def _is_retryable(exception: BaseException, retryable_types: tuple[type[BaseException], ...]) -> bool:
    """Проверить, является ли исключение retryable."""
    if isinstance(exception, retryable_types):
        return True
    return False


def retry(
    func: Callable[[], T],
    config: ConfigParser,
    retryable_types: tuple[type[BaseException], ...],
) -> T:
    """
    Выполнить функцию с повторными попытками при retryable ошибках.

    :param func: функция без аргументов, возвращающая результат
    :param config: ConfigParser с секцией [retry]
    :param retryable_types: кортеж типов исключении для retry
    :return: результат функции
    :raises: последнее исключение после исчерпания попыток
    """
    retry_count: int = config.getint("retry", "count", fallback=3)
    retry_delay: int = config.getint("retry", "delay", fallback=2)
    max_delay: int = config.getint("retry", "max_delay", fallback=30)

    last_exception: BaseException | None = None

    for attempt in range(1, retry_count + 1):
        try:
            return func()
        except Exception as e:
            last_exception = e

            if not _is_retryable(e, retryable_types):
                raise

            if attempt >= retry_count:
                raise

            sleep_time = min(retry_delay * (2 ** (attempt - 1)), max_delay)
            logging.getLogger(__name__).warning(
                t(
                    "msg.retry_attempt",
                    attempt=attempt,
                    total=retry_count,
                    delay=f"{sleep_time:.1f}",
                    reason=str(e),
                ),
            )
            time.sleep(sleep_time)

    raise last_exception  # type: ignore[misc]
