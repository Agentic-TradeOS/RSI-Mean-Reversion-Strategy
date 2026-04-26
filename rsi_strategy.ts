export interface RSIConfig {
  rsiPeriod: number;
  oversoldThreshold: number;
  overboughtThreshold: number;
  stopLossPct: number;
  takeProfitPct: number;
}

export const defaultConfig: RSIConfig = {
  rsiPeriod: 14,
  oversoldThreshold: 30,
  overboughtThreshold: 70,
  stopLossPct: 0.05,
  takeProfitPct: 0.15,
};

export function calculateRSI(closes: number[], period = 14): number[] {
  const rsi: number[] = new Array(period).fill(NaN);
  let avgGain = 0;
  let avgLoss = 0;

  for (let i = 1; i <= period; i++) {
    const change = closes[i] - closes[i - 1];
    if (change > 0) avgGain += change;
    else avgLoss += Math.abs(change);
  }
  avgGain /= period;
  avgLoss /= period;

  for (let i = period; i < closes.length; i++) {
    const change = closes[i] - closes[i - 1];
    const gain = change > 0 ? change : 0;
    const loss = change < 0 ? Math.abs(change) : 0;
    avgGain = (avgGain * (period - 1) + gain) / period;
    avgLoss = (avgLoss * (period - 1) + loss) / period;
    const rs = avgLoss === 0 ? 100 : avgGain / avgLoss;
    rsi.push(100 - 100 / (1 + rs));
  }

  return rsi;
}

export function generateSignals(
  closes: number[],
  config: RSIConfig = defaultConfig
): Array<{ index: number; signal: 1 | -1 | 0; rsi: number }> {
  const rsiValues = calculateRSI(closes, config.rsiPeriod);

  return rsiValues.map((rsi, i) => {
    if (isNaN(rsi)) return { index: i, signal: 0 as const, rsi };
    if (rsi < config.oversoldThreshold) return { index: i, signal: 1 as const, rsi };
    if (rsi > config.overboughtThreshold) return { index: i, signal: -1 as const, rsi };
    return { index: i, signal: 0 as const, rsi };
  });
}
