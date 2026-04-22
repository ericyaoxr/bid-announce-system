import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Plus, Trash2, Send, ToggleLeft, ToggleRight, Settings } from 'lucide-react';
import { api } from '../lib/api';
import { useAuth } from '../lib/auth';
import { cn } from '../lib/utils';

interface NotifConfig {
  id: string;
  name: string;
  ntype: string;
  enabled: boolean;
  config: Record<string, any>;
  created_at: string;
  updated_at: string;
}

const TYPE_OPTIONS = [
  { value: 'webhook', label: 'Webhook', color: 'bg-blue-500' },
  { value: 'feishu', label: '飞书', color: 'bg-indigo-500' },
  { value: 'dingtalk', label: '钉钉', color: 'bg-orange-500' },
  { value: 'wecom', label: '企业微信', color: 'bg-green-500' },
  { value: 'email', label: 'Email', color: 'bg-red-500' },
];

const DEFAULT_CONFIGS: Record<string, Record<string, any>> = {
  webhook: { url: '', method: 'POST', headers: {} },
  feishu: { webhook_url: '', secret: '' },
  dingtalk: { webhook_url: '', secret: '' },
  wecom: { webhook_url: '' },
  email: { smtp_host: '', smtp_port: 465, username: '', password: '', use_ssl: true, sender: '', recipients: [] },
};

