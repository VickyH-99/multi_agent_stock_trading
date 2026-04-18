'use client';
import { clsx } from 'clsx';
import type { TechnicalSignals, StockScore } from '@/types/api';
import { getGradeColor, getRecColor, getRiskStyle, getRsiColor } from '@/lib/format';

interface SignalBoardProps {
  technical: TechnicalSignals | null;
  score: StockScore | null;
}

function Tag({ children, active, positive }: { children: React.ReactNode; active?: boolean; positive?: boolean }) {
  return (
    <span className={clsx(
      'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border',
      active
        ? positive !== false
          ? 'bg-rise/15 border-rise/40 text-rise'
          : 'bg-fall/15 border-fall/40 text-fall'
        : 'bg-border/30 border-border/30 text-text-secondary opacity-50'
    )}>
      {children}
    </span>
  );
}

export function SignalBoard({ technical, score }: SignalBoardProps) {
  return (
    <div className="space-y-4">
      {/* Composite Score */}
      {score && (
        <div className="bg-card-bg border border-border rounded-xl p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-text-primary">综合评分</h3>
            <span className={clsx(
              'text-xs font-bold px-2 py-0.5 rounded',
              getGradeColor(score.grade)
            )}>
              {score.grade}
            </span>
          </div>

          {/* Score bar */}
          <div className="mb-3">
            <div className="flex justify-between text-xs text-text-secondary mb-1">
              <span>-100</span>
              <span className={clsx(
                'font-mono text-base font-bold',
                score.composite_score >= 0 ? 'text-rise' : 'text-fall'
              )}>
                {score.composite_score > 0 ? '+' : ''}{score.composite_score}
              </span>
              <span>+100</span>
            </div>
            <div className="h-2 bg-border rounded-full overflow-hidden">
              <div
                className={clsx(
                  'h-full rounded-full transition-all duration-500',
                  score.composite_score >= 0 ? 'bg-rise' : 'bg-fall'
                )}
                style={{
                  width: `${Math.abs(score.composite_score)}%`,
                  marginLeft: score.composite_score < 0
                    ? `${50 + score.composite_score}%` : '50%',
                }}
              />
            </div>
          </div>

          <div className="flex items-center justify-between">
            <span className={clsx(
              'text-sm font-medium px-3 py-1 rounded-full',
              getRecColor(score.recommendation)
            )}>
              {score.recommendation}
            </span>
            <div className="text-right text-xs text-text-secondary">
              <div>技术: {score.technical_score >= 0 ? '+' : ''}{score.technical_score}</div>
              <div>资金: {score.capital_flow_score >= 0 ? '+' : ''}{score.capital_flow_score}</div>
            </div>
          </div>

          {/* Risk warnings */}
          {score.risk_warnings.length > 0 && (
            <div className={clsx(
              'mt-3 rounded-lg p-2 border',
              getRiskStyle(score.risk_level).border,
              getRiskStyle(score.risk_level).bg,
            )}>
              <div className="text-xs font-semibold text-text-secondary mb-1">
                ⚠️ 风险提示 ({score.risk_level})
              </div>
              {score.risk_warnings.map((w, i) => (
                <div key={i} className="text-xs text-text-secondary leading-5">
                  · {w}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Technical Signals */}
      {technical && (
        <div className="bg-card-bg border border-border rounded-xl p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-text-primary">技术信号</h3>
            <span className={clsx(
              'text-xs font-mono',
              technical.signal_score >= 0 ? 'text-rise' : 'text-fall'
            )}>
              {technical.signal_label}
            </span>
          </div>

          {/* MA tags */}
          <div className="mb-3">
            <div className="text-xs text-text-secondary mb-1.5">均线</div>
            <div className="flex flex-wrap gap-1.5">
              <Tag active={technical.above_ma5}>站上MA5</Tag>
              <Tag active={technical.above_ma10}>站上MA10</Tag>
              <Tag active={technical.above_ma20}>站上MA20</Tag>
              <Tag active={technical.above_ma60}>站上MA60</Tag>
              <Tag active={technical.golden_cross} positive={true}>金叉</Tag>
              <Tag active={technical.death_cross} positive={false}>死叉</Tag>
            </div>
          </div>

          {/* Breakout */}
          <div className="mb-3">
            <div className="text-xs text-text-secondary mb-1.5">突破</div>
            <div className="flex flex-wrap gap-1.5">
              <Tag active={technical.price_breakout}>价格突破</Tag>
              <Tag active={technical.volume_surge}>量能放大 ×{technical.volume_ratio.toFixed(1)}</Tag>
              <Tag active={technical.macd_golden_cross}>MACD金叉</Tag>
              <Tag active={technical.near_support} positive={false}>接近支撑</Tag>
            </div>
          </div>

          {/* Indicators */}
          <div className="space-y-2">
            {/* RSI */}
            <div className="flex items-center justify-between">
              <span className="text-xs text-text-secondary">RSI(14)</span>
              <div className="flex items-center gap-2">
                <div className="w-24 h-1.5 bg-border rounded-full overflow-hidden">
                  <div
                    className={clsx(
                      'h-full rounded-full',
                      technical.rsi_14 >= 70 ? 'bg-rise' : technical.rsi_14 <= 30 ? 'bg-fall' : 'bg-accent-blue'
                    )}
                    style={{ width: `${technical.rsi_14}%` }}
                  />
                </div>
                <span className={clsx('text-xs font-mono', getRsiColor(technical.rsi_14))}>
                  {technical.rsi_14.toFixed(1)}
                </span>
                {technical.rsi_signal !== 'neutral' && (
                  <span className={clsx(
                    'text-[10px] px-1 rounded',
                    technical.rsi_signal === 'overbought' ? 'text-rise bg-rise/10' : 'text-fall bg-fall/10'
                  )}>
                    {technical.rsi_signal === 'overbought' ? '超买' : '超卖'}
                  </span>
                )}
              </div>
            </div>

            {/* MACD */}
            <div className="flex items-center justify-between">
              <span className="text-xs text-text-secondary">MACD</span>
              <div className="flex items-center gap-2 font-mono text-xs">
                <span className={technical.macd >= 0 ? 'text-rise' : 'text-fall'}>
                  {technical.macd.toFixed(3)}
                </span>
                <span className="text-text-secondary">/</span>
                <span className={technical.macd_hist >= 0 ? 'text-rise' : 'text-fall'}>
                  {technical.macd_hist > 0 ? '+' : ''}{technical.macd_hist.toFixed(3)}
                </span>
              </div>
            </div>

            {/* Bollinger */}
            <div>
              <div className="flex items-center justify-between mb-0.5">
                <span className="text-xs text-text-secondary">布林带位置</span>
                <span className="text-xs font-mono text-text-primary">
                  {(technical.bb_position * 100).toFixed(0)}%
                </span>
              </div>
              <div className="h-1.5 bg-border rounded-full overflow-hidden">
                <div
                  className={clsx(
                    'h-full w-1 rounded-full',
                    technical.bb_position > 0.8 ? 'bg-rise' : technical.bb_position < 0.2 ? 'bg-fall' : 'bg-accent-blue'
                  )}
                  style={{ marginLeft: `${technical.bb_position * 100}%`, transform: 'translateX(-50%)' }}
                />
              </div>
              <div className="flex justify-between text-[10px] text-text-secondary mt-0.5">
                <span>{technical.bb_lower.toFixed(2)}</span>
                <span>{technical.bb_middle.toFixed(2)}</span>
                <span>{technical.bb_upper.toFixed(2)}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
