import { useQuery } from '@tanstack/react-query';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { api, type DashboardStats } from '../lib/api';
import { formatAmount } from '../lib/utils';

export function Winners() {
  const { data } = useQuery({
    queryKey: ['dashboard'],
    queryFn: () => api.get<DashboardStats>('/dashboard'),
  });

  if (!data) return <div className="text-center py-20" style={{ color: 'var(--text-sec)' }}>加载中...</div>;

  const topAmountData = data.top_amount_companies?.slice(0, 10).map((c) => ({
    name: c.name.length > 8 ? c.name.slice(0, 8) + '...' : c.name,
    amount: c.total_amount,
    count: c.count,
  })) || [];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold" style={{ color: 'var(--text)' }}>中标分析</h1>

      <div className="grid grid-cols-2 gap-6">
        <div className="rounded-lg p-5 shadow-sm border" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)' }}>
          <h3 className="text-sm font-medium mb-4" style={{ color: 'var(--text)' }}>中标金额TOP10</h3>
          <ResponsiveContainer width="100%" height={350}>
            <BarChart data={topAmountData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis type="number" tick={{ fontSize: 10 }} stroke="var(--text-sec)" tickFormatter={(v) => `${(v / 10000).toFixed(0)}万`} />
              <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} stroke="var(--text-sec)" width={80} />
              <Tooltip formatter={(value: unknown) => formatAmount(value as number | null)} />
              <Bar dataKey="amount" fill="#1677ff" radius={[0, 4, 4, 0]} name="中标金额" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="rounded-lg p-5 shadow-sm border" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)' }}>
          <h3 className="text-sm font-medium mb-4" style={{ color: 'var(--text)' }}>中标次数TOP10</h3>
          <div className="space-y-2">
            {data.top_count_companies?.slice(0, 10).map((c, i) => (
              <div key={i} className="flex items-center justify-between py-2 px-3 rounded text-sm">
                <div className="flex items-center gap-2">
                  <span className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white"
                    style={{ backgroundColor: i < 3 ? '#1677ff' : '#8c8c8c' }}>
                    {i + 1}
                  </span>
                  <span style={{ color: 'var(--text)' }}>{c.name}</span>
                </div>
                <div className="flex items-center gap-4">
                  <span className="font-medium" style={{ color: 'var(--primary)' }}>{c.count}次</span>
                  <span className="text-xs" style={{ color: 'var(--text-sec)' }}>{formatAmount(c.total_amount)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
