"""
RSI Oversold Bounce Strategy
A mean reversion strategy using the Relative Strength Index (RSI).

Entry: Buy when RSI drops below oversold threshold (30) and shows reversal
Exit: Sell when RSI reaches overbought levels (70) or on stop loss

Author: Agentic Trading ML
Version: 1.0.0
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Signal:
    """Trading signal data class"""
    timestamp: datetime
    symbol: str
    action: str
    price: float
    confidence: float = 1.0
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class Trade:
    """Trade record data class"""
    entry_date: datetime
    exit_date: Optional[datetime]
    symbol: str
    entry_price: float
    exit_price: Optional[float]
    quantity: float
    pnl: float = 0.0
    pnl_pct: float = 0.0
    duration_days: int = 0


class RSIOversoldBounceStrategy:
    """
    RSI Oversold Bounce Strategy
    
    This mean reversion strategy identifies oversold conditions using the Relative 
    Strength Index (RSI). It enters long positions when RSI drops below the 
    oversold threshold (default 30) and shows signs of reversal. Exits are 
    triggered when RSI reaches overbought levels (default 70).
    
    Best suited for:
    - Sideways or choppy markets
    - Mean-reverting assets
    - Short-term swing trading
    
    Avoid in:
    - Strong trending markets (bull or bear)
    - High momentum breakouts
    
    Parameters:
    -----------
    rsi_period : int
        RSI calculation period (default: 14)
    oversold_threshold : float
        RSI level considered oversold (default: 30)
    overbought_threshold : float
        RSI level considered overbought (default: 70)
    reversal_confirmation_periods : int
        Number of periods RSI must rise to confirm reversal (default: 2)
    stop_loss_pct : float
        Stop loss percentage (default: 0.05)
    take_profit_pct : float
        Take profit percentage (default: 0.15)
    position_size_pct : float
        Position size as percentage of equity (default: 0.25)
    max_positions : int
        Maximum number of concurrent positions (default: 4)
    
    Example:
    --------
    >>> import pandas as pd
    >>> from rsi_oversold_strategy import RSIOversoldBounceStrategy
    >>> 
    >>> # Load data
    >>> df = pd.read_csv('spy_data.csv', parse_dates=['date'])
    >>> df.set_index('date', inplace=True)
    >>> 
    >>> # Initialize strategy
    >>> strategy = RSIOversoldBounceStrategy(
    ...     rsi_period=14,
    ...     oversold_threshold=30,
    ...     overbought_threshold=70,
    ...     stop_loss_pct=0.05
    ... )
    >>> 
    >>> # Run backtest
    >>> results = strategy.backtest(df, initial_capital=100000)
    >>> print(f"Total Return: {results['total_return']:.2%}")
    >>> print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    >>> print(f"Win Rate: {results['win_rate']:.1%}")
    """
    
    def __init__(
        self,
        rsi_period: int = 14,
        oversold_threshold: float = 30.0,
        overbought_threshold: float = 70.0,
        reversal_confirmation_periods: int = 2,
        stop_loss_pct: float = 0.05,
        take_profit_pct: float = 0.15,
        position_size_pct: float = 0.25,
        max_positions: int = 4,
        min_volume: int = 500_000,
        min_price: float = 5.0
    ):
        self.rsi_period = rsi_period
        self.oversold_threshold = oversold_threshold
        self.overbought_threshold = overbought_threshold
        self.reversal_confirmation_periods = reversal_confirmation_periods
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.position_size_pct = position_size_pct
        self.max_positions = max_positions
        self.min_volume = min_volume
        self.min_price = min_price
        
        self.positions: Dict[str, Dict] = {}
        self.signals: List[Signal] = []
        self.trades: List[Trade] = []
    
    def calculate_rsi(self, data: pd.Series, period: int = 14) -> pd.Series:
        """
        Calculate Relative Strength Index (RSI)
        
        RSI = 100 - (100 / (1 + RS))
        where RS = Average Gain / Average Loss
        
        Parameters:
        -----------
        data : pd.Series
            Price series (typically closing prices)
        period : int
            RSI lookback period
            
        Returns:
        --------
        pd.Series : RSI values (0-100)
        """
        # Calculate price changes
        delta = data.diff()
        
        # Separate gains and losses
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        # Calculate average gain and loss using Wilder's smoothing
        avg_gain = gain.ewm(com=period-1, min_periods=period).mean()
        avg_loss = loss.ewm(com=period-1, min_periods=period).mean()
        
        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def detect_oversold_reversal(
        self, 
        rsi: pd.Series, 
        oversold_threshold: float = 30.0,
        confirmation_periods: int = 2
    ) -> pd.Series:
        """
        Detect oversold conditions with reversal confirmation
        
        Entry signal requires:
        1. RSI below oversold threshold
        2. RSI rising for 'confirmation_periods' consecutive bars
        
        Parameters:
        -----------
        rsi : pd.Series
            RSI values
        oversold_threshold : float
            Level considered oversold
        confirmation_periods : int
            Number of consecutive rising periods required
            
        Returns:
        --------
        pd.Series : Boolean series with entry signals
        """
        # RSI is below oversold threshold
        oversold = rsi < oversold_threshold
        
        # RSI is rising (current > previous)
        rsi_rising = rsi > rsi.shift(1)
        
        # RSI has been rising for confirmation_periods
        rising_streak = rsi_rising.rolling(window=confirmation_periods).sum() == confirmation_periods
        
        # Combined signal: oversold AND rising streak
        signal = oversold & rising_streak
        
        return signal
    
    def detect_overbought(
        self, 
        rsi: pd.Series, 
        overbought_threshold: float = 70.0
    ) -> pd.Series:
        """
        Detect overbought conditions for exit signals
        
        Parameters:
        -----------
        rsi : pd.Series
            RSI values
        overbought_threshold : float
            Level considered overbought
            
        Returns:
        --------
        pd.Series : Boolean series with exit signals
        """
        return rsi > overbought_threshold
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals for the given price data.
        
        Parameters:
        -----------
        data : pd.DataFrame
            DataFrame with columns: 'open', 'high', 'low', 'close', 'volume'
            Index should be datetime
            
        Returns:
        --------
        pd.DataFrame : Original data with added columns:
            - 'rsi': RSI values
            - 'oversold': Boolean indicating oversold condition
            - 'reversal': Boolean indicating RSI reversal
            - 'overbought': Boolean indicating overbought condition
            - 'signal': Combined signal (1 = buy, -1 = sell, 0 = hold)
        """
        df = data.copy()
        
        # Calculate RSI
        df['rsi'] = self.calculate_rsi(df['close'], self.rsi_period)
        
        # Detect oversold with reversal
        df['oversold_reversal'] = self.detect_oversold_reversal(
            df['rsi'], 
            self.oversold_threshold,
            self.reversal_confirmation_periods
        )
        
        # Detect overbought
        df['overbought'] = self.detect_overbought(
            df['rsi'], 
            self.overbought_threshold
        )
        
        # Generate signals
        df['signal'] = 0
        df.loc[df['oversold_reversal'], 'signal'] = 1  # Buy signal
        df.loc[df['overbought'], 'signal'] = -1  # Sell signal
        
        # Apply filters
        if 'volume' in df.columns:
            low_volume = df['volume'] < self.min_volume
            df.loc[low_volume, 'signal'] = 0
        
        low_price = df['close'] < self.min_price
        df.loc[low_price, 'signal'] = 0
        
        return df
    
    def backtest(
        self, 
        data: pd.DataFrame, 
        initial_capital: float = 100000.0,
        commission: float = 0.001,
        slippage: float = 0.001
    ) -> Dict:
        """
        Run backtest on historical data.
        
        Parameters:
        -----------
        data : pd.DataFrame
            Price data with OHLCV columns
        initial_capital : float
            Starting capital (default: 100000)
        commission : float
            Commission per trade as decimal (default: 0.001 = 0.1%)
        slippage : float
            Slippage per trade as decimal (default: 0.001 = 0.1%)
            
        Returns:
        --------
        Dict : Backtest results including performance metrics
        """
        # Generate signals
        df = self.generate_signals(data)
        
        # Initialize tracking
        capital = initial_capital
        equity_curve = []
        trades = []
        position = None
        
        for timestamp, row in df.iterrows():
            if pd.isna(row['rsi']):
                equity_curve.append({
                    'date': timestamp,
                    'equity': capital,
                    'drawdown': 0
                })
                continue
            
            # Entry signal
            if row['signal'] == 1 and position is None:
                position_value = capital * self.position_size_pct
                shares = position_value / row['close']
                
                entry_price = row['close'] * (1 + slippage)
                commission_cost = position_value * commission
                
                position = {
                    'entry_date': timestamp,
                    'entry_price': entry_price,
                    'shares': shares,
                    'stop_loss': entry_price * (1 - self.stop_loss_pct),
                    'take_profit': entry_price * (1 + self.take_profit_pct)
                }
                
                capital -= commission_cost
            
            # Exit logic
            elif position is not None:
                current_price = row['close']
                exit_reason = None
                exit_price = current_price
                
                if current_price <= position['stop_loss']:
                    exit_reason = 'stop_loss'
                    exit_price = position['stop_loss']
                elif current_price >= position['take_profit']:
                    exit_reason = 'take_profit'
                    exit_price = position['take_profit']
                elif row['signal'] == -1:
                    exit_reason = 'rsi_overbought'
                    exit_price = current_price * (1 - slippage)
                
                if exit_reason:
                    position_value = position['shares'] * exit_price
                    commission_cost = position_value * commission
                    
                    gross_pnl = position['shares'] * (exit_price - position['entry_price'])
                    net_pnl = gross_pnl - commission_cost * 2
                    
                    trade = Trade(
                        entry_date=position['entry_date'],
                        exit_date=timestamp,
                        symbol='UNKNOWN',
                        entry_price=position['entry_price'],
                        exit_price=exit_price,
                        quantity=position['shares'],
                        pnl=net_pnl,
                        pnl_pct=(exit_price - position['entry_price']) / position['entry_price'],
                        duration_days=(timestamp - position['entry_date']).days
                    )
                    trades.append(trade)
                    
                    capital += net_pnl
                    position = None
            
            # Calculate equity
            if position:
                position_value = position['shares'] * row['close']
                current_equity = capital + position_value
            else:
                current_equity = capital
            
            peak_equity = max([e['equity'] for e in equity_curve]) if equity_curve else current_equity
            drawdown = (peak_equity - current_equity) / peak_equity if peak_equity > 0 else 0
            
            equity_curve.append({
                'date': timestamp,
                'equity': current_equity,
                'drawdown': drawdown
            })
        
        # Calculate metrics
        equity_df = pd.DataFrame(equity_curve)
        total_return = (equity_df['equity'].iloc[-1] - initial_capital) / initial_capital
        
        equity_df['daily_return'] = equity_df['equity'].pct_change()
        avg_return = equity_df['daily_return'].mean()
        std_return = equity_df['daily_return'].std()
        sharpe_ratio = (avg_return / std_return) * np.sqrt(252) if std_return > 0 else 0
        
        max_drawdown = equity_df['drawdown'].max()
        
        if trades:
            winning_trades = [t for t in trades if t.pnl > 0]
            win_rate = len(winning_trades) / len(trades)
            avg_win = np.mean([t.pnl_pct for t in winning_trades]) if winning_trades else 0
            losing_trades = [t for t in trades if t.pnl <= 0]
            avg_loss = np.mean([t.pnl_pct for t in losing_trades]) if losing_trades else 0
        else:
            win_rate = 0
            avg_win = 0
            avg_loss = 0
        
        return {
            'total_return': total_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'total_trades': len(trades),
            'equity_curve': equity_curve,
            'trades': trades
        }


if __name__ == "__main__":
    print("RSI Oversold Bounce Strategy")
    print("=" * 50)
    print()
    print("Mean reversion strategy using RSI oscillator.")
    print()
    print("Entry: RSI < 30 (oversold) + RSI rising for 2 periods")
    print("Exit: RSI > 70 (overbought) or stop loss")
    print()
    print("Best for: Sideways markets, mean-reverting assets")
    print("Avoid: Strong trending markets")
    print()
    print("Usage:")
    print("  from rsi_oversold_strategy import RSIOversoldBounceStrategy")
    print("  strategy = RSIOversoldBounceStrategy()")
    print("  results = strategy.backtest(data)")
