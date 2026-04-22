import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Play, Pause, Trash2, Plus, Clock, History, List, Edit2, Save, X, FileText } from 'lucide-react';
import { api } from '../lib/api';
import { useAuth } from '../lib/auth';
import { cn } from '../lib/utils';

interface ScheduleJob {
  id: string;
  name: string;
  description: string | null;
  mode: string;
  cron: string;
  max_pages: number;
  days: number | null;
  next_run: string | null;
  enabled: boolean;
  created_at: string;
  updated_at: string;
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

interface EditHistoryRecord {
  id: string;
  schedule_id: string;
  editor: string;
  action: string;
  old_values: string | null;
  new_values: string | null;
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
  const [description, setDescription] = useState('');

  const [editingJob, setEditingJob] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<Partial<ScheduleJob>>({});

  const [viewingHistory, setViewingHistory] = useState<string | null>(null);

  const { data: jobs } = useQuery({
    queryKey: ['schedules'],
    queryFn: () => api.get<ScheduleJob[]>('/schedules'),
  });

  const { data: history } = useQuery({
    queryKey: ['schedule-history'],
    queryFn: () => api.get<ScheduleHistoryRecord[]>('/schedules/history?limit=50'),
    refetchInterval: tab === 'history' ? 5000 : false,
  });

  const { data: editHistory } = useQuery({
    queryKey: ['schedule-edit-history', viewingHistory],
    queryFn: () => api.get<EditHistoryRecord[]>(`/schedules/${viewingHistory}/edit-history`),
    enabled: !!viewingHistory,
  });

