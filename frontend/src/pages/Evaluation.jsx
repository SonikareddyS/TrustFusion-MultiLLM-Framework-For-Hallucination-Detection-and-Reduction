import { useState, useEffect } from 'react'
import axios from 'axios'
import { getAuthHeaders, API_BASE } from '../hooks/useQuery'

export default function Evaluation({ onBack }) {
  const [metrics, setMetrics] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchMetrics()
  }, [])

  const fetchMetrics = async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/eval/metrics`, {
        headers: getAuthHeaders()
      })
      setMetrics(res.data)
    } catch (err) {
      console.error('Failed to fetch metrics', err)
    } finally {
      setLoading(false)
    }
  }

  const getColor = (value, threshold1 = 70, threshold2 = 40) => {
    if (value >= threshold1) return '#4ade80'
    if (value >= threshold2) return '#fb923c'
    return '#f87171'
  }

  const MODEL_LABELS = {
    'gpt-oss-120b': 'GPT OSS 120B',
    'qwen-3.8-27b': 'Qwen 3.8 27B',
    'llama-3.3-70b': 'LLaMA 3.3 70B',
    'llama-3.1-8b': 'LLaMA 3.1 8B',
    'llama-4-scout': 'LLaMA 4 Scout',
    'gemma-3-27b': 'GPT OSS 20B',
    'mistral-large': 'Mistral Large',
  }

  const MODEL_COLORS = {
    'gpt-oss-120b': '#10a37f',
    'qwen-3.8-27b': '#4285f4',
    'llama-3.3-70b': '#10a37f',
    'llama-3.1-8b': '#cc785c',
    'llama-4-scout': '#4285f4',
    'gemma-3-27b': '#7c3aed',
    'mistral-large': '#ff7000',
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <p className="text-gray-400">Loading metrics...</p>
      </div>
    )
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
          <h1 className="text-xl font-bold text-white">
            Evaluation Metrics
          </h1>
          <p className="text-xs text-gray-500">
            System performance analysis
          </p>
        </div>
      </div>

      <div className="p-6 space-y-6">

        {/* Top stats */}
        <div className="grid grid-cols-5 gap-4">
          <div className="bg-gray-900 rounded-xl p-5 border border-gray-800">
            <p className="text-xs text-gray-500 mb-2">Total Queries</p>
            <p className="text-3xl font-bold text-white">
              {metrics?.total_queries || 0}
            </p>
          </div>
          <div className="bg-gray-900 rounded-xl p-5 border border-gray-800">
            <p className="text-xs text-gray-500 mb-2">Avg Agreement</p>
            <p
              className="text-3xl font-bold"
              style={{ color: getColor(metrics?.avg_agreement || 0) }}
            >
              {metrics?.avg_agreement || 0}%
            </p>
          </div>
          <div className="bg-gray-900 rounded-xl p-5 border border-gray-800">
            <p className="text-xs text-gray-500 mb-2">RAG Trigger Rate</p>
            <p className="text-3xl font-bold text-amber-400">
              {metrics?.rag_trigger_rate || 0}%
            </p>
          </div>
          <div className="bg-gray-900 rounded-xl p-5 border border-gray-800">
            <p className="text-xs text-gray-500 mb-2">Hallucination Rate</p>
            <p className="text-3xl font-bold text-red-400">
              {metrics?.hallucination_rate || 0}%
            </p>
          </div>
          <div className="bg-gray-900 rounded-xl p-5 border border-gray-800">
            <p className="text-xs text-gray-500 mb-2">Avg Latency</p>
            <p className="text-3xl font-bold text-blue-400">
              {Math.round(metrics?.avg_latency_ms || 0)}ms
            </p>
          </div>
        </div>

        {/* Model performance */}
        <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
          <h2 className="text-sm font-bold text-white mb-4">
            Model Trust Score Performance
          </h2>
          <div className="space-y-4">
            {metrics?.model_performance?.length > 0 ? (
              metrics.model_performance.map((model, i) => (
                <div key={i}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm text-gray-300">
                      {MODEL_LABELS[model.model_id] || model.model_id}
                    </span>
                    <div className="flex items-center gap-3">
                      <span className="text-xs text-gray-500">
                        {model.query_count} queries
                      </span>
                      <span
                        className="text-sm font-bold"
                        style={{
                          color: MODEL_COLORS[model.model_id] || '#6b7280'
                        }}
                      >
                        {model.avg_trust}%
                      </span>
                    </div>
                  </div>
                  <div className="w-full bg-gray-800 rounded-full h-2">
                    <div
                      className="h-2 rounded-full transition-all"
                      style={{
                        width: `${model.avg_trust}%`,
                        backgroundColor: MODEL_COLORS[model.model_id] || '#6b7280',
                      }}
                    />
                  </div>
                </div>
              ))
            ) : (
              <p className="text-gray-500 text-sm">
                No data yet. Ask some questions first!
              </p>
            )}
          </div>
        </div>

        {/* Agreement trend */}
        <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
          <h2 className="text-sm font-bold text-white mb-4">
            Recent Query Agreement Trend
          </h2>
          {metrics?.recent_trend?.length > 0 ? (
            <div className="flex items-end gap-2 h-32">
              {metrics.recent_trend.map((item, i) => (
                <div key={i} className="flex-1 flex flex-col items-center gap-1">
                  <span className="text-xs text-gray-500">
                    {item.agreement}%
                  </span>
                  <div
                    className="w-full rounded-t"
                    style={{
                      height: `${item.agreement}%`,
                      backgroundColor: getColor(item.agreement),
                      minHeight: '4px',
                    }}
                  />
                  <span className="text-xs text-gray-600">{item.date}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-sm">No trend data yet.</p>
          )}
        </div>

        {/* Hallucination breakdown */}
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
            <h2 className="text-sm font-bold text-white mb-4">
              RAG System Performance
            </h2>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-400">Queries with RAG</span>
                <span className="text-xs font-bold text-amber-400">
                  {metrics?.rag_trigger_rate}%
                </span>
              </div>
              <div className="w-full bg-gray-800 rounded-full h-2">
                <div
                  className="h-2 rounded-full bg-amber-500"
                  style={{ width: `${metrics?.rag_trigger_rate}%` }}
                />
              </div>
              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-400">
                  Queries without RAG
                </span>
                <span className="text-xs font-bold text-green-400">
                  {100 - (metrics?.rag_trigger_rate || 0)}%
                </span>
              </div>
              <div className="w-full bg-gray-800 rounded-full h-2">
                <div
                  className="h-2 rounded-full bg-green-500"
                  style={{
                    width: `${100 - (metrics?.rag_trigger_rate || 0)}%`
                  }}
                />
              </div>
            </div>
          </div>

          <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
            <h2 className="text-sm font-bold text-white mb-4">
              Hallucination Detection Rate
            </h2>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-400">
                  Queries with hallucinations
                </span>
                <span className="text-xs font-bold text-red-400">
                  {metrics?.hallucination_rate}%
                </span>
              </div>
              <div className="w-full bg-gray-800 rounded-full h-2">
                <div
                  className="h-2 rounded-full bg-red-500"
                  style={{ width: `${metrics?.hallucination_rate}%` }}
                />
              </div>
              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-400">
                  Clean responses
                </span>
                <span className="text-xs font-bold text-green-400">
                  {100 - (metrics?.hallucination_rate || 0)}%
                </span>
              </div>
              <div className="w-full bg-gray-800 rounded-full h-2">
                <div
                  className="h-2 rounded-full bg-green-500"
                  style={{
                    width: `${100 - (metrics?.hallucination_rate || 0)}%`
                  }}
                />
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  )
}