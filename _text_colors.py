
RED    = "\033[31m"
YELLOW = "\033[33m"
GREEN  = "\033[32m"
BLUE   = "\033[34m"
RESET  = "\033[0m"


def red_text(text: str) -> str:
    return RED + text + RESET


def yellow_text(text: str) -> str:
    return YELLOW + text + RESET


def green_text(text: str) -> str:
    return GREEN + text + RESET


def blue_text(text: str) -> str:
    return BLUE + text + RESET