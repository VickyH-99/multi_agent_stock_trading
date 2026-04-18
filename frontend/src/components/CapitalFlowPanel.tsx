'use client';
import { clsx } from 'clsx';
import type { CapitalFlow } from '@/types/api';
import { formatAmount, formatNetFlow } from '@/lib/format';

interface CapitalFlowPanelProps {
  flow: CapitalFlow | null;
}

interface FlowRowProps {
  label: string;
  inflow: number;
  outflow: number;
  net?: number;
}

function FlowBar({ inflow, outflow }: { inflow: number; outflow: number }) {
  const total = inflow + outflow;
  if (total <= 0) return <div className="h-2 bg-border rounded-full" />;
  const infPct = (inflow / total) * 100;
  return (
    <div className="h-1.5 bg-fall/40 rounded-full overflow-hidden flex">
      <div
        className="h-full bg-rise/70 rounded-full"
        style={{ width: `${infPct}%` }}
      />
    </div>
  );
}

function FlowRow({ label, inflow, outflow, net }: FlowRowProps) {
  const netVal = net !== undefined ? net : inflow - outflow;
  const isPositive = netVal >= 0;
  return (
    <div className="py-1.5 border-b border-border/30 last:border-b-0">
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs text-text-secondary">{label}</span>
        <span className={clsx(
          'text-xs font-mono font-semibold',
          isPositive ? 'text-rise' : 'text-fall'
        )}>
          {formatNetFlow(netVal)}
        </span>
      </div>
      <div className="flex items-center gap-2">
        <FlowBar inflow={Math.abs(inflow)} outflow={Math.abs(outflow)} />
      </div>
      <div className="flex justify-between text-[10px] text-text-secondary mt-0.5 font-mono">
        <span className="text-rise">+{formatAmount(inflow)}</span>
        <span className="text-fall">-{formatAmount(outflow)}</span>
      </div>
    </div>
  );
}

export function CapitalFlowPanel({ flow }: CapitalFlowPanelProps) {
  if (!flow) {
    return (
      <div className="bg-card-bg border border-border rounded-xl p-4">
        <h3 className="text-sm font-semibold text-text-primary mb-2">资金流向</h3>
        <div className="text-text-secondary text-xs">暂无资金流数据</div>
      </div>
    );
  }

  const mainNet = flow.main_net_inflow;
  const isMainPositive = mainNet >= 0;

  return (
    <div className="bg-card-bg border border-border rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-text-primary">资金流向</h3>
        <span className={clsx(
          'text-xs font-mono font-bold',
          isMainPositive ? 'text-rise' : 'text-fall'
        )}>
          今日主力: {flow.main_net_inflow_fmt}
        </span>
      </div>

      {/* Main flow summary */}
      <div className={clsx(
        'rounded-lg p-3 mb-3 text-center',
        isMainPositive ? 'bg-rise/10 border border-rise/20' : 'bg-fall/10 border border-fall/20'
      )}>
        <div className={clsx(
          'text-2xl font-bold font-mono',
          isMainPositive ? 'text-rise' : 'text-fall'
        )}>
          {flow.main_net_inflow_fmt}
        </div>
        <div className="text-xs text-text-secondary mt-0.5">
          {isMainPositive ? '主力净流入' : '主力净流出'}
        </div>
      </div>

      {/* Detailed breakdown */}
      <div>
        <FlowRow
          label="超大单"
          inflow={flow.super_large_inflow}
          outflow={flow.super_large_outflow}
        />
        <FlowRow
          label="大单"
          inflow={flow.large_inflow}
          outflow={flow.large_outflow}
        />
        <FlowRow
          label="中单"
          inflow={flow.medium_inflow}
          outflow={flow.medium_outflow}
        />
        <FlowRow
          label="小单"
          inflow={flow.small_inflow}
          outflow={flow.small_outflow}
        />
      </div>
    </div>
  );
}
