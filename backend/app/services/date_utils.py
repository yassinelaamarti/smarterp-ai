from datetime import date


def current_month_str() -> str:
    return date.today().strftime("%Y-%m")


def previous_month_str() -> str:
    today = date.today()
    year = today.year - 1 if today.month == 1 else today.year
    month = 12 if today.month == 1 else today.month - 1
    return f"{year:04d}-{month:02d}"
