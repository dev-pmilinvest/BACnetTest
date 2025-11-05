"""
Utility functions
Includes safe Unicode character handling for cross-platform compatibility
"""

import sys


class Symbols:
    """
    Unicode symbols with ASCII fallbacks for Windows compatibility
    """

    # Detect if terminal supports Unicode
    _supports_unicode = sys.stdout.encoding.lower().startswith('utf') if hasattr(sys.stdout, 'encoding') else False

    if _supports_unicode:
        # Unicode versions
        CHECK = '✓'
        CROSS = '✗'
        WARNING = '⚠'
        INFO = 'ℹ'
        STATS = '📊'
        ARROW_RIGHT = '→'
        BULLET = '•'
    else:
        # ASCII fallbacks
        CHECK = '[OK]'
        CROSS = '[X]'
        WARNING = '[!]'
        INFO = '[i]'
        STATS = '[*]'
        ARROW_RIGHT = '->'
        BULLET = '*'


# Convenience functions
def check(text: str) -> str:
    """Add check mark to text"""
    return f"{Symbols.CHECK} {text}"


def cross(text: str) -> str:
    """Add cross mark to text"""
    return f"{Symbols.CROSS} {text}"


def warning(text: str) -> str:
    """Add warning symbol to text"""
    return f"{Symbols.WARNING} {text}"


def info(text: str) -> str:
    """Add info symbol to text"""
    return f"{Symbols.INFO} {text}"