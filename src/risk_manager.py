"""
Risk Management Engine for Thai SET 6-Button Strategy (Bot 2):
1. Stop Loss: Swing Low (10 bars) with ATR buffer, snapped down to legal SET tick.
2. Board Lot: 100 shares. If 0.5% risk budget cannot buy 100 shares, order is rejected.
3. Max Position Cap: 20% of 1,000,000 THB = 200,000 THB.
4. Targets: Target 3R (+3.0R) and Target 5R (+5.0R), snapped to legal SET ticks.
"""
from typing import Dict, Optional
import pandas as pd
from .indicators import step_tick_down, round_to_set_tick


class Thai6ButtonRiskManager:
    def __init__(self, config: Optional[Dict] = None):
        cfg = config or {}
        self.total_capital = float(cfg.get("total_capital", 1000000.0))  # 1M THB
        self.risk_pct = float(cfg.get("risk_per_trade_pct", 0.005))  # 0.5% = 5,000 THB
        self.max_cap_pct = float(cfg.get("max_position_capital_pct", 0.20))  # 20% = 200,000 THB
        self.board_lot = int(cfg.get("board_lot_size", 100))
        self.trailing_ema = int(cfg.get("trailing_ema", 21))

    def calculate_position(self, ticker: str, df: pd.DataFrame, entry_price: float) -> Optional[Dict]:
        if entry_price <= 0 or len(df) < 15:
            return None

        # 1. Calculate Initial Stop Loss (1R)
        low_10 = float(df["Low"].iloc[-10:].min())
        high = df["High"]
        low = df["Low"]
        close = df["Close"]
        prev_close = close.shift(1)
        tr = pd.concat([high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
        atr = float(tr.ewm(span=14, adjust=False).mean().iloc[-1])
        vol_buffer = max(0.05, 0.5 * atr)

        raw_sl = low_10 - vol_buffer
        min_sl = entry_price * 0.92  # max 8% stop
        max_sl = entry_price * 0.975  # min 2.5% stop
        bounded_sl = max(min_sl, min(max_sl, raw_sl))
        sl = round_to_set_tick(bounded_sl, round_mode="down")
        if sl >= entry_price:
            sl = step_tick_down(entry_price)

        risk_per_share = round(entry_price - sl, 2)
        if risk_per_share <= 0:
            sl = step_tick_down(round_to_set_tick(entry_price * 0.95, round_mode="down"))
            risk_per_share = round(entry_price - sl, 2)

        # 2. Position Sizing
        risk_budget = self.total_capital * self.risk_pct  # 5,000 THB
        max_capital = self.total_capital * self.max_cap_pct  # 200,000 THB

        raw_shares = int(risk_budget / risk_per_share) if risk_per_share > 0 else 0
        lot_shares = (raw_shares // self.board_lot) * self.board_lot

        # Rejection if budget cannot buy 100 shares
        if lot_shares < self.board_lot:
            print(f"[RiskManager] {ticker} ถูกปฏิเสธ: งบเสี่ยง 0.5% ({risk_budget:,.0f} ฿) ไม่พอซื้อขั้นต่ำ 100 หุ้น")
            return None

        cap_shares = (int(max_capital / entry_price) // self.board_lot) * self.board_lot
        shares = min(lot_shares, cap_shares)
        if shares < self.board_lot:
            return None

        pos_capital = round(shares * entry_price, 2)

        # Targets snapped to legal ticks
        target_3r = round_to_set_tick(entry_price + 3.0 * risk_per_share, round_mode="up")
        target_5r = round_to_set_tick(entry_price + 5.0 * risk_per_share, round_mode="up")

        return {
            "ticker": ticker,
            "entry_price": entry_price,
            "current_sl": sl,
            "stop_loss": sl,
            "risk_per_share": risk_per_share,
            "shares": shares,
            "current_shares": shares,
            "initial_shares": shares,
            "target_3r": target_3r,
            "target_5r": target_5r,
            "position_capital": pos_capital,
            "tp1_hit": False,
            "tp2_hit": False
        }
