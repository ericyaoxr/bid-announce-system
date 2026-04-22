import { useQuery } from '@tanstack/react-query';
import { Database, Activity, AlertCircle, FileText, TrendingUp, DollarSign, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { api, type DashboardStats } from '../lib/api';
import { formatNumber, formatAmount, cn } from '../lib/utils';

function StatCard({ icon: Icon, label, value, sub, color }: { icon: typeof Database; label: string; value: string; sub?: string; color: string }) {
  return (
    <div className="rounded-lg p-5 shadow-sm border" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)' }}>
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs" style={{ color: 'var(--text-sec)' }}>{label}</div>
          <div className="text-2xl font-bold mt-1" style={{ color: 'var(--text)' }}>{value}</div>
          {sub && <div className="text-xs mt-1" style={{ color: 'var(--text-sec)' }}>{sub}</div>}
        </div>
        <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ backgroundColor: `${color}15` }}>
          <Icon className="w-5 h-5" style={{ color }} />
        </div>
      </div>
    </div>
  );
}

const MODE_LABELS: Record<string, string> = {
  incremental: '增量',
  full: '全量',
  by_date: '按时间',
  detail_only: '仅详情',
};

export function Dashboard() {
  const { data } = useQuery({
    queryKey: ['dashboard'],
    queryFn: () => api.get<DashboardStats>('/dashboard'),
  });

  if (!data) return <div className="text-center py-20" style={{ color: 'var(--text-sec)' }}>加载中...</div>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold" style={{ color: 'var(--text)' }}>仪表盘</h1>
        <p className="text-sm mt-1" style={{ color: 'var(--text-sec)' }}>数据采集系统实时概览</p>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <StatCard
          icon={Database}
          label="数据源总数"
          value={String(data.crawl_stats.data_source_count)}
          sub={`${data.crawl_stats.data_source_count} 个已启用`}
          color="#1677ff"
        />
        <StatCard
          icon={Activity}
          label="运行中任务"
          value={String(data.crawl_stats.running_tasks)}
          sub={`共 ${data.total} 个`}
          color="#52c41a"
        />
        <StatCard
          icon={AlertCircle}
          label="失败任务"
          value={String(data.crawl_stats.failed_tasks)}
          sub="需要关注"
          color="#ff4d4f"
        />
        <StatCard
          icon={FileText}
          label="已采集记录"
          value={formatNumber(data.crawl_stats.total_records)}
          sub="0 条 AI 处理"
          color="#722ed1"
        />
      </div>

      <div className="rounded-lg shadow-sm border" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)' }}>
        <div className="px-5 py-3 border-b flex items-center justify-between" style={{ borderColor: 'var(--border)' }}>
          <h3 className="text-sm font-medium" style={{ color: 'var(--text)' }}>最近任务运行</h3>
          <span className="text-xs" style={{ color: 'var(--text-sec)' }}>共 {data.recent_crawl_tasks.length} 条</span>
        </div>
        {data.recent_crawl_tasks.length === 0 ? (
          <div className="py-12 text-center" style={{ color: 'var(--text-sec)' }}>暂无任务记录</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b" style={{ borderColor: 'var(--border)' }}>
                  <th className="text-left px-5 py-2.5 font-medium" style={{ color: 'var(--text-sec)' }}>状态</th>
                  <th className="text-left px-5 py-2.5 font-medium" style={{ color: 'var(--text-sec)' }}>类型</th>
                  <th className="text-left px-5 py-2.5 font-medium" style={{ color: 'var(--text-sec)' }}>模式</th>
                  <th className="text-left px-5 py-2.5 font-medium" style={{ color: 'var(--text-sec)' }}>记录数</th>
                  <th className="text-left px-5 py-2.5 font-medium" style={{ color: 'var(--text-sec)' }}>耗时</th>
                  <th className="text-left px-5 py-2.5 font-medium" style={{ color: 'var(--text-sec)' }}>开始时间</th>
                  <th className="text-left px-5 py-2.5 font-medium" style={{ color: 'var(--text-sec)' }}>完成时间</th>
                </tr>
              </thead>
              <tbody>
                {data.recent_crawl_tasks.map((r) => (
                  <tr key={r.id} className="border-b last:border-0" style={{ borderColor: 'var(--border)' }}>
                    <td className="px-5 py-3">
                      <span className={cn(
                        'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium',
                        r.status === 'completed' ? 'bg-green-50 text-green-600 dark:bg-green-900/30 dark:text-green-400' :
                        r.status === 'error' ? 'bg-red-50 text-red-600 dark:bg-red-900/30 dark:text-red-400' :
                        'bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400'
                      )}>
                        {r.status === 'completed' ? <><CheckCircle className="w-3 h-3" /> 完成</> :
                         r.status === 'error' ? <><XCircle className="w-3 h-3" /> 失败</> :
                         <><Loader2 className="w-3 h-3 animate-spin" /> 运行中</>}
                      </span>
                    </td>
                    <td className="px-5 py-3">
                      <span className={cn(
                        'inline-flex items-center px-2 py-0.5 rounded-full text-xs',
                        r.task_type === 'scheduled' ? 'bg-purple-50 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400' :
                        'bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400'
                      )}>
                        {r.task_type === 'scheduled' ? '定时' : '手动'}
                      </span>
                    </td>
                    <td className="px-5 py-3" style={{ color: 'var(--text)' }}>{MODE_LABELS[r.mode] || r.mode}</td>
                    <td className="px-5 py-3" style={{ color: 'var(--text)' }}>{r.record_count ?? 0}</td>
                    <td className="px-5 py-3" style={{ color: 'var(--text-sec)' }}>{r.elapsed_seconds ? `${r.elapsed_seconds.toFixed(1)}s` : '-'}</td>
                    <td className="px-5 py-3 text-xs" style={{ color: 'var(--text-sec)' }}>{r.started_at ? r.started_at.slice(0, 19).replace('T', ' ') : '-'}</td>
                    <td className="px-5 py-3 text-xs" style={{ color: 'var(--text-sec)' }}>{r.finished_at ? r.finished_at.slice(0, 19).replace('T', ' ') : '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="rounded-lg p-5 shadow-sm border" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)' }}>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ backgroundColor: '#1677ff15' }}>
              <FileText className="w-5 h-5" style={{ color: '#1677ff' }} />
            </div>
            <div>
              <div className="text-xs" style={{ color: 'var(--text-sec)' }}>总公告数</div>
              <div className="text-xl font-bold" style={{ color: 'var(--text)' }}>{formatNumber(data.total)}</div>
            </div>
          </div>
        </div>
        <div className="rounded-lg p-5 shadow-sm border" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)' }}>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ backgroundColor: '#52c41a15' }}>
              <TrendingUp className="w-5 h-5" style={{ color: '#52c41a' }} />
            </div>
            <div>
              <div className="text-xs" style={{ color: 'var(--text-sec)' }}>今日新增</div>
              <div className="text-xl font-bold" style={{ color: 'var(--text)' }}>{formatNumber(data.today)}</div>
            </div>
          </div>
        </div>
        <div className="rounded-lg p-5 shadow-sm border" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)' }}>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ backgroundColor: '#faad1415' }}>
              <DollarSign className="w-5 h-5" style={{ color: '#faad14' }} />
            </div>
            <div>
              <div className="text-xs" style={{ color: 'var(--text-sec)' }}>中标总金额</div>
              <div className="text-xl font-bold" style={{ color: 'var(--text)' }}>{formatAmount(data.total_bid_amount)}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
