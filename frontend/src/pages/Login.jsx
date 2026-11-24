import { useState } from 'react'
import axios from 'axios'

const API_BASE = 'http://localhost:8000'

export default function Login({ onLogin, switchToRegister }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleLogin = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await axios.post(`${API_BASE}/api/auth/login`, { email, password }, { timeout: 10000 })
      localStorage.setItem('token', res.data.token)
      localStorage.setItem('user', JSON.stringify(res.data.user))
      onLogin(res.data.user)
    } catch (err) {
      const detail = err.response?.data?.detail
      setError(typeof detail === 'string' ? detail :
        Array.isArray(detail) ? detail.map(issue => issue.msg || 'Invalid login details').join('; ') :
        err.code === 'ECONNABORTED' ? 'Login timed out. Check that the backend and MongoDB are running.' :
        'Cannot reach the server. Check that the backend is running.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center">
      <div className="bg-gray-900 rounded-2xl p-8 w-full max-w-md border border-gray-800">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-white mb-2">
            Trust-Aware Multi-LLM
          </h1>
          <p className="text-gray-400 text-sm">Sign in to your account</p>
        </div>

        {/* Error */}
        {error && (
          <div className="mb-4 p-3 bg-red-950 border border-red-800 rounded-lg text-red-300 text-sm">
            {error}
          </div>
        )}

        {/* Form */}
        <div className="space-y-4">
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Email</label>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="w-full bg-gray-800 text-white rounded-xl px-4 py-3 
                         border border-gray-700 focus:outline-none focus:border-blue-500 text-sm"
            />
          </div>
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Password</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleLogin()}
              placeholder="••••••••"
              className="w-full bg-gray-800 text-white rounded-xl px-4 py-3 
                         border border-gray-700 focus:outline-none focus:border-blue-500 text-sm"
            />
          </div>
          <button
            onClick={handleLogin}
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-900 
                       text-white py-3 rounded-xl font-semibold transition-colors"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </div>

        {/* Switch */}
        <p className="text-center text-gray-400 text-sm mt-6">
          Don't have an account?{' '}
          <button
            onClick={switchToRegister}
            className="text-blue-400 hover:text-blue-300"
          >
            Register
          </button>
        </p>
      </div>
    </div>
  )
}