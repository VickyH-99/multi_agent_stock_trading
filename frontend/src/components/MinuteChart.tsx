'use client';
import { useMemo } from 'react';
import dynamic from 'next/dynamic';
import type { Quote, MinuteData } from '@/types/api';
import { DataStatusBadge } from './DataStatusBadge';

// Dynamic import ECharts to avoid SSR issues
const ReactECharts = dynamic(() => import('echarts-for-react'), { ssr: false });

interface StockChartProps {
  quote: Quote | null;
  minuteData: MinuteData | null;
}

export function MinuteChart({ quote, minuteData }: StockChartProps) {
  const option = useMemo(() => {
    if (!minuteData || !minuteData.times.length) return null;

    const prevClose = quote?.prev_close ?? minuteData.prices[0];

    return {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        backgroundColor: '#1c2128',
        borderColor: '#30363d',
        textStyle: { color: '#e6edf3', fontSize: 12 },
        formatter: (params: any[]) => {
          if (!params.length) return '';
          const p = params[0];
          const vol = minuteData.volumes[p.dataIndex] ?? 0;
          const pct = prevClose > 0
            ? (((p.value as number) - prevClose) / prevClose * 100).toFixed(2)
            : '0.00';
          const sign = parseFloat(pct) >= 0 ? '+' : '';
          return `
            <div style="font-family: monospace; font-size: 12px;">
              <div>${p.name}</div>
              <div>价格: <b>${(p.value as number).toFixed(2)}</b></div>
              <div>涨幅: <b style="color:${parseFloat(pct) >= 0 ? '#f23645' : '#089981'}">${sign}${pct}%</b></div>
              <div>成交量: ${(vol / 100).toFixed(0)}手</div>
            </div>
          `;
        },
      },
      grid: [
        { left: 60, right: 10, top: 10, bottom: 60 },
        { left: 60, right: 10, top: '75%', bottom: 10 },
      ],
      xAxis: [
        {
          type: 'category',
          data: minuteData.times,
          gridIndex: 0,
          axisLine: { lineStyle: { color: '#30363d' } },
          axisLabel: { color: '#8b949e', fontSize: 10 },
          splitLine: { show: false },
          axisTick: { show: false },
        },
        {
          type: 'category',
          data: minuteData.times,
          gridIndex: 1,
          axisLine: { lineStyle: { color: '#30363d' } },
          axisLabel: { show: false },
          axisTick: { show: false },
        },
      ],
      yAxis: [
        {
          type: 'value',
          gridIndex: 0,
          scale: true,
          axisLine: { show: false },
          axisTick: { show: false },
          splitLine: { lineStyle: { color: '#21262d', type: 'dashed' } },
          axisLabel: {
            color: '#8b949e',
            fontSize: 10,
            formatter: (v: number) => v.toFixed(2),
          },
        },
        {
          type: 'value',
          gridIndex: 1,
          axisLine: { show: false },
          axisTick: { show: false },
          splitLine: { lineStyle: { color: '#21262d', type: 'dashed' } },
          axisLabel: {
            color: '#8b949e',
            fontSize: 9,
            formatter: (v: number) => v >= 1e4 ? `${(v / 1e4).toFixed(0)}万` : String(v),
          },
        },
      ],
      series: [
        {
          name: '价格',
          type: 'line',
          data: minuteData.prices,
          xAxisIndex: 0,
          yAxisIndex: 0,
          smooth: false,
          symbol: 'none',
          lineStyle: { color: '#f23645', width: 1.5 },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(242,54,69,0.18)' },
                { offset: 1, color: 'rgba(242,54,69,0.02)' },
              ],
            },
          },
          markLine: prevClose > 0 ? {
            silent: true,
            symbol: 'none',
            data: [{ yAxis: prevClose }],
            lineStyle: { color: '#8b949e', type: 'dashed', width: 1 },
            label: { show: false },
          } : undefined,
        },
        {
          name: '均价',
          type: 'line',
          data: minuteData.avg_prices,
          xAxisIndex: 0,
          yAxisIndex: 0,
          smooth: false,
          symbol: 'none',
          lineStyle: { color: '#f0b90b', width: 1, type: 'dashed' },
        },
        {
          name: '成交量',
          type: 'bar',
          data: minuteData.volumes.map((v, i) => ({
            value: v,
            itemStyle: {
              color: minuteData.prices[i] >= (minuteData.prices[i - 1] ?? prevClose)
                ? 'rgba(242,54,69,0.7)' : 'rgba(8,153,129,0.7)',
            },
          })),
          xAxisIndex: 1,
          yAxisIndex: 1,
        },
      ],
    };
  }, [minuteData, quote]);

  if (!option) {
    return (
      <div className="flex items-center justify-center h-64 text-text-secondary text-sm">
        暂无分时数据
      </div>
    );
  }

  return (
    <div className="w-full">
      <ReactECharts
        option={option}
        style={{ height: '320px', width: '100%' }}
        opts={{ renderer: 'canvas' }}
        notMerge={false}
      />
      {minuteData && (
        <div className="flex justify-end px-2 pb-1">
          <DataStatusBadge status={minuteData.data_status} showSource />
        </div>
      )}
    </div>
  );
}
