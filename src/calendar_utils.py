"""
Calendar & Liquidity Filters for Thai Stock Market (SET - Bot 2)
"""
from datetime import datetime, date
import pandas as pd


SET_HOLIDAYS_2026_2027 = {
    # 2026
    date(2026, 1, 1),   # New Year's Day
    date(2026, 3, 3),   # Makha Bucha
    date(2026, 4, 6),   # Chakri Day
    date(2026, 4, 13),  # Songkran
    date(2026, 4, 14),  # Songkran
    date(2026, 4, 15),  # Songkran
    date(2026, 5, 1),   # Labor Day
    date(2026, 5, 4),   # Coronation Day
    date(2026, 5, 31),  # Visakha Bucha (observed June 1)
    date(2026, 6, 1),   # Visakha Bucha substitute
    date(2026, 6, 3),   # Queen's Birthday
    date(2026, 7, 28),  # King Rama X Birthday
    date(2026, 7, 29),  # Asahna Bucha
    date(2026, 8, 12),  # Queen Mother Birthday
    date(2026, 10, 13), # King Rama IX Memorial
    date(2026, 10, 23), # Chulalongkorn Day
    date(2026, 12, 5),  # King Rama IX Birthday (observed Dec 7)
    date(2026, 12, 7),  # Substitute
    date(2026, 12, 10), # Constitution Day
    date(2026, 12, 31), # New Year's Eve
    # 2027
    date(2027, 1, 1),
}


def is_thai_market_holiday(dt: datetime = None) -> bool:
    """Checks if the given date is a SET market holiday or weekend."""
    d = (dt or datetime.now()).date()
    if d.weekday() >= 5:
        return True
    return d in SET_HOLIDAYS_2026_2027


def passes_thai_liquidity_filter(df: pd.DataFrame, min_turnover_thb: float = 10000000.0, min_price: float = 1.0) -> bool:
    """
    Checks if a Thai stock meets SET liquidity:
    - 20-day Average Daily Value (Turnover) >= 10,000,000 THB
    - Close price >= 1.00 THB (exclude Penny stocks)
    """
    if len(df) < 20:
        return False
    curr_close = float(df["Close"].iloc[-1])
    if curr_close < min_price:
        return False
    turnover_20 = (df["Volume"] * df["Close"]).iloc[-20:].mean()
    return float(turnover_20) >= min_turnover_thb
