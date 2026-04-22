import { useQuery } from '@tanstack/react-query';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, LineChart, Line } from 'recharts';
import { TrendingUp, MapPin, Users, Target, DollarSign, Award } from 'lucide-react';
import { api } from '../lib/api';
import { formatAmount, formatNumber } from '../lib/utils';
import { cn } from '../lib/utils';

interface MarketingStats {
  region_distribution: { region: string; count: number; total_amount: number }[];
  competitors: {
    name: string;
    win_count: number;
    total_amount: number;
    avg_amount: number;
    categories: string[];
    recent_projects: string[];
  }[];
  opportunities: {
    category: string;
    count: number;
    total_amount: number;
    avg_amount: number;
    competitor_count: number;
    top_competitors: string[];
  }[];
  monthly_trend: { month: string; count: number; total_amount: number; avg_amount: number }[];
  category_competition: {
    category: string;
    total_competitors: number;
    top_competitors: { name: string; count: number }[];
  }[];
  key_metrics: {
    total_announcements_6m: number;
    with_winner_6m: number;
    total_amount_6m: number;
    avg_amount_6m: number;
    coverage_rate: number;
  };
}

export function Marketing() {
  const { data } = useQuery({
    queryKey: ['marketing'],
    queryFn: () => api.get<MarketingStats>('/marketing'),
  });

  if (!data) return <div className="text-center py-20" style={{ color: 'var(--text-sec)' }}>加载中...</div>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold" style={{ color: 'var(--text)' }}>营销分析</h1>

      <div className="grid grid-cols-4 gap-4">
        <div className="rounded-lg p-5 shadow-sm border" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)' }}>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ backgroundColor: '#1677ff15' }}>
              <FileText className="w-5 h-5" style={{ color: '#1677ff' }} />
            </div>
            <div>
              <div className="text-xs" style={{ color: 'var(--text-sec)' }}>近6月公告</div>
              <div className="text-xl font-bold" style={{ color: 'var(--text)' }}>{formatNumber(data.key_metrics.total_announcements_6m)}</div>
            </div>
          </div>
        </div>
        <div className="rounded-lg p-5 shadow-sm border" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)' }}>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ backgroundColor: '#52c41a15' }}>
              <Award className="w-5 h-5" style={{ color: '#52c41a' }} />
            </div>
            <div>
              <div className="text-xs" style={{ color: 'var(--text-sec)' }}>含中标信息</div>
              <div className="text-xl font-bold" style={{ color: 'var(--text)' }}>{formatNumber(data.key_metrics.with_winner_6m)}</div>
            </div>
          </div>
        </div>
        <div className="rounded-lg p-5 shadow-sm border" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)' }}>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ backgroundColor: '#faad1415' }}>
              <DollarSign className="w-5 h-5" style={{ color: '#faad14' }} />
            </div>
            <div>
              <div className="text-xs" style={{ color: 'var(--text-sec)' }}>近6月总金额</div>
              <div className="text-xl font-bold" style={{ color: 'var(--text)' }}>{formatAmount(data.key_metrics.total_amount_6m)}</div>
            </div>
          </div>
        </div>
        <div className="rounded-lg p-5 shadow-sm border" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)' }}>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ backgroundColor: '#722ed115' }}>
              <Target className="w-5 h-5" style={{ color: '#722ed1' }} />
            </div>
            <div>
              <div className="text-xs" style={{ color: 'var(--text-sec)' }}>信息覆盖率</div>
              <div className="text-xl font-bold" style={{ color: 'var(--text)' }}>{data.key_metrics.coverage_rate}%</div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="rounded-lg p-5 shadow-sm border" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)' }}>
          <h3 className="text-sm font-medium mb-4 flex items-center gap-2" style={{ color: 'var(--text)' }}>
            <TrendingUp className="w-4 h-4" /> 月度趋势（近12月）
          </h3>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={data.monthly_trend}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="month" tick={{ fontSize: 11 }} stroke="var(--text-sec)" />
              <YAxis tick={{ fontSize: 11 }} stroke="var(--text-sec)" />
              <Tooltip />
              <Line type="monotone" dataKey="count" stroke="#1677ff" strokeWidth={2} dot={false} name="公告数" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="rounded-lg p-5 shadow-sm border" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)' }}>
          <h3 className="text-sm font-medium mb-4 flex items-center gap-2" style={{ color: 'var(--text)' }}>
            <MapPin className="w-4 h-4" /> 区域分布
          </h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={data.region_distribution}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="region" tick={{ fontSize: 11 }} stroke="var(--text-sec)" />
              <YAxis tick={{ fontSize: 11 }} stroke="var(--text-sec)" />
              <Tooltip />
              <Bar dataKey="count" fill="#52c41a" radius={[4, 4, 0, 0]} name="数量" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="rounded-lg p-5 shadow-sm border" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)' }}>
        <h3 className="text-sm font-medium mb-4 flex items-center gap-2" style={{ color: 'var(--text)' }}>
          <Users className="w-4 h-4" /> 竞争对手分析
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b" style={{ borderColor: 'var(--border)' }}>
                <th className="text-left px-3 py-2 font-medium" style={{ color: 'var(--text-sec)' }}>排名</th>
                <th className="text-left px-3 py-2 font-medium" style={{ color: 'var(--text-sec)' }}>企业名称</th>
                <th className="text-left px-3 py-2 font-medium" style={{ color: 'var(--text-sec)' }}>中标次数</th>
                <th className="text-left px-3 py-2 font-medium" style={{ color: 'var(--text-sec)' }}>中标总额</th>
                <th className="text-left px-3 py-2 font-medium" style={{ color: 'var(--text-sec)' }}>平均金额</th>
                <th className="text-left px-3 py-2 font-medium" style={{ color: 'var(--text-sec)' }}>涉及领域</th>
              </tr>
            </thead>
            <tbody>
              {data.competitors.map((c, i) => (
                <tr key={c.name} className="border-b last:border-0" style={{ borderColor: 'var(--border)' }}>
                  <td className="px-3 py-2">
                    <span className={cn(
                      'w-5 h-5 rounded-full inline-flex items-center justify-center text-xs font-bold text-white',
                      i < 3 ? 'bg-blue-600' : 'bg-gray-400'
                    )}>{i + 1}</span>
                  </td>
                  <td className="px-3 py-2 font-medium" style={{ color: 'var(--text)' }}>{c.name}</td>
                  <td className="px-3 py-2" style={{ color: 'var(--text-sec)' }}>{c.win_count}次</td>
                  <td className="px-3 py-2 font-medium" style={{ color: 'var(--text)' }}>{formatAmount(c.total_amount)}</td>
                  <td className="px-3 py-2" style={{ color: 'var(--text-sec)' }}>{formatAmount(c.avg_amount)}</td>
                  <td className="px-3 py-2">
                    <div className="flex gap-1 flex-wrap">
                      {c.categories.map((cat) => (
                        <span key={cat} className="px-1.5 py-0.5 rounded text-xs bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400">{cat}</span>
                      ))}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="rounded-lg p-5 shadow-sm border" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)' }}>
          <h3 className="text-sm font-medium mb-4 flex items-center gap-2" style={{ color: 'var(--text)' }}>
            <Target className="w-4 h-4" /> 市场机会分析
          </h3>
          <div className="space-y-3">
            {data.opportunities.map((opp) => (
              <div key={opp.category} className="p-3 rounded border" style={{ borderColor: 'var(--border)' }}>
                <div className="flex items-center justify-between mb-1">
                  <span className="font-medium" style={{ color: 'var(--text)' }}>{opp.category}</span>
                  <span className="text-xs px-2 py-0.5 rounded bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400">
                    {opp.count}个项目
                  </span>
                </div>
                <div className="flex items-center gap-4 text-xs" style={{ color: 'var(--text-sec)' }}>
                  <span>平均金额: {formatAmount(opp.avg_amount)}</span>
                  <span>竞争者: {opp.competitor_count}家</span>
                </div>
                {opp.top_competitors.length > 0 && (
                  <div className="mt-1.5 text-xs" style={{ color: 'var(--text-sec)' }}>
                    主要对手: {opp.top_competitors.join('、')}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-lg p-5 shadow-sm border" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)' }}>
          <h3 className="text-sm font-medium mb-4 flex items-center gap-2" style={{ color: 'var(--text)' }}>
            <Award className="w-4 h-4" /> 各领域竞争格局
          </h3>
          <div className="space-y-4">
            {data.category_competition.map((cc) => (
              <div key={cc.category}>
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-sm" style={{ color: 'var(--text)' }}>{cc.category}</span>
                  <span className="text-xs" style={{ color: 'var(--text-sec)' }}>共 {cc.total_competitors} 家竞争者</span>
                </div>
                <div className="space-y-1.5">
                  {cc.top_competitors.map((tc, i) => (
                    <div key={tc.name} className="flex items-center gap-2">
                      <span className="w-4 text-xs font-bold" style={{ color: i < 3 ? 'var(--primary)' : 'var(--text-sec)' }}>{i + 1}</span>
                      <div className="flex-1 h-5 rounded overflow-hidden" style={{ backgroundColor: 'var(--bg)' }}>
                        <div className="h-full rounded flex items-center px-2 text-xs text-white"
                          style={{
                            width: `${cc.top_competitors[0]?.count ? (tc.count / cc.top_competitors[0].count * 100) : 0}%`,
                            minWidth: '40px',
                            backgroundColor: i === 0 ? '#1677ff' : i === 1 ? '#52c41a' : i === 2 ? '#faad14' : '#8c8c8c'
                          }}>
                          {tc.name} ({tc.count})
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function FileText(props: any) {
  return (
    <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z" /><path d="M14 2v4a2 2 0 0 0 2 2h4" />
    </svg>
  );
}
