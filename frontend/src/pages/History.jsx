import { useState, useEffect } from 'react'
import axios from 'axios'
import { getAuthHeaders, API_BASE } from '../hooks/useQuery'

export default function History({ onBack }) {
  const [history, setHistory] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchHistory()
    fetchStats()
  }, [])

  const fetchHistory = async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/history`, {
        headers: getAuthHeaders()
      })
      setHistory(res.data)
    } catch (err) {
      console.error('Failed to fetch history', err)
    } finally {
      setLoading(false)
    }
  }

  const fetchStats = async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/stats`, {
        headers: getAuthHeaders()
      })
      setStats(res.data)
    } catch (err) {
      console.error('Failed to fetch stats', err)
    }
  }

  const formatDate = (dateStr) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const getAgreementColor = (score) => {
    if (score >= 0.7) return '#4ade80'
    if (score >= 0.4) return '#fb923c'
    return '#f87171'
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <div className="border-b border-gray-800 px-6 py-4 flex items-center gap-4">
        <button
          onClick={onBack}
          className="text-gray-400 hover:text-white text-sm flex items-center gap-2"
        >
          ← Back
        </button>
        <div>
          <h1 className="text-xl font-bold text-white">Query History</h1>
          <p className="text-xs text-gray-500">Your past queries and results</p>
        </div>
      </div>

      <div className="p-6">
        {/* Stats cards */}
        {stats && (
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="bg-gray-900 rounded-xl p-5 border border-gray-800">
              <p className="text-xs text-gray-500 mb-1">Total Queries</p>
              <p className="text-3xl font-bold text-white">{stats.total_queries}</p>
            </div>
            <div className="bg-gray-900 rounded-xl p-5 border border-gray-800">
              <p className="text-xs text-gray-500 mb-1">RAG Triggered</p>
              <p className="text-3xl font-bold text-amber-400">
                {stats.rag_triggered_count}
              </p>
            </div>
            <div className="bg-gray-900 rounded-xl p-5 border border-gray-800">
              <p className="text-xs text-gray-500 mb-1">Hallucinations Detected</p>
              <p className="text-3xl font-bold text-red-400">
                {stats.hallucination_detected_count}
              </p>
            </div>
          </div>
        )}

        {/* History list */}
        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="bg-gray-900 rounded-xl p-4 animate-pulse h-24" />
            ))}
          </div>
        ) : history.length === 0 ? (
          <div className="text-center py-20 text-gray-500">
            <p className="text-4xl mb-4">🔍</p>
            <p>No queries yet. Go ask something!</p>
          </div>
        ) : (
          <div className="space-y-3">
            {history.map((item, i) => (
              <div
                key={i}
                className="bg-gray-900 rounded-xl p-5 border border-gray-800 hover:border-gray-600 transition-colors"
              >
                <div className="flex items-start justify-between mb-3">
                  <p className="text-white font-medium text-sm flex-1 mr-4">
                    {item.query}
                  </p>
                  <span className="text-xs text-gray-500 whitespace-nowrap">
                    {formatDate(item.created_at)}
                  </span>
                </div>

                {/* Answer preview */}
                <p className="text-gray-400 text-xs mb-3 line-clamp-2">
                  {item.final_answer}
                </p>

                {/* Stats row */}
                <div className="flex items-center gap-4">
                  {/* Agreement */}
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-500">Agreement</span>
                    <span
                      className="text-xs font-bold"
                      style={{ color: getAgreementColor(item.agreement_score) }}
                    >
                      {Math.round(item.agreement_score * 100)}%
                    </span>
                  </div>

                  {/* Source model */}
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-500">Best model</span>
                    <span className="text-xs text-blue-400">{item.source_model}</span>
                  </div>

                  {/* RAG badge */}
                  {item.rag_triggered && (
                    <span className="text-xs bg-amber-900 text-amber-300 px-2 py-0.5 rounded-full border border-amber-700">
                      ⚡ RAG
                    </span>
                  )}

                  {/* Hallucination badge */}
                  {item.hallucination_count > 0 && (
                    <span className="text-xs bg-red-900 text-red-300 px-2 py-0.5 rounded-full border border-red-700">
                      ⚠ {item.hallucination_count} hallucination(s)
                    </span>
                  )}

                  {/* Latency */}
                  <span className="text-xs text-gray-600 ml-auto">
                    ⚡ {Math.round(item.total_latency_ms)}ms
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}