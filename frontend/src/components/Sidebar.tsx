import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  FileText,
  Download,
  Bug,
  Clock,
  Moon,
  Sun,
  LogOut,
  BarChart3,
  Database,
  Bell,
} from 'lucide-react';
import { useAuth, useTheme } from '../lib/auth';
import { cn } from '../lib/utils';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: '仪表盘' },
  { to: '/announcements', icon: FileText, label: '公告列表' },
  { to: '/marketing', icon: BarChart3, label: '营销分析' },
  { to: '/crawler', icon: Bug, label: '采集管理' },
  { to: '/export', icon: Download, label: '数据导出' },
  { to: '/schedules', icon: Clock, label: '定时调度' },
  { to: '/notifications', icon: Bell, label: '通知推送' },
];

export function Sidebar() {
  const { username, isAdmin, logout } = useAuth();
  const { dark, toggle } = useTheme();
  const location = useLocation();

  return (
    <aside className="fixed left-0 top-0 bottom-0 w-56 flex flex-col" style={{ backgroundColor: 'var(--sidebar-bg)' }}>
      <div className="h-14 flex items-center px-5 border-b border-white/10">
        <Database className="w-6 h-6 text-blue-400 mr-2" />
        <span className="text-white font-semibold text-base">数据采集系统</span>
      </div>

      <nav className="flex-1 py-3 overflow-y-auto">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={cn(
              'flex items-center gap-3 px-5 py-2.5 text-sm transition-colors',
              location.pathname === item.to
                ? 'text-white bg-white/15 border-r-2 border-blue-400'
                : 'text-gray-400 hover:text-white hover:bg-white/5'
            )}
          >
            <item.icon className="w-4 h-4" />
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-white/10 p-4">
        <div className="flex items-center justify-between mb-3">
          <span className="text-gray-400 text-xs">
            {username}
            {isAdmin && <span className="ml-1 text-yellow-400">[管理员]</span>}
          </span>
        </div>
        <div className="flex gap-2">
          <button
            onClick={toggle}
            className="flex-1 flex items-center justify-center gap-1.5 px-2 py-1.5 text-xs text-gray-400 hover:text-white rounded transition-colors"
          >
            {dark ? <Sun className="w-3.5 h-3.5" /> : <Moon className="w-3.5 h-3.5" />}
            {dark ? '亮色' : '暗色'}
          </button>
          <button
            onClick={logout}
            className="flex-1 flex items-center justify-center gap-1.5 px-2 py-1.5 text-xs text-gray-400 hover:text-red-400 rounded transition-colors"
          >
            <LogOut className="w-3.5 h-3.5" />
            退出
          </button>
        </div>
      </div>
    </aside>
  );
}
