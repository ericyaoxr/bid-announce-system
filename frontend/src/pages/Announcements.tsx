import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search, ExternalLink } from 'lucide-react';
import { api, type AnnouncementListResponse } from '../lib/api';
import { formatDate, formatAmount } from '../lib/utils';

export function Announcements() {
  const [page, setPage] = useState(1);
  const [keyword, setKeyword] = useState('');
  const [searchKeyword, setSearchKeyword] = useState('');
  const [category, setCategory] = useState('');
  const [tenderMode, setTenderMode] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['announcements', page, searchKeyword, category, tenderMode, startDate, endDate],
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page), size: '20' });
      if (searchKeyword) params.set('keyword', searchKeyword);
      if (category) params.set('category', category);
      if (tenderMode) params.set('tender_mode', tenderMode);
      if (startDate) params.set('start_date', startDate);
      if (endDate) params.set('end_date', endDate);
      return api.get<AnnouncementListResponse>(`/announcements?${params}`);
    },
  });

  const handleSearch = () => {
    setPage(1);
    setSearchKeyword(keyword);
  };

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold" style={{ color: 'var(--text)' }}>公告列表</h1>

      <div className="rounded-lg p-4 shadow-sm border flex flex-wrap gap-3 items-end" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)' }}>
        <div className="flex-1 min-w-[200px]">
          <label className="text-xs block mb-1" style={{ color: 'var(--text-sec)' }}>关键词</label>
          <div className="relative">
            <input
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="搜索标题、项目编号、招标人..."
              className="w-full pl-3 pr-9 py-2 rounded border text-sm outline-none focus:ring-2 focus:ring-blue-400"
              style={{ backgroundColor: 'var(--bg)', borderColor: 'var(--border)', color: 'var(--text)' }}
            />
            <button onClick={handleSearch} className="absolute right-2 top-1/2 -translate-y-1/2">
              <Search className="w-4 h-4" style={{ color: 'var(--text-sec)' }} />
            </button>
          </div>
        </div>
        <div>
          <label className="text-xs block mb-1" style={{ color: 'var(--text-sec)' }}>分类</label>
          <select value={category} onChange={(e) => { setCategory(e.target.value); setPage(1); }}
            className="px-3 py-2 rounded border text-sm outline-none"
            style={{ backgroundColor: 'var(--bg)', borderColor: 'var(--border)', color: 'var(--text)' }}>
            <option value="">全部</option>
            <option value="工程">工程</option>
            <option value="货物">货物</option>
            <option value="服务">服务</option>
          </select>
        </div>
        <div>
          <label className="text-xs block mb-1" style={{ color: 'var(--text-sec)' }}>招标方式</label>
          <select value={tenderMode} onChange={(e) => { setTenderMode(e.target.value); setPage(1); }}
            className="px-3 py-2 rounded border text-sm outline-none"
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
          <input type="date" value={startDate} onChange={(e) => { setStartDate(e.target.value); setPage(1); }}
            className="px-3 py-2 rounded border text-sm outline-none"
            style={{ backgroundColor: 'var(--bg)', borderColor: 'var(--border)', color: 'var(--text)' }} />
        </div>
        <div>
          <label className="text-xs block mb-1" style={{ color: 'var(--text-sec)' }}>结束日期</label>
          <input type="date" value={endDate} onChange={(e) => { setEndDate(e.target.value); setPage(1); }}
            className="px-3 py-2 rounded border text-sm outline-none"
            style={{ backgroundColor: 'var(--bg)', borderColor: 'var(--border)', color: 'var(--text)' }} />
        </div>
      </div>

      {isLoading ? (
        <div className="text-center py-20" style={{ color: 'var(--text-sec)' }}>加载中...</div>
      ) : (
        <>
          <div className="text-sm" style={{ color: 'var(--text-sec)' }}>
            共 {data?.total ?? 0} 条记录
          </div>
          <div className="space-y-2">
            {data?.items.map((item) => (
              <div key={item.id} className="rounded-lg p-4 shadow-sm border hover:shadow-md transition-shadow" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)' }}>
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-medium truncate" style={{ color: 'var(--text)' }}>{item.title}</h3>
                    <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2 text-xs" style={{ color: 'var(--text-sec)' }}>
                      {item.project_no && <span>编号: {item.project_no}</span>}
                      {item.category && <span>分类: {item.category}</span>}
                      {item.tender_mode_desc && <span>方式: {item.tender_mode_desc}</span>}
                      {item.tenderer_name && <span>招标人: {item.tenderer_name}</span>}
                      {item.publish_date && <span>发布: {formatDate(item.publish_date)}</span>}
                    </div>
                    {item.winner_supplier && (
                      <div className="mt-2 flex items-center gap-3 text-xs">
                        <span className="px-2 py-0.5 rounded font-medium text-green-700 bg-green-50 dark:text-green-400 dark:bg-green-900/30">
                          中标: {item.winner_supplier}
                        </span>
                        {item.winner_amount != null && (
                          <span className="font-medium" style={{ color: 'var(--danger)' }}>{formatAmount(item.winner_amount)}</span>
                        )}
                      </div>
                    )}
                  </div>
                  <div className="flex gap-1.5">
                    {item.source_url && (
                      <a href={item.source_url} target="_blank" rel="noopener noreferrer"
                        className="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
                        <ExternalLink className="w-4 h-4" style={{ color: 'var(--text-sec)' }} />
                      </a>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {data && data.total > 20 && (
            <div className="flex items-center justify-center gap-2 pt-4">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-3 py-1.5 rounded border text-sm disabled:opacity-40"
                style={{ borderColor: 'var(--border)', color: 'var(--text)' }}
              >上一页</button>
              <span className="text-sm" style={{ color: 'var(--text-sec)' }}>
                第 {page} / {Math.ceil(data.total / 20)} 页
              </span>
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={page >= Math.ceil(data.total / 20)}
                className="px-3 py-1.5 rounded border text-sm disabled:opacity-40"
                style={{ borderColor: 'var(--border)', color: 'var(--text)' }}
              >下一页</button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