  const handleCreate = async () => {
    try {
      await api.post('/schedules', {
        mode,
        cron,
        max_pages: maxPages,
        days: mode === 'by_date' ? days : undefined,
        description: description || undefined,
      });
      queryClient.invalidateQueries({ queryKey: ['schedules'] });
      setShowForm(false);
      setDescription('');
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

  const startEdit = (job: ScheduleJob) => {
    setEditingJob(job.id);
    setEditForm({
      name: job.name,
      cron: job.cron,
      max_pages: job.max_pages,
      days: job.days,
      enabled: job.enabled,
      description: job.description,
    });
  };

  const cancelEdit = () => {
    setEditingJob(null);
    setEditForm({});
  };

  const handleUpdate = async (jobId: string) => {
    try {
      const payload: Record<string, any> = {};
      if (editForm.name !== undefined) payload.name = editForm.name;
      if (editForm.cron !== undefined) payload.cron = editForm.cron;
      if (editForm.max_pages !== undefined) payload.max_pages = editForm.max_pages;
      if (editForm.days !== undefined) payload.days = editForm.days;
      if (editForm.enabled !== undefined) payload.enabled = editForm.enabled;
      if (editForm.description !== undefined) payload.description = editForm.description;

      await api.put(`/schedules/${jobId}`, payload);
      queryClient.invalidateQueries({ queryKey: ['schedules'] });
      setEditingJob(null);
      setEditForm({});
    } catch (e: any) {
      alert(e.message);
    }
  };

  const modeLabel = (m: string) =>
    ({ incremental: '增量', full: '全量', by_date: '按时间', detail_only: '仅详情' }[m] || m);

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
              <div className="mb-4">
                <label className="text-xs block mb-1.5 font-medium" style={{ color: 'var(--text-sec)' }}>任务描述</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={2}
                  className="w-full px-3 py-2 rounded-lg border text-sm outline-none focus:ring-2 focus:ring-blue-400 resize-none"
                  style={{ backgroundColor: 'var(--bg)', borderColor: 'var(--border)', color: 'var(--text)' }}
                  placeholder="可选：输入任务描述..."
                />
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
                  <th className="text-left px-4 py-3 font-medium" style={{ color: 'var(--text-sec)' }}>模式</th>
                  <th className="text-left px-4 py-3 font-medium" style={{ color: 'var(--text-sec)' }}>Cron</th>
                  <th className="text-left px-4 py-3 font-medium" style={{ color: 'var(--text-sec)' }}>下次执行</th>
                  <th className="text-left px-4 py-3 font-medium" style={{ color: 'var(--text-sec)' }}>状态</th>
                  {isAdmin && <th className="text-right px-4 py-3 font-medium" style={{ color: 'var(--text-sec)' }}>操作</th>}
                </tr>
              </thead>
              <tbody>
                {(!jobs || jobs.length === 0) ? (
                  <tr>
                    <td colSpan={6} className="text-center py-8" style={{ color: 'var(--text-sec)' }}>
                      暂无定时任务，{isAdmin && '点击"新建任务"添加'}
                    </td>
                  </tr>
                ) : (
                  jobs.map((job) => (
                    <tr key={job.id} className="border-b last:border-0" style={{ borderColor: 'var(--border)' }}>
                      <td className="px-4 py-3">
                        {editingJob === job.id ? (
                          <div className="space-y-2">
                            <input
                              value={editForm.name || ''}
                              onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                              className="w-full px-2 py-1 rounded border text-sm font-mono"
                              style={{ backgroundColor: 'var(--bg)', borderColor: 'var(--border)', color: 'var(--text)' }}
                            />
                            <textarea
                              value={editForm.description || ''}
                              onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                              rows={2}
                              className="w-full px-2 py-1 rounded border text-xs resize-none"
                              style={{ backgroundColor: 'var(--bg)', borderColor: 'var(--border)', color: 'var(--text)' }}
                              placeholder="任务描述"
                            />
                          </div>
                        ) : (
                          <div>
                            <div style={{ color: 'var(--text)' }}>{job.name}</div>
                            {job.description && (
                              <div className="text-xs mt-0.5 flex items-center gap-1" style={{ color: 'var(--text-sec)' }}>
                                <FileText className="w-3 h-3" /> {job.description}
                              </div>
                            )}
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-3" style={{ color: 'var(--text-sec)' }}>
                        {modeLabel(job.mode)}
                      </td>
                      <td className="px-4 py-3 font-mono text-xs" style={{ color: 'var(--text-sec)' }}>
                        {editingJob === job.id ? (
                          <div className="space-y-2">
                            <input
                              value={editForm.cron || ''}
                              onChange={(e) => setEditForm({ ...editForm, cron: e.target.value })}
                              className="w-full px-2 py-1 rounded border text-sm font-mono"
                              style={{ backgroundColor: 'var(--bg)', borderColor: 'var(--border)', color: 'var(--text)' }}
                            />
                            <div className="flex flex-wrap gap-1">
                              {CRON_PRESETS.map((preset) => (
                                <button
                                  key={preset.value}
                                  onClick={() => setEditForm({ ...editForm, cron: preset.value })}
                                  className={cn(
                                    'px-2 py-0.5 rounded text-[10px] border transition-colors',
                                    editForm.cron === preset.value
                                      ? 'bg-blue-600 text-white border-blue-600'
                                      : 'border-gray-200 dark:border-gray-700 hover:border-blue-400'
                                  )}
                                >
                                  {preset.label}
                                </button>
                              ))}
                            </div>
                          </div>
                        ) : (
                          job.cron
                        )}
                      </td>
                      <td className="px-4 py-3" style={{ color: 'var(--text-sec)' }}>{job.next_run || '-'}</td>
                      <td className="px-4 py-3">
                        {editingJob === job.id ? (
                          <select
                            value={editForm.enabled ? 'true' : 'false'}
                            onChange={(e) => setEditForm({ ...editForm, enabled: e.target.value === 'true' })}
                            className="px-2 py-1 rounded border text-sm"
                            style={{ backgroundColor: 'var(--bg)', borderColor: 'var(--border)', color: 'var(--text)' }}
                          >
                            <option value="true">启用</option>
                            <option value="false">暂停</option>
                          </select>
                        ) : (
                          <span className={cn(
                            'inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium',
                            job.enabled ? 'bg-green-50 text-green-700 dark:bg-green-900/30 dark:text-green-400' : 'bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400'
                          )}>
                            <span className={cn('w-1.5 h-1.5 rounded-full', job.enabled ? 'bg-green-500' : 'bg-gray-400')} />
                            {job.enabled ? '启用' : '暂停'}
                          </span>
                        )}
                      </td>
                      {isAdmin && (
                        <td className="px-4 py-3 text-right">
                          {editingJob === job.id ? (
                            <div className="flex items-center justify-end gap-1">
                              <button onClick={() => handleUpdate(job.id)} className="p-1.5 rounded hover:bg-green-50 dark:hover:bg-green-900/30">
                                <Save className="w-4 h-4 text-green-500" />
                              </button>
                              <button onClick={cancelEdit} className="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-800">
                                <X className="w-4 h-4 text-gray-400" />
                              </button>
                            </div>
                          ) : (
                            <div className="flex items-center justify-end gap-1">
                              <button onClick={() => startEdit(job)} className="p-1.5 rounded hover:bg-blue-50 dark:hover:bg-blue-900/30">
                                <Edit2 className="w-4 h-4 text-blue-400" />
                              </button>
                              {job.enabled ? (
                                <button onClick={() => handleAction('pause', job.id)} className="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-800">
                                  <Pause className="w-4 h-4" style={{ color: 'var(--text-sec)' }} />
                                </button>
                              ) : (
                                <button onClick={() => handleAction('resume', job.id)} className="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-800">
                                  <Play className="w-4 h-4" style={{ color: 'var(--text-sec)' }} />
                                </button>
                              )}
                              <button onClick={() => setViewingHistory(job.id)} className="p-1.5 rounded hover:bg-purple-50 dark:hover:bg-purple-900/30">
                                <History className="w-4 h-4 text-purple-400" />
                              </button>
                              <button onClick={() => handleDelete(job.id)} className="p-1.5 rounded hover:bg-red-50 dark:hover:bg-red-900/30">
                                <Trash2 className="w-4 h-4 text-red-400" />
                              </button>
                            </div>
                          )}
                        </td>
                      )}
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {viewingHistory && (
            <div className="rounded-lg p-5 shadow-sm border mt-4" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)' }}>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-medium flex items-center gap-2" style={{ color: 'var(--text)' }}>
                  <History className="w-4 h-4" /> 修改历史
                </h3>
                <button onClick={() => setViewingHistory(null)} className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-800">
                  <X className="w-4 h-4 text-gray-400" />
                </button>
              </div>
              {(!editHistory || editHistory.length === 0) ? (
                <div className="text-center py-4 text-sm" style={{ color: 'var(--text-sec)' }}>暂无修改记录</div>
              ) : (
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {editHistory.map((record) => (
                    <div key={record.id} className="rounded p-3 text-xs border" style={{ backgroundColor: 'var(--bg)', borderColor: 'var(--border)' }}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-medium" style={{ color: 'var(--text)' }}>
                          {record.action === 'delete' ? '删除任务' :
                           record.action === 'pause' ? '暂停任务' :
                           record.action === 'resume' ? '恢复任务' :
                           record.action.startsWith('update:') ? `更新字段 (${record.action.replace('update:', '')})` : record.action}
                        </span>
                        <span style={{ color: 'var(--text-sec)' }}>{record.editor} · {record.created_at?.slice(0, 19).replace('T', ' ')}</span>
                      </div>
                      {record.old_values && (
                        <div className="mt-1 font-mono" style={{ color: 'var(--text-sec)' }}>
                          <span className="text-red-400">- {record.old_values}</span>
                        </div>
                      )}
                      {record.new_values && (
                        <div className="mt-0.5 font-mono" style={{ color: 'var(--text-sec)' }}>
                          <span className="text-green-400">+ {record.new_values}</span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
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
