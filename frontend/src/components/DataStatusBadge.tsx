import type { DataStatus } from '@/types/api';
import { clsx } from 'clsx';

interface DataStatusBadgeProps {
  status: DataStatus | null | undefined;
  className?: string;
  showSource?: boolean;
}

export function DataStatusBadge({ status, className, showSource = false }: DataStatusBadgeProps) {
  if (!status) {
    return (
      <span className={clsx('text-xs text-flat', className)}>
        ⚪ 无数据
      </span>
    );
  }

  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1 text-xs font-mono',
        status.is_live ? 'text-fall' : 'text-yellow-400',
        className
      )}
      title={showSource ? `来源: ${status.source}` : undefined}
    >
      {status.label}
      <span className="text-text-secondary opacity-60">
        {status.timestamp}
      </span>
      {showSource && (
        <span className="text-text-secondary opacity-50 text-[10px]">
          [{status.source}]
        </span>
      )}
    </span>
  );
}
