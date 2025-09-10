from datetime import date, timedelta
from typing import Iterable, Optional, Set


def business_days(start: date, end: date, holidays: Optional[Iterable[date]] = None) -> int:
    """Return the number of business days between ``start`` and ``end``.

    Weekends (Saturday and Sunday) are excluded. An optional ``holidays``
    iterable may be supplied to exclude specific dates.

    The calculation is inclusive of both ``start`` and ``end``.
    """
    if start > end:
        start, end = end, start

    holiday_set: Set[date] = set(holidays or [])
    current = start
    day_count = 0
    one_day = timedelta(days=1)
    while current <= end:
        if current.weekday() < 5 and current not in holiday_set:
            day_count += 1
        current += one_day
    return day_count
