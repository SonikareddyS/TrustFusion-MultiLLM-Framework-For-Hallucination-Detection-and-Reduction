import { useEffect, useRef, useState } from 'react'
import axios from 'axios'

const API_BASE = 'http://localhost:8000'

const getAuthHeaders = () => {
  const token = localStorage.getItem('token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export default function useQuery() {
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [elapsedSeconds, setElapsedSeconds] = useState(0)
  const controllerRef = useRef(null)

  useEffect(() => {
    if (!loading) return
    const timer = setInterval(() => setElapsedSeconds(value => value + 1), 1000)
    return () => clearInterval(timer)
  }, [loading])

  useEffect(() => () => controllerRef.current?.abort(), [])

  const submitQuery = async (query, enabledModels) => {
    if (controllerRef.current) return
    if (!enabledModels.length) {
      setError('Select at least one model.')
      return
    }
    const controller = new AbortController()
    controllerRef.current = controller
    setLoading(true)
    setElapsedSeconds(0)
    setError(null)
    setResult(null)

    try {
      const response = await axios.post(
        `${API_BASE}/api/query`,
        {
          query,
          enabled_models: enabledModels,
          use_rag: true,
        },
        { headers: getAuthHeaders(), timeout: 85000, signal: controller.signal }
      )
      setResult(response.data)
    } catch (err) {
      const detail = err.response?.data?.detail
      setError(
        axios.isCancel(err) ? 'Query cancelled.' :
        err.code === 'ECONNABORTED' ? 'Query timed out. A model or evidence source was too slow; please retry.' :
        typeof detail === 'string' ? detail :
        Array.isArray(detail) ? detail.map((issue) => issue.msg || 'Invalid query').join('; ') :
        'Something went wrong. Is the backend running?'
      )
    } finally {
      controllerRef.current = null
      setLoading(false)
    }
  }

  const cancelQuery = () => controllerRef.current?.abort()

  return { result, loading, error, submitQuery, elapsedSeconds, cancelQuery }
}

export { getAuthHeaders, API_BASE }