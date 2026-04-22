import { useState } from 'react';
import { useAuth } from '../lib/auth';
import { Trophy } from 'lucide-react';

export function Login() {
  const { login } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(username, password);
    } catch (err: any) {
      setError(err.message || '登录失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: 'var(--bg)' }}>
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-blue-600 mb-4">
            <Trophy className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold" style={{ color: 'var(--text)' }}>中标结果公示系统</h1>
          <p className="text-sm mt-1" style={{ color: 'var(--text-sec)' }}>请登录以继续</p>
        </div>

        <form onSubmit={handleSubmit} className="rounded-xl p-6 shadow-sm border space-y-4" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)' }}>
          {error && (
            <div className="p-3 rounded text-sm text-red-600 bg-red-50 dark:text-red-400 dark:bg-red-900/30">{error}</div>
          )}
          <div>
            <label className="text-xs block mb-1.5 font-medium" style={{ color: 'var(--text-sec)' }}>用户名</label>
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-3 py-2.5 rounded-lg border text-sm outline-none focus:ring-2 focus:ring-blue-400"
              style={{ backgroundColor: 'var(--bg)', borderColor: 'var(--border)', color: 'var(--text)' }}
              placeholder="请输入用户名"
              required
            />
          </div>
          <div>
            <label className="text-xs block mb-1.5 font-medium" style={{ color: 'var(--text-sec)' }}>密码</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2.5 rounded-lg border text-sm outline-none focus:ring-2 focus:ring-blue-400"
              style={{ backgroundColor: 'var(--bg)', borderColor: 'var(--border)', color: 'var(--text)' }}
              placeholder="请输入密码"
              required
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 rounded-lg text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {loading ? '登录中...' : '登录'}
          </button>
          <p className="text-xs text-center" style={{ color: 'var(--text-sec)' }}>
            默认账号: admin / admin
          </p>
        </form>
      </div>
    </div>
  );
}
