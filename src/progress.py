"""
Индикация прогресса в консоли.

Для длительных операции (обработка файлов, транскрибация) используется
перезапись одной строки через \r. Вывод идет напрямую в sys.stdout, минуя
логгер - строки прогресса не дублируются в лог-файл.

Использование:
    from src.progress import update_progress, clear_progress
    for i in range(total):
        update_progress(f"Обработка {i/total*100:.1f}% ({i}/{total})")
    clear_progress()
"""

import sys


def update_progress(line: str) -> None:
    """Перезаписать текущую строку в консоли."""
    sys.stdout.write(f"\r{line}")
    sys.stdout.flush()


def clear_progress() -> None:
    """Очистить строку прогресса после завершения."""
    sys.stdout.write("\r\033[K")
    sys.stdout.flush()
