from datetime import datetime, timedelta
from typing import List


def getDateIntervals(startDate: datetime, endDate: datetime, interval: str) -> List[datetime]:
    """
    Generate a list of dates between startDate and endDate based on the specified interval.
    
    Args:
        startDate (datetime): The starting date
        endDate (datetime): The ending date
        interval (str): The interval type - must be one of: 'day', 'week', 'month'
        
    Returns:
        List[datetime]: A list of dates from startDate to endDate at the specified interval
        
    Raises:
        ValueError: If endDate is not greater than startDate
        ValueError: If interval is not one of: 'day', 'week', 'month'
    """
    if endDate <= startDate:
        raise ValueError("endDate must be greater than startDate")
    if interval not in {"day", "week", "month"}:
        raise ValueError("interval must be one of: 'day', 'week', 'month'")

    intervals = [startDate]
    current = startDate

    while True:
        next_date = getNextIntervalDate(current, interval)
        if next_date > endDate:
            break
        intervals.append(next_date)
        current = next_date

    return intervals


def getNextIntervalDate(date: datetime, interval: str) -> datetime:
    """
    Returns the next date based on the specified interval.

    Args:
        date (datetime): The starting date
        interval (str): The interval type - must be one of: 'day', 'week', 'month'
        
    Returns:
        datetime: The next date based on the interval:
            - 'day': next day after `date`
            - 'week': next Monday after `date`
            - 'month': first day of the next month after `date`
            
    Raises:
        ValueError: If interval is not one of: 'day', 'week', 'month'
    """
    if interval == 'day':
        return date + timedelta(days=1)
    elif interval == 'week':
        days_until_monday = (7 - date.weekday()) % 7 or 7
        return date + timedelta(days=days_until_monday)
    elif interval == 'month':
        year = date.year + (date.month // 12)
        month = (date.month % 12) + 1
        return datetime(year, month, 1, date.hour, date.minute, date.second, date.microsecond)
    else:
        raise ValueError("interval must be one of: 'day', 'week', 'month'")


if __name__ == "__main__":
    # Example usage
    print("Testing getDateIntervals:")
    s = datetime(2025, 1, 10)
    e = datetime(2025, 1, 19)
    print("Day intervals:")
    for d in getDateIntervals(s, e, "day"):
        print(d)

    s = datetime(2025, 1, 10)
    e = datetime(2025, 2, 5)
    print("\nWeek intervals:")
    for d in getDateIntervals(s, e, "week"):
        print(d)

    s = datetime(2024, 11, 16)
    e = datetime(2025, 7, 10)
    print("\nMonth intervals:")
    for d in getDateIntervals(s, e, "month"):
        print(d)

    # Test getNextIntervalDate
    print("\nTesting getNextIntervalDate:")
    d = datetime(2025, 2, 5)
    print("Current date:", d)
    print("Next day:", getNextIntervalDate(d, "day"))
    print("Next Monday:", getNextIntervalDate(d, "week"))
    print("First of next month:", getNextIntervalDate(d, "month")) 