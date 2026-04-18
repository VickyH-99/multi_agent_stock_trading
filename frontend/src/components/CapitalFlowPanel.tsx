'use client';
import { clsx } from 'clsx';
import type { CapitalFlow } from '@/types/api';
import { formatAmount, formatNetFlow } from '@/lib/format';
import { DataStatusBadge } from './DataStatusBadge';

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
  if (total <= 0) {
    return <div className="h-2 rounded-full bg-border/40" />;
  }
  const inflowPct = Math.max(6, (inflow / total) * 100);
  const outflowPct = Math.max(6, (outflow / total) * 100);
  return (
    <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-2">
      <div className="h-2 rounded-full bg-border/40 overflow-hidden">
        <div
          className="ml-auto h-full rounded-full bg-fall/75"
          style={{ width: `${outflow > 0 ? outflowPct : 0}%` }}
        />
      </div>
      <div className="h-3 w-px bg-border/80" />
      <div className="h-2 rounded-full bg-border/40 overflow-hidden">
        <div
          className="h-full rounded-full bg-rise/75"
          style={{ width: `${inflow > 0 ? inflowPct : 0}%` }}
        />
      </div>
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
        <span className="text-fall">流出 {formatAmount(outflow)}</span>
        <span className="text-rise">流入 {formatAmount(inflow)}</span>
      </div>
    </div>
  );
}

export function CapitalFlowPanel({ flow }: CapitalFlowPanelProps) {
  if (!flow) {
    return (
      <div className="bg-card-bg border border-border rounded-xl p-4">
        <h3 className="text-sm font-semibold text-text-primary mb-2">资金流向</h3>
        <div className="text-text-secondary text-xs leading-5">
          暂无资金流数据，系统会继续尝试从东方财富和 AkShare 获取主力资金明细。
        </div>
      </div>
    );
  }

  const mainNet = flow.main_net_inflow;
  const isMainPositive = mainNet >= 0;
  const bigOrderNet =
    flow.super_large_inflow - flow.super_large_outflow +
    flow.large_inflow - flow.large_outflow;

  return (
    <div className="bg-card-bg border border-border rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h3 className="text-sm font-semibold text-text-primary">资金流向</h3>
          <div className="mt-1">
            <DataStatusBadge status={flow.data_status} showSource />
          </div>
        </div>
        <span className={clsx(
          'text-xs font-mono font-bold',
          isMainPositive ? 'text-rise' : 'text-fall'
        )}>
          今日主力: {flow.main_net_inflow_fmt}
        </span>
      </div>

      {/* Main flow summary */}
      <div className="grid gap-3 md:grid-cols-2 mb-3">
        <div className={clsx(
          'rounded-lg p-3 text-center',
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

        <div className="rounded-lg border border-border/60 bg-dark-bg/30 p-3">
          <div className="flex items-center justify-between text-xs">
            <span className="text-text-secondary">大单偏向</span>
            <span className={clsx('font-mono font-semibold', bigOrderNet >= 0 ? 'text-rise' : 'text-fall')}>
              {formatNetFlow(bigOrderNet)}
            </span>
          </div>
          <div className="mt-2 text-[11px] leading-5 text-text-secondary">
            超大单和大单代表更偏机构与主力方向，数值越大说明抢筹越明显。
          </div>
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