export function Notifications() {
  const { isAdmin } = useAuth();
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<NotifConfig | null>(null);
  const [form, setForm] = useState({ name: '', ntype: 'webhook', enabled: true, config: {} as Record<string, any> });
  const [testing, setTesting] = useState(false);

  const { data: configs } = useQuery({
    queryKey: ['notifications'],
    queryFn: () => api.get<NotifConfig[]>('/notifications/configs'),
  });

  const handleOpenCreate = () => {
    setEditing(null);
    setForm({ name: '', ntype: 'webhook', enabled: true, config: { ...DEFAULT_CONFIGS.webhook } });
    setShowForm(true);
  };

  const handleOpenEdit = (c: NotifConfig) => {
    setEditing(c);
    setForm({ name: c.name, ntype: c.ntype, enabled: c.enabled, config: { ...c.config } });
    setShowForm(true);
  };

  const handleSave = async () => {
    try {
      if (editing) {
        await api.put(`/notifications/configs/${editing.id}`, { name: form.name, ntype: form.ntype, enabled: form.enabled, config: form.config });
      } else {
        await api.post('/notifications/configs', { name: form.name, ntype: form.ntype, enabled: form.enabled, config: form.config });
      }
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      setShowForm(false);
    } catch (e: any) {
      alert(e.message);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('确定删除此通知配置？')) return;
    try {
      await api.delete(`/notifications/configs/${id}`);
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    } catch (e: any) {
      alert(e.message);
    }
  };

  const handleToggle = async (id: string) => {
    try {
      await api.post(`/notifications/configs/${id}/toggle`);
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    } catch (e: any) {
      alert(e.message);
    }
  };

  const handleTest = async () => {
    setTesting(true);
    try {
      const res = await api.post('/notifications/test', { title: '测试通知', content: '这是一条测试通知，用于验证配置是否正确。' });
      const results = (res as any).results || {};
      const msgs = Object.entries(results).map(([k, v]) => `${k}: ${v ? '成功' : '失败'}`).join('\n');
      alert('测试结果:\n' + msgs);
    } catch (e: any) {
      alert(e.message);
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold" style={{ color: 'var(--text)' }}>通知推送</h1>
        <div className="flex gap-2">
          <button onClick={handleTest} disabled={testing}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm border transition-colors"
            style={{ color: 'var(--text)', borderColor: 'var(--border)' }}>
            <Send className="w-4 h-4" /> {testing ? '发送中...' : '测试推送'}
          </button>
          {isAdmin && (
            <button onClick={handleOpenCreate}
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm text-white bg-blue-600 hover:bg-blue-700 transition-colors">
              <Plus className="w-4 h-4" /> 新建配置
            </button>
          )}
        </div>
      </div>

      {isAdmin && showForm && (
        <div className="rounded-lg p-5 shadow-sm border" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)' }}>
          <h3 className="text-sm font-medium mb-4 flex items-center gap-2" style={{ color: 'var(--text)' }}>
            <Settings className="w-4 h-4" /> {editing ? '编辑通知配置' : '新建通知配置'}
          </h3>
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label className="text-xs block mb-1.5 font-medium" style={{ color: 'var(--text-sec)' }}>名称</label>
              <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="w-full px-3 py-2 rounded-lg border text-sm outline-none focus:ring-2 focus:ring-blue-400"
                style={{ backgroundColor: 'var(--bg)', borderColor: 'var(--border)', color: 'var(--text)' }}
                placeholder="例如：飞书告警群" />
            </div>
            <div>
              <label className="text-xs block mb-1.5 font-medium" style={{ color: 'var(--text-sec)' }}>类型</label>
              <select value={form.ntype} onChange={(e) => setForm({ ...form, ntype: e.target.value, config: { ...DEFAULT_CONFIGS[e.target.value] } })}
                className="w-full px-3 py-2 rounded-lg border text-sm outline-none focus:ring-2 focus:ring-blue-400"
                style={{ backgroundColor: 'var(--bg)', borderColor: 'var(--border)', color: 'var(--text)' }}>
                {TYPE_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="mb-4 space-y-3">
            {form.ntype === 'webhook' && (
              <>
                <div>
                  <label className="text-xs block mb-1.5 font-medium" style={{ color: 'var(--text-sec)' }}>Webhook URL</label>
                  <input value={form.config.url || ''} onChange={(e) => setForm({ ...form, config: { ...form.config, url: e.target.value } })}
                    className="w-full px-3 py-2 rounded-lg border text-sm outline-none focus:ring-2 focus:ring-blue-400 font-mono"
                    style={{ backgroundColor: 'var(--bg)', borderColor: 'var(--border)', color: 'var(--text)' }}
                    placeholder="https://example.com/webhook" />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs block mb-1.5 font-medium" style={{ color: 'var(--text-sec)' }}>Method</label>
                    <select value={form.config.method || 'POST'} onChange={(e) => setForm({ ...form, config: { ...form.config, method: e.target.value } })}
                      className="w-full px-3 py-2 rounded-lg border text-sm outline-none focus:ring-2 focus:ring-blue-400"
                      style={{ backgroundColor: 'var(--bg)', borderColor: 'var(--border)', color: 'var(--text)' }}>
                      <option value="POST">POST</option>
                      <option value="PUT">PUT</option>
                      <option value="PATCH">PATCH</option>
                    </select>
                  </div>
                </div>
              </>
            )}

            {form.ntype === 'feishu' && (
              <>
                <div>
                  <label className="text-xs block mb-1.5 font-medium" style={{ color: 'var(--text-sec)' }}>Webhook URL</label>
                  <input value={form.config.webhook_url || ''} onChange={(e) => setForm({ ...form, config: { ...form.config, webhook_url: e.target.value } })}
                    className="w-full px-3 py-2 rounded-lg border text-sm outline-none focus:ring-2 focus:ring-blue-400 font-mono"
                    style={{ backgroundColor: 'var(--bg)', borderColor: 'var(--border)', color: 'var(--text)' }}
                    placeholder="https://open.feishu.cn/open-apis/bot/v2/hook/..." />
                </div>
                <div>
                  <label className="text-xs block mb-1.5 font-medium" style={{ color: 'var(--text-sec)' }}>签名密钥 (可选)</label>
                  <input value={form.config.secret || ''} onChange={(e) => setForm({ ...form, config: { ...form.config, secret: e.target.value } })}
                    className="w-full px-3 py-2 rounded-lg border text-sm outline-none focus:ring-2 focus:ring-blue-400"
                    style={{ backgroundColor: 'var(--bg)', borderColor: 'var(--border)', color: 'var(--text)' }} />
                </div>
              </>
            )}

            {form.ntype === 'dingtalk' && (
              <>
                <div>
                  <label className="text-xs block mb-1.5 font-medium" style={{ color: 'var(--text-sec)' }}>Webhook URL</label>
                  <input value={form.config.webhook_url || ''} onChange={(e) => setForm({ ...form, config: { ...form.config, webhook_url: e.target.value } })}
                    className="w-full px-3 py-2 rounded-lg border text-sm outline-none focus:ring-2 focus:ring-blue-400 font-mono"
                    style={{ backgroundColor: 'var(--bg)', borderColor: 'var(--border)', color: 'var(--text)' }}
                    placeholder="https://oapi.dingtalk.com/robot/send?access_token=..." />
                </div>
                <div>
                  <label className="text-xs block mb-1.5 font-medium" style={{ color: 'var(--text-sec)' }}>签名密钥 (可选)</label>
                  <input value={form.config.secret || ''} onChange={(e) => setForm({ ...form, config: { ...form.config, secret: e.target.value } })}
                    className="w-full px-3 py-2 rounded-lg border text-sm outline-none focus:ring-2 focus:ring-blue-400"
                    style={{ backgroundColor: 'var(--bg)', borderColor: 'var(--border)', color: 'var(--text)' }} />
                </div>
              </>
            )}

            {form.ntype === 'wecom' && (
              <div>
                <label className="text-xs block mb-1.5 font-medium" style={{ color: 'var(--text-sec)' }}>Webhook URL</label>
                <input value={form.config.webhook_url || ''} onChange={(e) => setForm({ ...form, config: { ...form.config, webhook_url: e.target.value } })}
                  className="w-full px-3 py-2 rounded-lg border text-sm outline-none focus:ring-2 focus:ring-blue-400 font-mono"
                  style={{ backgroundColor: 'var(--bg)', borderColor: 'var(--border)', color: 'var(--text)' }}
                  placeholder="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=..." />
              </div>
            )}

            {form.ntype === 'email' && (
              <>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs block mb-1.5 font-medium" style={{ color: 'var(--text-sec)' }}>SMTP 服务器</label>
                    <input value={form.config.smtp_host || ''} onChange={(e) => setForm({ ...form, config: { ...form.config, smtp_host: e.target.value } })}
                      className="w-full px-3 py-2 rounded-lg border text-sm outline-none focus:ring-2 focus:ring-blue-400"
                      style={{ backgroundColor: 'var(--bg)', borderColor: 'var(--border)', color: 'var(--text)' }}
                      placeholder="smtp.example.com" />
                  </div>
                  <div>
                    <label className="text-xs block mb-1.5 font-medium" style={{ color: 'var(--text-sec)' }}>端口</label>
                    <input type="number" value={form.config.smtp_port || 465} onChange={(e) => setForm({ ...form, config: { ...form.config, smtp_port: Number(e.target.value) } })}
                      className="w-full px-3 py-2 rounded-lg border text-sm outline-none focus:ring-2 focus:ring-blue-400"
                      style={{ backgroundColor: 'var(--bg)', borderColor: 'var(--border)', color: 'var(--text)' }} />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs block mb-1.5 font-medium" style={{ color: 'var(--text-sec)' }}>用户名</label>
                    <input value={form.config.username || ''} onChange={(e) => setForm({ ...form, config: { ...form.config, username: e.target.value } })}
                      className="w-full px-3 py-2 rounded-lg border text-sm outline-none focus:ring-2 focus:ring-blue-400"
                      style={{ backgroundColor: 'var(--bg)', borderColor: 'var(--border)', color: 'var(--text)' }} />
                  </div>
                  <div>
                    <label className="text-xs block mb-1.5 font-medium" style={{ color: 'var(--text-sec)' }}>密码</label>
                    <input type="password" value={form.config.password || ''} onChange={(e) => setForm({ ...form, config: { ...form.config, password: e.target.value } })}
                      className="w-full px-3 py-2 rounded-lg border text-sm outline-none focus:ring-2 focus:ring-blue-400"
                      style={{ backgroundColor: 'var(--bg)', borderColor: 'var(--border)', color: 'var(--text)' }} />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs block mb-1.5 font-medium" style={{ color: 'var(--text-sec)' }}>发件人</label>
                    <input value={form.config.sender || ''} onChange={(e) => setForm({ ...form, config: { ...form.config, sender: e.target.value } })}
                      className="w-full px-3 py-2 rounded-lg border text-sm outline-none focus:ring-2 focus:ring-blue-400"
                      style={{ backgroundColor: 'var(--bg)', borderColor: 'var(--border)', color: 'var(--text)' }} />
                  </div>
                  <div>
                    <label className="text-xs block mb-1.5 font-medium" style={{ color: 'var(--text-sec)' }}>收件人 (逗号分隔)</label>
                    <input value={(form.config.recipients || []).join(', ')} onChange={(e) => setForm({ ...form, config: { ...form.config, recipients: e.target.value.split(',').map((s: string) => s.trim()).filter(Boolean) } })}
                      className="w-full px-3 py-2 rounded-lg border text-sm outline-none focus:ring-2 focus:ring-blue-400"
                      style={{ backgroundColor: 'var(--bg)', borderColor: 'var(--border)', color: 'var(--text)' }} />
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <input type="checkbox" checked={form.config.use_ssl ?? true} onChange={(e) => setForm({ ...form, config: { ...form.config, use_ssl: e.target.checked } })} />
                  <label className="text-sm" style={{ color: 'var(--text)' }}>使用 SSL</label>
                </div>
              </>
            )}
          </div>

          <div className="flex gap-2 justify-end">
            <button onClick={() => setShowForm(false)}
              className="px-4 py-2 rounded text-sm border transition-colors"
              style={{ color: 'var(--text)', borderColor: 'var(--border)' }}>
              取消
            </button>
            <button onClick={handleSave}
              className="px-4 py-2 rounded text-sm text-white bg-blue-600 hover:bg-blue-700 transition-colors">
              {editing ? '保存' : '创建'}
            </button>
          </div>
        </div>
      )}

      <div className="rounded-lg shadow-sm border overflow-hidden" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)' }}>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b" style={{ borderColor: 'var(--border)' }}>
              <th className="text-left px-4 py-3 font-medium" style={{ color: 'var(--text-sec)' }}>名称</th>
              <th className="text-left px-4 py-3 font-medium" style={{ color: 'var(--text-sec)' }}>类型</th>
              <th className="text-left px-4 py-3 font-medium" style={{ color: 'var(--text-sec)' }}>状态</th>
              <th className="text-left px-4 py-3 font-medium" style={{ color: 'var(--text-sec)' }}>更新时间</th>
              {isAdmin && <th className="text-right px-4 py-3 font-medium" style={{ color: 'var(--text-sec)' }}>操作</th>}
            </tr>
          </thead>
          <tbody>
            {(!configs || configs.length === 0) ? (
              <tr>
                <td colSpan={5} className="text-center py-8" style={{ color: 'var(--text-sec)' }}>
                  暂无通知配置，{isAdmin && '点击"新建配置"添加'}
                </td>
              </tr>
            ) : (
              configs.map((c) => {
                const typeOpt = TYPE_OPTIONS.find((o) => o.value === c.ntype);
                return (
                  <tr key={c.id} className="border-b last:border-0" style={{ borderColor: 'var(--border)' }}>
                    <td className="px-4 py-3" style={{ color: 'var(--text)' }}>{c.name}</td>
                    <td className="px-4 py-3">
                      <span className={cn('inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs text-white', typeOpt?.color)}>
                        {typeOpt?.label || c.ntype}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={cn(
                        'inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium',
                        c.enabled ? 'bg-green-50 text-green-700 dark:bg-green-900/30 dark:text-green-400' : 'bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400'
                      )}>
                        <span className={cn('w-1.5 h-1.5 rounded-full', c.enabled ? 'bg-green-500' : 'bg-gray-400')} />
                        {c.enabled ? '启用' : '禁用'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs" style={{ color: 'var(--text-sec)' }}>{c.updated_at ? c.updated_at.slice(0, 19).replace('T', ' ') : '-'}</td>
                    {isAdmin && (
                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end gap-1">
                          <button onClick={() => handleToggle(c.id)} className="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-800">
                            {c.enabled ? <ToggleRight className="w-5 h-5 text-green-500" /> : <ToggleLeft className="w-5 h-5 text-gray-400" />}
                          </button>
                          <button onClick={() => handleOpenEdit(c)} className="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-800">
                            <Settings className="w-4 h-4" style={{ color: 'var(--text-sec)' }} />
                          </button>
                          <button onClick={() => handleDelete(c.id)} className="p-1.5 rounded hover:bg-red-50 dark:hover:bg-red-900/30">
                            <Trash2 className="w-4 h-4 text-red-400" />
                          </button>
                        </div>
                      </td>
                    )}
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
