import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Play, Pause, Trash2, Plus, Clock, History, List } from 'lucide-react';
import { api } from '../lib/api';
import { useAuth } from '../lib/auth';
import { cn } from '../lib/utils';

interface ScheduleJob {
  id: string;
  name: string;
  cron: string;
  next_run: string | null;
  enabled: boolean;
}

interface ScheduleHistoryRecord {
  id: string;
  schedule_id: string;
  schedule_name: string;
  mode: string;
  status: string;
  list_count: number;
  detail_count: number;
  total_records: number;
  with_winner: number;
  elapsed_seconds: number;
  started_at: string | null;
  finished_at: string | null;
  error_message: string | null;
  created_at: string;
}

type Tab = 'jobs' | 'history';

const MODE_OPTIONS = [
  { value: 'incremental', label: '增量采集' },
  { value: 'full', label: '全量采集' },
  { value: 'by_date', label: '按时间采集' },
  { value: 'detail_only', label: '仅抓详情' },
];

const CRON_PRESETS = [
  { label: '每小时', value: '0 * * * *' },
  { label: '每6小时', value: '0 */6 * * *' },
  { label: '每天 0:00', value: '0 0 * * *' },
  { label: '每天 8:00', value: '0 8 * * *' },
  { label: '每周一 8:00', value: '0 8 * * 1' },
  { label: '工作日 8:00', value: '0 8 * * 1-5' },
];

