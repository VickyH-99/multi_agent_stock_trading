'use client';
import { useMemo } from 'react';
import dynamic from 'next/dynamic';
import type { HistoryBar } from '@/types/api';

const ReactECharts = dynamic(() => import('echarts-for-react'), { ssr: false });

interface CandlestickChartProps {
  data: HistoryBar[];
  showMA?: boolean;
  loading?: boolean;
  errorMessage?: string | null;
  periodLabel?: string;
}

function calcMA(data: number[], period: number): (number | null)[] {
  const result: (number | null)[] = [];
  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) { result.push(null); continue; }
    const sum = data.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0);
    result.push(parseFloat((sum / period).toFixed(3)));
  }
  return result;
}

export function CandlestickChart({
  data,
  showMA = true,
  loading = false,
  errorMessage = null,
  periodLabel = 'K线',
}: CandlestickChartProps) {
  const option = useMemo(() => {
    if (!data.length) return null;

    const dates = data.map(d => d.date);
    const ohlc = data.map(d => [d.open, d.close, d.low, d.high]);
    const volumes = data.map(d => d.volume);
    const closes = data.map(d => d.close);
    const ma5 = calcMA(closes, 5);
    const ma10 = calcMA(closes, 10);
    const ma20 = calcMA(closes, 20);
    const zoomStart = data.length > 180 ? 72 : data.length > 90 ? 45 : 0;

    return {
      backgroundColor: 'transparent',
      animation: false,
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross' },
        backgroundColor: '#1c2128',
        borderColor: '#30363d',
        textStyle: { color: '#e6edf3', fontSize: 11 },
        formatter: (params: any[]) => {
          const k = params.find(p => p.seriesName === 'K线');
          if (!k) return '';
          const [o, c, l, h] = k.value;
          const pct = data[k.dataIndex]?.change_pct ?? 0;
          const sign = pct >= 0 ? '+' : '';
          const color = c >= o ? '#f23645' : '#089981';
          return `
            <div style="font-family:monospace;font-size:11px;min-width:160px">
              <div style="margin-bottom:4px">${k.name}</div>
              <div>开: ${o.toFixed(2)} &nbsp; 收: <b style="color:${color}">${c.toFixed(2)}</b></div>
              <div>高: ${h.toFixed(2)} &nbsp; 低: ${l.toFixed(2)}</div>
              <div>涨幅: <b style="color:${color}">${sign}${pct.toFixed(2)}%</b></div>
              <div>成交量: ${(data[k.dataIndex]?.volume / 10000).toFixed(2)}万手</div>
            </div>
          `;
        },
      },
      legend: {
        data: showMA ? ['MA5', 'MA10', 'MA20'] : [],
        textStyle: { color: '#8b949e', fontSize: 10 },
        right: 0,
        top: 0,
      },
      grid: [
        { left: 65, right: 15, top: 30, bottom: 70 },
        { left: 65, right: 15, top: '78%', bottom: 20 },
      ],
      xAxis: [
        {
          type: 'category', data: dates, gridIndex: 0,
          axisLine: { lineStyle: { color: '#30363d' } },
          axisLabel: { color: '#8b949e', fontSize: 10 },
          splitLine: { show: false }, axisTick: { show: false },
        },
        {
          type: 'category', data: dates, gridIndex: 1,
          axisLabel: { show: false }, axisTick: { show: false },
          axisLine: { lineStyle: { color: '#30363d' } }, splitLine: { show: false },
        },
      ],
      yAxis: [
        {
          scale: true, gridIndex: 0,
          axisLine: { show: false }, axisTick: { show: false },
          splitLine: { lineStyle: { color: '#21262d', type: 'dashed' } },
          axisLabel: { color: '#8b949e', fontSize: 10, formatter: (v: number) => v.toFixed(2) },
        },
        {
          scale: false, gridIndex: 1,
          axisLine: { show: false }, axisTick: { show: false },
          splitLine: { lineStyle: { color: '#21262d', type: 'dashed' } },
          axisLabel: {
            color: '#8b949e', fontSize: 9,
            formatter: (v: number) => v >= 1e4 ? `${(v / 1e4).toFixed(0)}万` : String(v),
          },
        },
      ],
      dataZoom: [
        { type: 'inside', xAxisIndex: [0, 1], start: zoomStart, end: 100 },
        {
          show: true, xAxisIndex: [0, 1], type: 'slider',
          y: '94%', height: 16,
          backgroundColor: '#161b22', fillerColor: 'rgba(56,139,253,0.1)',
          borderColor: '#30363d',
          handleStyle: { color: '#388bfd' },
          textStyle: { color: '#8b949e', fontSize: 9 },
          start: zoomStart, end: 100,
        },
      ],
      series: [
        {
          name: 'K线',
          type: 'candlestick',
          data: ohlc,
          xAxisIndex: 0, yAxisIndex: 0,
          itemStyle: {
            color: '#f23645',           // 阳线 (bullish)
            color0: '#089981',          // 阴线 (bearish)
            borderColor: '#f23645',
            borderColor0: '#089981',
          },
        },
        ...(showMA ? [
          {
            name: 'MA5', type: 'line', data: ma5,
            xAxisIndex: 0, yAxisIndex: 0,
            smooth: false, symbol: 'none',
            lineStyle: { color: '#f0b90b', width: 1 },
          },
          {
            name: 'MA10', type: 'line', data: ma10,
            xAxisIndex: 0, yAxisIndex: 0,
            smooth: false, symbol: 'none',
            lineStyle: { color: '#388bfd', width: 1 },
          },
          {
            name: 'MA20', type: 'line', data: ma20,
            xAxisIndex: 0, yAxisIndex: 0,
            smooth: false, symbol: 'none',
            lineStyle: { color: '#bc8cff', width: 1 },
          },
        ] : []),
        {
          name: '成交量',
          type: 'bar',
          data: volumes.map((v, i) => ({
            value: v,
            itemStyle: {
              color: data[i]?.close >= data[i]?.open
                ? 'rgba(242,54,69,0.7)' : 'rgba(8,153,129,0.7)',
            },
          })),
          xAxisIndex: 1, yAxisIndex: 1,
        },
      ],
    };
  }, [data, showMA]);

  if (loading && !data.length) {
    return (
      <div className="h-[440px] rounded-lg border border-border/60 bg-dark-bg/30 animate-pulse" />
    );
  }

  if (errorMessage) {
    return (
      <div className="flex h-[440px] items-center justify-center rounded-lg border border-dashed border-rise/40 bg-rise/5 px-6 text-center">
        <div>
          <div className="mb-2 text-sm font-semibold text-rise">{periodLabel}加载失败</div>
          <div className="text-xs leading-5 text-text-secondary">{errorMessage}</div>
        </div>
      </div>
    );
  }

  if (!option) {
    return (
      <div className="flex h-[440px] items-center justify-center rounded-lg border border-dashed border-border text-center text-sm text-text-secondary">
        暂无{periodLabel}数据
      </div>
    );
  }

  return (
    <ReactECharts
      option={option}
      style={{ height: '440px', width: '100%' }}
      opts={{ renderer: 'canvas' }}
      notMerge={false}
    />
  );
}
