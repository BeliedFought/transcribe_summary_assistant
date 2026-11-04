"""
Single-line console progress indicator for plain mode.

Writes directly to sys.stdout using carriage return (\\r) and ANSI erase-in-line
(\\033[K), bypassing the file logger so intermediate progress frames do not
pollute the log file. Print the final completion summary via console_message().

Usage:
    import logging

    from src.localization import t
    from src.logger import console_message
    from src.progress import clear_progress, update_progress

    total = 5047
    for i in range(1, total + 1):
        pct = i / total * 100
        update_progress(
            t("msg.process_progress", pct=f"{pct:5.1f}", current=i, total=total)
        )

    clear_progress()
    console_message(logging.INFO, t("msg.process_done", total=total))
"""

import sys


def update_progress(line: str) -> None:
    """Overwrite the current console line with updated progress text."""
    sys.stdout.write(f"\r{line}")
    sys.stdout.flush()


def clear_progress() -> None:
    """Clear the current console progress line after completion."""
    sys.stdout.write("\r\033[K")
    sys.stdout.flush()
