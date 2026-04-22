import { useState, useEffect, useRef } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Play, Square, Terminal, Plus, Edit2, Trash2, Power, Globe, Clock, List, X, Check } from 'lucide-react';
import { api, type CrawlerStatus } from '../lib/api';
import { useAuth } from '../lib/auth';
import { cn } from '../lib/utils';

interface Site {
  id: string;
  name: string;
  base_url: string;
  description: string;
  enabled: boolean;
  crawler_type: string;
  created_at: string;
}

interface CrawlTask {
  id: string;
  mode: string;
  status: string;
  max_pages: number;
  days: number | null;
  list_count: number;
  detail_count: number;
  total_records: number;
  with_winner: number;
  elapsed_seconds: number;
  started_at: string | null;
  finished_at: string | null;
  error_message: string | null;
}

type Tab = 'control' | 'sites' | 'history';

function SiteModal({ open, editing, form, onChange, onSave, onClose }: {
  open: boolean;
  editing: Site | null;
  form: { id: string; name: string; base_url: string; description: string; crawler_type: string; enabled: boolean };
  onChange: (f: typeof form) => void;
  onSave: () => void;
  onClose: () => void;
}) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
      <div className="rounded-xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden" style={{ backgroundColor: 'var(--card)' }}>
        <div className="flex items-center justify-between px-5 py-3 border-b" style={{ borderColor: 'var(--border)' }}>
          <h3 className="text-base font-semibold" style={{ color: 'var(--text)' }}>{editing ? '编辑站点' : '添加站点'}</h3>
          <button onClick={onClose} className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
            <X className="w-4 h-4" style={{ color: 'var(--text-sec)' }} />
          </button>
        </div>
        <div className="p-5 space-y-4">
          <div>
            <label className="text-xs block mb-1 font-medium" style={{ color: 'var(--text)' }}>站点ID *</label>
            <input value={form.id} onChange={(e) => onChange({ ...form, id: e.target.value })} disabled={!!editing}
              placeholder="例如: tequ-jg-001"
              className="w-full px-3 py-2 rounded-lg border text-sm outline-none focus:ring-2 focus:ring-blue-500/30"
              style={{ backgroundColor: 'var(--bg)', borderColor: 'var(--border)', color: 'var(--text)' }} />
          </div>
          <div>
            <label className="text-xs block mb-1 font-medium" style={{ color: 'var(--text)' }}>站点名称 *</label>
            <input value={form.name} onChange={(e) => onChange({ ...form, name: e.target.value })}
              placeholder="例如: 特区建工集团采购平台"
              className="w-full px-3 py-2 rounded-lg border text-sm outline-none focus:ring-2 focus:ring-blue-500/30"
              style={{ backgroundColor: 'var(--bg)', borderColor: 'var(--border)', color: 'var(--text)' }} />
          </div>
          <div>
            <label className="text-xs block mb-1 font-medium" style={{ color: 'var(--text)' }}>基础URL *</label>
            <input value={form.base_url} onChange={(e) => onChange({ ...form, base_url: e.target.value })}
              placeholder="https://example.com"
              className="w-full px-3 py-2 rounded-lg border text-sm outline-none focus:ring-2 focus:ring-blue-500/30"
              style={{ backgroundColor: 'var(--bg)', borderColor: 'var(--border)', color: 'var(--text)' }} />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs block mb-1 font-medium" style={{ color: 'var(--text)' }}>爬虫类型</label>
              <select value={form.crawler_type} onChange={(e) => onChange({ ...form, crawler_type: e.target.value })}
                className="w-full px-3 py-2 rounded-lg border text-sm outline-none focus:ring-2 focus:ring-blue-500/30"
                style={{ backgroundColor: 'var(--bg)', borderColor: 'var(--border)', color: 'var(--text)' }}>
                <option value="deep">DeepCrawler</option>
                <option value="simple">SimpleCrawler</option>
              </select>
            </div>
            <div className="flex items-end pb-2">
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" checked={form.enabled} onChange={(e) => onChange({ ...form, enabled: e.target.checked })}
                  className="w-4 h-4 rounded" />
                <span className="text-sm" style={{ color: 'var(--text)' }}>启用</span>
              </label>
            </div>
          </div>
          <div>
            <label className="text-xs block mb-1 font-medium" style={{ color: 'var(--text)' }}>描述</label>
            <textarea value={form.description} onChange={(e) => onChange({ ...form, description: e.target.value })} rows={2}
              placeholder="站点描述信息..."
              className="w-full px-3 py-2 rounded-lg border text-sm outline-none focus:ring-2 focus:ring-blue-500/30 resize-none"
              style={{ backgroundColor: 'var(--bg)', borderColor: 'var(--border)', color: 'var(--text)' }} />
          </div>
        </div>
        <div className="flex justify-end gap-2 px-5 py-3 border-t" style={{ borderColor: 'var(--border)' }}>
          <button onClick={onClose}
            className="px-4 py-2 rounded-lg text-sm border transition-colors"
            style={{ borderColor: 'var(--border)', color: 'var(--text-sec)' }}>
            取消
          </button>
          <button onClick={onSave}
            className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm text-white bg-blue-600 hover:bg-blue-700 transition-colors">
            <Check className="w-3.5 h-3.5" /> 保存
          </button>
        </div>
      </div>
    </div>
  );
}