export function Schedules() {
  const { isAdmin } = useAuth();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<Tab>('jobs');
  const [showForm, setShowForm] = useState(false);
  const [mode, setMode] = useState('incremental');
  const [cron, setCron] = useState('0 8 * * *');
  const [maxPages, setMaxPages] = useState(10);
  const [days, setDays] = useState(30);

  const { data: jobs } = useQuery({
    queryKey: ['schedules'],
    queryFn: () => api.get<ScheduleJob[]>('/schedules'),
  });

  const { data: history } = useQuery({
    queryKey: ['schedule-history'],
    queryFn: () => api.get<ScheduleHistoryRecord[]>('/schedules/history?limit=50'),
    refetchInterval: tab === 'history' ? 5000 : false,
  });

  const handleCreate = async () => {
    try {
      await api.post('/schedules', { mode, cron, max_pages: maxPages, days: mode === 'by_date' ? days : undefined });
      queryClient.invalidateQueries({ queryKey: ['schedules'] });
      setShowForm(false);
    } catch (e: any) {
      alert(e.message);
    }
  };

  const handleAction = async (action: string, jobId: string) => {
    try {
      await api.post(`/schedules/${jobId}/${action}`);
      queryClient.invalidateQueries({ queryKey: ['schedules'] });
    } catch (e: any) {
      alert(e.message);
    }
  };

  const handleDelete = async (jobId: string) => {
    if (!confirm('确定删除此定时任务？')) return;
    try {
      await api.delete(`/schedules/${jobId}`);
      queryClient.invalidateQueries({ queryKey: ['schedules'] });
    } catch (e: any) {
      alert(e.message);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold" style={{ color: 'var(--text)' }}>定时调度</h1>
        <div className="flex items-center gap-3">
          <div className="flex gap-1 rounded-lg p-1" style={{ backgroundColor: 'var(--bg)' }}>
            <button onClick={() => setTab('jobs')}
              className={cn('flex items-center gap-1.5 px-3 py-1.5 rounded text-sm transition-colors', tab === 'jobs' ? 'text-white bg-blue-600' : 'text-gray-400 hover:text-white')}>
              <List className="w-3.5 h-3.5" /> 任务列表
            </button>
            <button onClick={() => setTab('history')}
              className={cn('flex items-center gap-1.5 px-3 py-1.5 rounded text-sm transition-colors', tab === 'history' ? 'text-white bg-blue-600' : 'text-gray-400 hover:text-white')}>
              <History className="w-3.5 h-3.5" /> 执行历史
            </button>
          </div>
          {isAdmin && (
            <button onClick={() => setShowForm(!showForm)}
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm text-white bg-blue-600 hover:bg-blue-700 transition-colors">
              <Plus className="w-4 h-4" /> 新建任务
            </button>
          )}
        </div>
      </div>

      {tab === 'jobs' && (
        <>
          {isAdmin && showForm && (
            <div className="rounded-lg p-5 shadow-sm border" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)' }}>
              <h3 className="text-sm font-medium mb-4 flex items-center gap-2" style={{ color: 'var(--text)' }}>
                <Clock className="w-4 h-4" /> 新建定时采集任务
              </h3>
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="text-xs block mb-1.5 font-medium" style={{ color: 'var(--text-sec)' }}>采集模式</label>
                  <select value={mode} onChange={(e) => setMode(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border text-sm outline-none focus:ring-2 focus:ring-blue-400"
                    style={{ backgroundColor: 'var(--bg)', borderColor: 'var(--border)', color: 'var(--text)' }}>
                    {MODE_OPTIONS.map((opt) => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-xs block mb-1.5 font-medium" style={{ color: 'var(--text-sec)' }}>Cron 表达式</label>
                  <input value={cron} onChange={(e) => setCron(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border text-sm outline-none focus:ring-2 focus:ring-blue-400 font-mono"
                    style={{ backgroundColor: 'var(--bg)', borderColor: 'var(--border)', color: 'var(--text)' }}
                    placeholder="0 8 * * *" />
                </div>
              </div>
              <div className="mb-4">
                <label className="text-xs block mb-1.5 font-medium" style={{ color: 'var(--text-sec)' }}>快速预设</label>
                <div className="flex flex-wrap gap-2">
                  {CRON_PRESETS.map((preset) => (
                    <button key={preset.value} onClick={() => setCron(preset.value)}
                      className={cn(
                        'px-3 py-1.5 rounded text-xs border transition-colors',
                        cron === preset.value
                          ? 'bg-blue-600 text-white border-blue-600'
                          : 'text-gray-600 dark:text-gray-400 border-gray-200 dark:border-gray-700 hover:border-blue-400'
                      )}>
                      {preset.label}
                    </button>
                  ))}
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="text-xs block mb-1.5 font-medium" style={{ color: 'var(--text-sec)' }}>最大页数</label>
                  <input type="number" value={maxPages} onChange={(e) => setMaxPages(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded-lg border text-sm outline-none focus:ring-2 focus:ring-blue-400"
                    style={{ backgroundColor: 'var(--bg)', borderColor: 'var(--border)', color: 'var(--text)' }} />
                </div>
                {mode === 'by_date' && (
                  <div>
                    <label className="text-xs block mb-1.5 font-medium" style={{ color: 'var(--text-sec)' }}>天数</label>
                    <input type="number" value={days} onChange={(e) => setDays(Number(e.target.value))}
                      className="w-full px-3 py-2 rounded-lg border text-sm outline-none focus:ring-2 focus:ring-blue-400"
                      style={{ backgroundColor: 'var(--bg)', borderColor: 'var(--border)', color: 'var(--text)' }} />
                  </div>
                )}
              </div>
              <div className="flex gap-2 justify-end">
                <button onClick={() => setShowForm(false)}
                  className="px-4 py-2 rounded text-sm border transition-colors"
                  style={{ color: 'var(--text)', borderColor: 'var(--border)' }}>
                  取消
                </button>
                <button onClick={handleCreate}
                  className="px-4 py-2 rounded text-sm text-white bg-blue-600 hover:bg-blue-700 transition-colors">
                  创建任务
                </button>
              </div>
            </div>
          )}

          <div className="rounded-lg shadow-sm border overflow-hidden" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)' }}>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b" style={{ borderColor: 'var(--border)' }}>
                  <th className="text-left px-4 py-3 font-medium" style={{ color: 'var(--text-sec)' }}>任务名称</th>
                  <th className="text-left px-4 py-3 font-medium" style={{ color: 'var(--text-sec)' }}>Cron</th>
                  <th className="text-left px-4 py-3 font-medium" style={{ color: 'var(--text-sec)' }}>下次执行</th>
                  <th className="text-left px-4 py-3 font-medium" style={{ color: 'var(--text-sec)' }}>状态</th>
                  {isAdmin && <th className="text-right px-4 py-3 font-medium" style={{ color: 'var(--text-sec)' }}>操作</th>}
                </tr>
              </thead>
              <tbody>
                {(!jobs || jobs.length === 0) ? (
                  <tr>
                    <td colSpan={5} className="text-center py-8" style={{ color: 'var(--text-sec)' }}>
                      暂无定时任务，{isAdmin && '点击"新建任务"添加'}
                    </td>
                  </tr>
                ) : (
                  jobs.map((job) => (
                    <tr key={job.id} className="border-b last:border-0" style={{ borderColor: 'var(--border)' }}>
                      <td className="px-4 py-3" style={{ color: 'var(--text)' }}>{job.name}</td>
                      <td className="px-4 py-3 font-mono text-xs" style={{ color: 'var(--text-sec)' }}>{job.cron}</td>
                      <td className="px-4 py-3" style={{ color: 'var(--text-sec)' }}>{job.next_run || '-'}</td>
                      <td className="px-4 py-3">
                        <span className={cn(
                          'inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium',
                          job.enabled ? 'bg-green-50 text-green-700 dark:bg-green-900/30 dark:text-green-400' : 'bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400'
                        )}>
                          <span className={cn('w-1.5 h-1.5 rounded-full', job.enabled ? 'bg-green-500' : 'bg-gray-400')} />
                          {job.enabled ? '启用' : '暂停'}
                        </span>
                      </td>
                      {isAdmin && (
                        <td className="px-4 py-3 text-right">
                          <div className="flex items-center justify-end gap-1">
                            {job.enabled ? (
                              <button onClick={() => handleAction('pause', job.id)} className="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-800">
                                <Pause className="w-4 h-4" style={{ color: 'var(--text-sec)' }} />
                              </button>
                            ) : (
                              <button onClick={() => handleAction('resume', job.id)} className="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-800">
                                <Play className="w-4 h-4" style={{ color: 'var(--text-sec)' }} />
                              </button>
                            )}
                            <button onClick={() => handleDelete(job.id)} className="p-1.5 rounded hover:bg-red-50 dark:hover:bg-red-900/30">
                              <Trash2 className="w-4 h-4 text-red-400" />
                            </button>
                          </div>
                        </td>
                      )}
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </>
      )}

      {tab === 'history' && (
        <div className="space-y-4">
          <h3 className="text-sm font-medium" style={{ color: 'var(--text)' }}>执行历史</h3>
          <div className="rounded-lg shadow-sm border overflow-hidden" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)' }}>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b" style={{ borderColor: 'var(--border)' }}>
                  <th className="text-left px-4 py-2.5 font-medium" style={{ color: 'var(--text-sec)' }}>任务名称</th>
                  <th className="text-left px-4 py-2.5 font-medium" style={{ color: 'var(--text-sec)' }}>模式</th>
                  <th className="text-left px-4 py-2.5 font-medium" style={{ color: 'var(--text-sec)' }}>状态</th>
                  <th className="text-left px-4 py-2.5 font-medium" style={{ color: 'var(--text-sec)' }}>列表</th>
                  <th className="text-left px-4 py-2.5 font-medium" style={{ color: 'var(--text-sec)' }}>详情</th>
                  <th className="text-left px-4 py-2.5 font-medium" style={{ color: 'var(--text-sec)' }}>总记录</th>
                  <th className="text-left px-4 py-2.5 font-medium" style={{ color: 'var(--text-sec)' }}>耗时</th>
                  <th className="text-left px-4 py-2.5 font-medium" style={{ color: 'var(--text-sec)' }}>开始时间</th>
                </tr>
              </thead>
              <tbody>
                {(!history || history.length === 0) ? (
                  <tr>
                    <td colSpan={8} className="text-center py-8" style={{ color: 'var(--text-sec)' }}>
                      暂无执行记录
                    </td>
                  </tr>
                ) : (
                  history.map((r) => (
                    <tr key={r.id} className="border-b last:border-0" style={{ borderColor: 'var(--border)' }}>
                      <td className="px-4 py-3" style={{ color: 'var(--text)' }}>{r.schedule_name}</td>
                      <td className="px-4 py-3" style={{ color: 'var(--text-sec)' }}>
                        {{ incremental: '增量', full: '全量', by_date: '按时间', detail_only: '仅详情' }[r.mode] || r.mode}
                      </td>
                      <td className="px-4 py-3">
                        <span className={cn(
                          'inline-flex items-center px-2 py-0.5 rounded-full text-xs',
                          r.status === 'completed' ? 'bg-green-50 text-green-600 dark:bg-green-900/30 dark:text-green-400' :
                          r.status === 'error' ? 'bg-red-50 text-red-600 dark:bg-red-900/30 dark:text-red-400' :
                          'bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400'
                        )}>
                          {r.status === 'completed' ? '完成' : r.status === 'error' ? '失败' : '运行中'}
                        </span>
                      </td>
                      <td className="px-4 py-3" style={{ color: 'var(--text)' }}>{r.list_count}</td>
                      <td className="px-4 py-3" style={{ color: 'var(--text)' }}>{r.detail_count}</td>
                      <td className="px-4 py-3" style={{ color: 'var(--text)' }}>{r.total_records}</td>
                      <td className="px-4 py-3" style={{ color: 'var(--text-sec)' }}>{r.elapsed_seconds ? `${r.elapsed_seconds.toFixed(1)}s` : '-'}</td>
                      <td className="px-4 py-3 text-xs" style={{ color: 'var(--text-sec)' }}>{r.started_at ? r.started_at.slice(0, 19).replace('T', ' ') : '-'}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
