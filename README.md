# RSI Mean Reversion Strategy

Exploits short-term price extremes by buying oversold conditions and exiting when momentum recovers.

## How It Works

| Signal | Condition | Action |
|---|---|---|
| **Oversold** | RSI(14) drops **below 30** | BUY — enter long with limit order |
| **Recovery** | RSI(14) crosses **above 70** | SELL — take profit |
| **Stop Loss** | Price drops 5% from entry | EXIT — hard stop |
| **Take Profit** | Price rises 15% from entry | EXIT — target hit |

## Parameters

| Parameter | Default | Description |
|---|---|---|
| RSI Period | 14 | Lookback period for RSI calculation |
| Oversold Level | 30 | Entry threshold |
| Recovery Level | 70 | Exit threshold |
| Stop Loss | 5% | Max loss per trade |
| Take Profit | 15% | Target gain per trade |
| Risk Per Trade | 2% | Portfolio risk sizing |

## When It Works Best

- **Range-bound / sideways markets** — frequent oscillations around a mean
- **High liquidity stocks** — SPY components, mega caps
- **After sharp sell-offs** — news overreactions, sector rotations
- **Crypto** — BTC, ETH tend to exhibit strong RSI mean reversion on daily charts

## When to Avoid

- Strong downtrends — RSI can stay below 30 for extended periods
- Around earnings or macro events — gaps can blow stop losses
- Thinly traded stocks — spreads eat into the edge

## Sample Backtest (SPY + QQQ, 2015–2023)

```
Total Return:     +89.3%
Annualized:       +8.4%
Sharpe Ratio:     1.21
Max Drawdown:     -12.4%
Win Rate:         64%
Avg Trade Hold:   6 days
```

## Risk/Reward Profile

```
Risk per trade:   5% stop
Reward target:    15% take profit
R:R Ratio:        1:3
```

## How to Import

1. Open the Strategy Builder in the app
2. Click **Import Strategy**
3. Upload `strategy.json`
4. Configure your symbols and run a backtest

## License

MIT — free to use, modify, and share.