export function Crawler() {
  const { isAdmin } = useAuth();
  const [tab, setTab] = useState<Tab>('control');
  const [mode, setMode] = useState('incremental');
  const [maxPages, setMaxPages] = useState(100);
  const [days, setDays] = useState(30);
  const [starting, setStarting] = useState(false);
  const [stopping, setStopping] = useState(false);
  const [showSiteForm, setShowSiteForm] = useState(false);
  const [editingSite, setEditingSite] = useState<Site | null>(null);
  const [siteForm, setSiteForm] = useState({ id: '', name: '', base_url: '', description: '', crawler_type: 'deep', enabled: true });
  const queryClient = useQueryClient();
  const logRef = useRef<HTMLDivElement>(null);

  const { data: status } = useQuery({
    queryKey: ['crawler-status'],
    queryFn: () => api.get<CrawlerStatus>('/crawler/status'),
    refetchInterval: 2000,
  });

  const { data: sites } = useQuery({
    queryKey: ['sites'],
    queryFn: () => api.get<Site[]>('/crawler/sites'),
  });

  const { data: tasks } = useQuery({
    queryKey: ['crawl-tasks'],
    queryFn: () => api.get<CrawlTask[]>('/crawler/tasks?limit=50'),
    refetchInterval: tab === 'history' ? 5000 : false,
  });

  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [status?.recent_logs]);

  const handleStart = async () => {
    setStarting(true);
    try {
      await api.post('/crawler/start', { mode, max_pages: maxPages, days: mode === 'by_date' ? days : null });
      queryClient.invalidateQueries({ queryKey: ['crawler-status'] });
    } catch (e: any) {
      alert(e.message);
    } finally {
      setStarting(false);
    }
  };

  const handleStop = async () => {
    setStopping(true);
    try {
      await api.post('/crawler/stop');
    } catch (e: any) {
      alert(e.message);
    } finally {
      setStopping(false);
    }
  };

  const handleToggleSite = async (siteId: string) => {
    try {
      await api.post(`/crawler/sites/${siteId}/toggle`);
      queryClient.invalidateQueries({ queryKey: ['sites'] });
    } catch (e: any) {
      alert(e.message);
    }
  };

  const handleDeleteSite = async (siteId: string) => {
    if (!confirm('确定删除该站点？')) return;
    try {
      await api.delete(`/crawler/sites/${siteId}`);
      queryClient.invalidateQueries({ queryKey: ['sites'] });
    } catch (e: any) {
      alert(e.message);
    }
  };

  const handleSaveSite = async () => {
    if (!siteForm.id || !siteForm.name || !siteForm.base_url) {
      alert('请填写必填字段');
      return;
    }
    try {
      if (editingSite) {
        await api.put(`/crawler/sites/${editingSite.id}`, siteForm);
      } else {
        await api.post('/crawler/sites', siteForm);
      }
      setShowSiteForm(false);
      setEditingSite(null);
      setSiteForm({ id: '', name: '', base_url: '', description: '', crawler_type: 'deep', enabled: true });
      queryClient.invalidateQueries({ queryKey: ['sites'] });
    } catch (e: any) {
      alert(e.message);
    }
  };

  const handleEditSite = (site: Site) => {
    setEditingSite(site);
    setSiteForm({ id: site.id, name: site.name, base_url: site.base_url, description: site.description, crawler_type: site.crawler_type, enabled: site.enabled });
    setShowSiteForm(true);
  };

  const handleOpenCreate = () => {
    setEditingSite(null);
    setSiteForm({ id: '', name: '', base_url: '', description: '', crawler_type: 'deep', enabled: true });
    setShowSiteForm(true);
  };

  const tabs: { key: Tab; label: string; icon: any }[] = [
    { key: 'control', label: '采集控制', icon: Play },
    { key: 'sites', label: '站点管理', icon: Globe },
    { key: 'history', label: '任务历史', icon: Clock },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold" style={{ color: 'var(--text)' }}>采集管理</h1>
        <div className="flex gap-1 rounded-lg p-1" style={{ backgroundColor: 'var(--bg)' }}>
          {tabs.map((t) => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={cn(
                'flex items-center gap-1.5 px-3 py-1.5 rounded text-sm transition-colors',
                tab === t.key ? 'text-white bg-blue-600' : 'text-gray-400 hover:text-white'
              )}
            >
              <t.icon className="w-3.5 h-3.5" />
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {tab === 'control' && (
        <>
          <div className="grid grid-cols-3 gap-4">
            <div className="rounded-lg p-5 shadow-sm border" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)' }}>
              <div className="text-xs mb-1" style={{ color: 'var(--text-sec)' }}>运行状态</div>
              <div className="flex items-center gap-2">
                <span className={cn('w-2.5 h-2.5 rounded-full', status?.is_running ? 'bg-green-500 animate-pulse' : 'bg-gray-400')} />
                <span className="text-lg font-bold" style={{ color: 'var(--text)' }}>
                  {status?.is_running ? '运行中' : '空闲'}
                </span>
              </div>
            </div>
            <div className="rounded-lg p-5 shadow-sm border" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)' }}>
              <div className="text-xs mb-1" style={{ color: 'var(--text-sec)' }}>当前模式</div>
              <div className="text-lg font-bold" style={{ color: 'var(--text)' }}>
                {{ incremental: '增量', full: '全量', by_date: '按时间', detail_only: '仅详情' }[status?.mode || 'incremental'] || '-'}
              </div>
            </div>
            <div className="rounded-lg p-5 shadow-sm border" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)' }}>
              <div className="text-xs mb-1" style={{ color: 'var(--text-sec)' }}>已耗时</div>
              <div className="text-lg font-bold" style={{ color: 'var(--text)' }}>{status?.elapsed || '-'}</div>
            </div>
          </div>

          {isAdmin && (
            <div className="rounded-lg p-5 shadow-sm border" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)' }}>
              <h3 className="text-sm font-medium mb-4" style={{ color: 'var(--text)' }}>启动采集</h3>
              <div className="flex flex-wrap gap-4 items-end">
                <div>
                  <label className="text-xs block mb-1" style={{ color: 'var(--text-sec)' }}>采集模式</label>
                  <select value={mode} onChange={(e) => setMode(e.target.value)} disabled={status?.is_running}
                    className="px-3 py-2 rounded border text-sm outline-none"
                    style={{ backgroundColor: 'var(--bg)', borderColor: 'var(--border)', color: 'var(--text)' }}>
                    <option value="incremental">增量采集</option>
                    <option value="full">全量采集</option>
                    <option value="by_date">按时间采集</option>
                    <option value="detail_only">仅抓详情</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs block mb-1" style={{ color: 'var(--text-sec)' }}>最大页数</label>
                  <input type="number" value={maxPages} onChange={(e) => setMaxPages(Number(e.target.value))} disabled={status?.is_running}
                    className="w-24 px-3 py-2 rounded border text-sm outline-none"
                    style={{ backgroundColor: 'var(--bg)', borderColor: 'var(--border)', color: 'var(--text)' }} />
                </div>
                {mode === 'by_date' && (
                  <div>
                    <label className="text-xs block mb-1" style={{ color: 'var(--text-sec)' }}>天数</label>
                    <input type="number" value={days} onChange={(e) => setDays(Number(e.target.value))}
                      className="w-24 px-3 py-2 rounded border text-sm outline-none"
                      style={{ backgroundColor: 'var(--bg)', borderColor: 'var(--border)', color: 'var(--text)' }} />
                  </div>
                )}
                <div className="flex gap-2">
                  <button onClick={handleStart} disabled={status?.is_running || starting}
                    className="flex items-center gap-1.5 px-4 py-2 rounded text-sm text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-40 transition-colors">
                    <Play className="w-4 h-4" /> {starting ? '启动中...' : '启动'}
                  </button>
                  <button onClick={handleStop} disabled={!status?.is_running || stopping}
                    className="flex items-center gap-1.5 px-4 py-2 rounded text-sm text-white bg-red-500 hover:bg-red-600 disabled:opacity-40 transition-colors">
                    <Square className="w-4 h-4" /> {stopping ? '停止中...' : '停止'}
                  </button>
                </div>
              </div>
            </div>
          )}

          <div className="rounded-lg shadow-sm border overflow-hidden" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)' }}>
            <div className="flex items-center justify-between px-4 py-2.5 border-b" style={{ borderColor: 'var(--border)' }}>
              <div className="flex items-center gap-2">
                <Terminal className="w-4 h-4" style={{ color: 'var(--text-sec)' }} />
                <span className="text-sm font-medium" style={{ color: 'var(--text)' }}>实时日志</span>
              </div>
              <span className="text-xs" style={{ color: 'var(--text-sec)' }}>{status?.log_count ?? 0} 条</span>
            </div>
            <div ref={logRef} className="h-80 overflow-y-auto p-3 font-mono text-xs space-y-0.5" style={{ backgroundColor: '#0d1117' }}>
              {(status?.recent_logs ?? []).length === 0 ? (
                <div className="text-gray-500">暂无日志</div>
              ) : (
                [...(status?.recent_logs ?? [])].reverse().map((log, i) => (
                  <div key={i} className={cn(
                    log.level === 'error' ? 'text-red-400' : log.level === 'warning' ? 'text-yellow-400' : 'text-gray-300'
                  )}>
                    <span className="text-gray-600">[{log.time}]</span> {log.msg}
                  </div>
                ))
              )}
            </div>
          </div>
        </>
      )}

      {tab === 'sites' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-medium" style={{ color: 'var(--text)' }}>已注册站点</h3>
              <p className="text-xs mt-0.5" style={{ color: 'var(--text-sec)' }}>管理数据采集的目标网站，支持多站点配置</p>
            </div>
            {isAdmin && (
              <button onClick={handleOpenCreate}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm text-white bg-blue-600 hover:bg-blue-700 transition-colors">
                <Plus className="w-3.5 h-3.5" /> 添加站点
              </button>
            )}
          </div>

          {(sites ?? []).length === 0 ? (
            <div className="rounded-lg p-12 text-center shadow-sm border" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)' }}>
              <Globe className="w-10 h-10 mx-auto mb-3" style={{ color: 'var(--text-sec)' }} />
              <p className="text-sm" style={{ color: 'var(--text-sec)' }}>暂无已注册站点</p>
              {isAdmin && (
                <button onClick={handleOpenCreate} className="mt-3 text-sm text-blue-600 hover:underline">添加第一个站点</button>
              )}
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-4">
              {(sites ?? []).map((site) => (
                <div key={site.id} className="rounded-lg shadow-sm border overflow-hidden transition-all hover:shadow-md" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)' }}>
                  <div className="px-4 py-3 border-b flex items-center justify-between" style={{ borderColor: 'var(--border)' }}>
                    <div className="flex items-center gap-2">
                      <div className={cn('w-2 h-2 rounded-full', site.enabled ? 'bg-green-500' : 'bg-gray-400')} />
                      <span className="text-sm font-semibold" style={{ color: 'var(--text)' }}>{site.name}</span>
                    </div>
                    <span className={cn(
                      'px-2 py-0.5 rounded-full text-xs',
                      site.enabled ? 'bg-green-50 text-green-600 dark:bg-green-900/30 dark:text-green-400' : 'bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400'
                    )}>
                      {site.enabled ? '启用' : '禁用'}
                    </span>
                  </div>
                  <div className="p-4 space-y-2">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-medium" style={{ color: 'var(--text-sec)' }}>ID:</span>
                      <span className="text-xs font-mono" style={{ color: 'var(--text)' }}>{site.id}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-medium" style={{ color: 'var(--text-sec)' }}>URL:</span>
                      <span className="text-xs truncate" style={{ color: 'var(--text-sec)' }}>{site.base_url}</span>
                    </div>
                    {site.description && (
                      <div className="text-xs" style={{ color: 'var(--text-sec)' }}>{site.description}</div>
                    )}
                    <div className="flex items-center gap-2 text-xs" style={{ color: 'var(--text-sec)' }}>
                      <span>类型: {site.crawler_type}</span>
                      <span className="mx-1">|</span>
                      <span>创建: {site.created_at ? site.created_at.slice(0, 10) : '-'}</span>
                    </div>
                  </div>
                  {isAdmin && (
                    <div className="flex border-t" style={{ borderColor: 'var(--border)' }}>
                      <button onClick={() => handleToggleSite(site.id)}
                        className="flex-1 flex items-center justify-center gap-1 py-2 text-xs transition-colors hover:bg-gray-50 dark:hover:bg-gray-800"
                        style={{ color: site.enabled ? '#52c41a' : '#8c8c8c' }}>
                        <Power className="w-3 h-3" /> {site.enabled ? '禁用' : '启用'}
                      </button>
                      <button onClick={() => handleEditSite(site)}
                        className="flex-1 flex items-center justify-center gap-1 py-2 text-xs transition-colors hover:bg-gray-50 dark:hover:bg-gray-800"
                        style={{ color: '#1677ff' }}>
                        <Edit2 className="w-3 h-3" /> 编辑
                      </button>
                      <button onClick={() => handleDeleteSite(site.id)}
                        className="flex-1 flex items-center justify-center gap-1 py-2 text-xs transition-colors hover:bg-gray-50 dark:hover:bg-gray-800"
                        style={{ color: '#ff4d4f' }}>
                        <Trash2 className="w-3 h-3" /> 删除
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {tab === 'history' && (
        <div className="space-y-4">
          <h3 className="text-sm font-medium" style={{ color: 'var(--text)' }}>任务历史</h3>
          <div className="rounded-lg shadow-sm border overflow-hidden" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)' }}>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b" style={{ borderColor: 'var(--border)' }}>
                  <th className="text-left px-4 py-2.5 font-medium" style={{ color: 'var(--text-sec)' }}>任务ID</th>
                  <th className="text-left px-4 py-2.5 font-medium" style={{ color: 'var(--text-sec)' }}>模式</th>
                  <th className="text-left px-4 py-2.5 font-medium" style={{ color: 'var(--text-sec)' }}>状态</th>
                  <th className="text-left px-4 py-2.5 font-medium" style={{ color: 'var(--text-sec)' }}>列表</th>
                  <th className="text-left px-4 py-2.5 font-medium" style={{ color: 'var(--text-sec)' }}>详情</th>
                  <th className="text-left px-4 py-2.5 font-medium" style={{ color: 'var(--text-sec)' }}>总记录</th>
                  <th className="text-left px-4 py-2.5 font-medium" style={{ color: 'var(--text-sec)' }}>有中标</th>
                  <th className="text-left px-4 py-2.5 font-medium" style={{ color: 'var(--text-sec)' }}>耗时</th>
                  <th className="text-left px-4 py-2.5 font-medium" style={{ color: 'var(--text-sec)' }}>开始时间</th>
                </tr>
              </thead>
              <tbody>
                {(tasks ?? []).map((t) => (
                  <tr key={t.id} className="border-b last:border-0" style={{ borderColor: 'var(--border)' }}>
                    <td className="px-4 py-3 font-mono text-xs" style={{ color: 'var(--text)' }}>{t.id.slice(0, 16)}...</td>
                    <td className="px-4 py-3" style={{ color: 'var(--text-sec)' }}>
                      {{ incremental: '增量', full: '全量', by_date: '按时间', detail_only: '仅详情' }[t.mode] || t.mode}
                    </td>
                    <td className="px-4 py-3">
                      <span className={cn(
                        'inline-flex items-center px-2 py-0.5 rounded-full text-xs',
                        t.status === 'completed' ? 'bg-green-50 text-green-600 dark:bg-green-900/30 dark:text-green-400' :
                        t.status === 'error' ? 'bg-red-50 text-red-600 dark:bg-red-900/30 dark:text-red-400' :
                        'bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400'
                      )}>
                        {t.status === 'completed' ? '完成' : t.status === 'error' ? '失败' : '运行中'}
                      </span>
                    </td>
                    <td className="px-4 py-3" style={{ color: 'var(--text)' }}>{t.list_count}</td>
                    <td className="px-4 py-3" style={{ color: 'var(--text)' }}>{t.detail_count}</td>
                    <td className="px-4 py-3" style={{ color: 'var(--text)' }}>{t.total_records}</td>
                    <td className="px-4 py-3" style={{ color: 'var(--text)' }}>{t.with_winner}</td>
                    <td className="px-4 py-3" style={{ color: 'var(--text-sec)' }}>{t.elapsed_seconds ? `${t.elapsed_seconds.toFixed(1)}s` : '-'}</td>
                    <td className="px-4 py-3 text-xs" style={{ color: 'var(--text-sec)' }}>{t.started_at ? t.started_at.slice(0, 19).replace('T', ' ') : '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <SiteModal
        open={showSiteForm}
        editing={editingSite}
        form={siteForm}
        onChange={setSiteForm}
        onSave={handleSaveSite}
        onClose={() => { setShowSiteForm(false); setEditingSite(null); }}
      />
    </div>
  );
}
