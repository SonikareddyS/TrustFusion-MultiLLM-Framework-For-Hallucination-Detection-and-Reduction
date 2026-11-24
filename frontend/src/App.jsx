import { useState, useEffect } from 'react'
import Dashboard from './pages/Dashboard'
import Login from './pages/Login'
import Register from './pages/Register'
import History from './pages/History'
import Evaluation from './pages/Evaluation'

export default function App() {
  const [user, setUser] = useState(null)
  const [page, setPage] = useState('login')

  useEffect(() => {
    const savedUser = localStorage.getItem('user')
    const token = localStorage.getItem('token')
    if (savedUser && token) {
      setUser(JSON.parse(savedUser))
      setPage('dashboard')
    }
  }, [])

  const handleLogin = (userData) => {
    setUser(userData)
    setPage('dashboard')
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setUser(null)
    setPage('login')
  }

  if (!user) {
    if (page === 'login') {
      return (
        <Login
          onLogin={handleLogin}
          switchToRegister={() => setPage('register')}
        />
      )
    }
    return (
      <Register
        onLogin={handleLogin}
        switchToLogin={() => setPage('login')}
      />
    )
  }

  if (page === 'history') {
    return <History onBack={() => setPage('dashboard')} />
  }

  if (page === 'evaluation') {
    return <Evaluation onBack={() => setPage('dashboard')} />
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <Dashboard
        user={user}
        onLogout={handleLogout}
        onShowHistory={() => setPage('history')}
        onShowEvaluation={() => setPage('evaluation')}
      />
    </div>
  )
}