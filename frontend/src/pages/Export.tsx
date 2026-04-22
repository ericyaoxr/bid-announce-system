import { useState } from 'react';
import { Download, FileSpreadsheet, Eye, Search } from 'lucide-react';
import { api } from '../lib/api';
import { formatAmount, formatDate } from '../lib/utils';

interface AnnouncementPreview {
  id: string;
  title: string;
  project_no: string;
  category: string;
  tender_mode: string;
  publish_date: string;
  bid_price: number | null;
  tenderer_name: string | null;
  winner_supplier: string;
  winner_amount: number | null;
}

function getWinningSupplier(item: AnnouncementPreview): string {
  return item.winner_supplier || '-';
}

export function Export() {
  const [keyword, setKeyword] = useState('');
  const [category, setCategory] = useState('');
  const [tenderMode, setTenderMode] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [preview, setPreview] = useState<AnnouncementPreview[] | null>(null);
  const [previewTotal, setPreviewTotal] = useState(0);
  const [previewLoading, setPreviewLoading] = useState(false);

  const buildParams = () => {
    const params = new URLSearchParams();
    if (keyword) params.set('keyword', keyword);
    if (category) params.set('category', category);
    if (tenderMode) params.set('tender_mode', tenderMode);
    if (startDate) params.set('start_date', startDate);
    if (endDate) params.set('end_date', endDate);
    return params.toString();
  };

  const handlePreview = async () => {
    setPreviewLoading(true);
    setPreview(null);
    try {
      const params = buildParams();
      const res = await api.get<any>(`/announcements?${params}&page=1&size=10`);
      setPreview(res.items || []);
      setPreviewTotal(res.total || 0);
    } catch (e: any) {
      alert(e.message);
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleExport = (format: 'csv' | 'excel') => {
    const token = localStorage.getItem('token');
    const params = buildParams();
    const url = `/api/export/${format}${params ? '?' + params : ''}`;
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', '');
    fetch(url, { headers: { Authorization: `Bearer ${token}` } })
      .then((res) => {
        if (!res.ok) throw new Error('导出失败');
        const disposition = res.headers.get('content-disposition');
        const filename = disposition
          ? decodeURIComponent(disposition.split("filename*=UTF-8''")[1] || disposition.split('filename=')[1] || `export.${format === 'csv' ? 'csv' : 'xlsx'}`)
          : `export.${format === 'csv' ? 'csv' : 'xlsx'}`;
        return res.blob().then((blob) => ({ blob, filename }));
      })
      .then(({ blob, filename }) => {
        const objUrl = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = objUrl;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(objUrl);
      })
      .catch((e) => alert(e.message));
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold" style={{ color: 'var(--text)' }}>数据导出</h1>

      <div className="rounded-lg p-5 shadow-sm border space-y-4" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)' }}>
        <h3 className="text-sm font-medium" style={{ color: 'var(--text)' }}>筛选条件</h3>
        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="text-xs block mb-1" style={{ color: 'var(--text-sec)' }}>关键词</label>
            <input value={keyword} onChange={(e) => setKeyword(e.target.value)}
              placeholder="搜索标题、项目编号..."
              className="w-full px-3 py-2 rounded border text-sm outline-none"
              style={{ backgroundColor: 'var(--bg)', borderColor: 'var(--border)', color: 'var(--text)' }} />
          </div>
          <div>
            <label className="text-xs block mb-1" style={{ color: 'var(--text-sec)' }}>分类</label>
            <select value={category} onChange={(e) => setCategory(e.target.value)}
              className="w-full px-3 py-2 rounded border text-sm outline-none"
              style={{ backgroundColor: 'var(--bg)', borderColor: 'var(--border)', color: 'var(--text)' }}>
              <option value="">全部</option>
              <option value="工程">工程</option>
              <option value="货物">货物</option>
              <option value="服务">服务</option>
            </select>
          </div>
          <div>
            <label className="text-xs block mb-1" style={{ color: 'var(--text-sec)' }}>招标方式</label>
            <select value={tenderMode} onChange={(e) => setTenderMode(e.target.value)}
              className="w-full px-3 py-2 rounded border text-sm outline-none"
              style={{ backgroundColor: 'var(--bg)', borderColor: 'var(--border)', color: 'var(--text)' }}>
              <option value="">全部</option>
              <option value="公开招标">公开招标</option>
              <option value="邀请招标">邀请招标</option>
              <option value="竞争性谈判">竞争性谈判</option>
              <option value="竞争性磋商">竞争性磋商</option>
              <option value="单一来源">单一来源</option>
            </select>
          </div>
          <div>
            <label className="text-xs block mb-1" style={{ color: 'var(--text-sec)' }}>开始日期</label>
            <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)}
              className="w-full px-3 py-2 rounded border text-sm outline-none"
              style={{ backgroundColor: 'var(--bg)', borderColor: 'var(--border)', color: 'var(--text)' }} />
          </div>
          <div>
            <label className="text-xs block mb-1" style={{ color: 'var(--text-sec)' }}>结束日期</label>
            <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)}
              className="w-full px-3 py-2 rounded border text-sm outline-none"
              style={{ backgroundColor: 'var(--bg)', borderColor: 'var(--border)', color: 'var(--text)' }} />
          </div>
        </div>

        <div className="flex gap-3 pt-2">
          <button onClick={handlePreview} disabled={previewLoading}
            className="flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium border transition-colors disabled:opacity-40"
            style={{ color: 'var(--text)', borderColor: 'var(--border)' }}>
            <Search className="w-4 h-4" /> {previewLoading ? '加载中...' : '预览数据'}
          </button>
          <button onClick={() => handleExport('csv')}
            className="flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium text-white bg-green-600 hover:bg-green-700 transition-colors">
            <Download className="w-4 h-4" /> 导出 CSV
          </button>
          <button onClick={() => handleExport('excel')}
            className="flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 transition-colors">
            <FileSpreadsheet className="w-4 h-4" /> 导出 Excel
          </button>
        </div>
      </div>

      {preview !== null && (
        <div className="rounded-lg shadow-sm border overflow-hidden" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)' }}>
          <div className="flex items-center justify-between px-4 py-2.5 border-b" style={{ borderColor: 'var(--border)' }}>
            <div className="flex items-center gap-2">
              <Eye className="w-4 h-4" style={{ color: 'var(--text-sec)' }} />
              <span className="text-sm font-medium" style={{ color: 'var(--text)' }}>数据预览</span>
            </div>
            <span className="text-xs" style={{ color: 'var(--text-sec)' }}>
              共 {previewTotal} 条，显示前 10 条
            </span>
          </div>
          {preview.length === 0 ? (
            <div className="py-12 text-center" style={{ color: 'var(--text-sec)' }}>
              没有符合条件的数据
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b" style={{ borderColor: 'var(--border)' }}>
                    <th className="text-left px-4 py-2.5 font-medium" style={{ color: 'var(--text-sec)' }}>标题</th>
                    <th className="text-left px-4 py-2.5 font-medium" style={{ color: 'var(--text-sec)' }}>招标单位</th>
                    <th className="text-left px-4 py-2.5 font-medium" style={{ color: 'var(--text-sec)' }}>中标人</th>
                    <th className="text-left px-4 py-2.5 font-medium" style={{ color: 'var(--text-sec)' }}>中标金额</th>
                    <th className="text-left px-4 py-2.5 font-medium" style={{ color: 'var(--text-sec)' }}>发布日期</th>
                  </tr>
                </thead>
                <tbody>
                  {preview.map((item) => (
                    <tr key={item.id} className="border-b last:border-0" style={{ borderColor: 'var(--border)' }}>
                      <td className="px-4 py-2.5 max-w-xs truncate" style={{ color: 'var(--text)' }} title={item.title}>{item.title}</td>
                      <td className="px-4 py-2.5" style={{ color: 'var(--text-sec)' }}>{item.tenderer_name || '-'}</td>
                      <td className="px-4 py-2.5 max-w-xs truncate" style={{ color: 'var(--text)' }} title={getWinningSupplier(item)}>{getWinningSupplier(item)}</td>
                      <td className="px-4 py-2.5 font-medium" style={{ color: 'var(--text)' }}>{formatAmount(item.winner_amount)}</td>
                      <td className="px-4 py-2.5" style={{ color: 'var(--text-sec)' }}>{formatDate(item.publish_date)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
