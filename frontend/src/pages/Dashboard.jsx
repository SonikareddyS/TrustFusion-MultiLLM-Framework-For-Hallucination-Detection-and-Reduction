import { useState } from "react";
import ModelColumn from "../components/ModelColumn";
import FinalAnswer from "../components/FinalAnswer";
import useQuery from "../hooks/useQuery";

const ALL_MODELS = [
  { id: "gpt-oss-120b", label: "GPT OSS 120B", color: "#10a37f" },
  { id: "qwen-3.8-27b", label: "Qwen 3.8 27B", color: "#4285f4" },
  { id: "gemma-3-27b", label: "GPT OSS 20B", color: "#7c3aed" },
  { id: "mistral-large", label: "Mistral Large (credits required)", color: "#ff7000", unavailable: true },
];

export default function Dashboard({
  user,
  onLogout,
  onShowHistory,
  onShowEvaluation,
}) {
  const [query, setQuery] = useState("");
  const [enabledModels, setEnabledModels] = useState(
    ALL_MODELS.filter((model) => !model.unavailable).map((model) => model.id),
  );
  const { result, loading, error, submitQuery, elapsedSeconds, cancelQuery } = useQuery();

  const handleSubmit = () => {
    if (!query.trim() || loading) return;
    submitQuery(query, enabledModels);
  };

  const toggleModel = (modelId) => {
    setEnabledModels((prev) =>
      prev.includes(modelId)
        ? prev.filter((id) => id !== modelId)
        : [...prev, modelId],
    );
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <div className="border-b border-gray-800 px-6 py-4 flex flex-wrap gap-4 items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">
            Trust-Aware Multi-LLM System
          </h1>
          <p className="text-xs text-gray-500">
            Hallucination Detection & Response Verification
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-4 min-w-0">
          {/* Model toggles */}
          <div className="flex flex-wrap items-center gap-2">
            {ALL_MODELS.map((model) => (
              <button
                key={model.id}
                onClick={() => toggleModel(model.id)}
                disabled={model.unavailable || loading}
                title={model.unavailable ? "OpenRouter returned insufficient credits. Add credits before enabling this model." : model.label}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all border disabled:cursor-not-allowed"
                style={{
                  backgroundColor: enabledModels.includes(model.id)
                    ? model.color + "22"
                    : "transparent",
                  borderColor: enabledModels.includes(model.id)
                    ? model.color
                    : "#374151",
                  color: enabledModels.includes(model.id)
                    ? model.color
                    : "#6b7280",
                }}
              >
                <span
                  className="w-2 h-2 rounded-full"
                  style={{
                    backgroundColor: enabledModels.includes(model.id)
                      ? model.color
                      : "#6b7280",
                  }}
                />
                {model.label}
              </button>
            ))}
          </div>

          {/* History button */}
          <button
            onClick={onShowHistory}
            className="text-xs bg-gray-800 hover:bg-gray-700 text-gray-300 px-3 py-1.5 rounded-lg transition-colors border border-gray-700"
          >
            📋 History
          </button>
          {/* Evaluation button */}
          <button
            onClick={onShowEvaluation}
            className="text-xs bg-gray-800 hover:bg-gray-700 text-gray-300 px-3 py-1.5 rounded-lg transition-colors border border-gray-700"
          >
            📊 Metrics
          </button>

          {/* User info + Logout */}
          <div className="flex items-center gap-3 border-l border-gray-700 pl-4">
            <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-sm font-bold">
              {user?.username?.charAt(0).toUpperCase()}
            </div>
            <div className="text-right">
              <p className="text-xs text-white font-medium">{user?.username}</p>
              <p className="text-xs text-gray-500">{user?.email}</p>
            </div>
            <button
              onClick={onLogout}
              className="text-xs bg-red-900 hover:bg-red-800 text-red-300 px-3 py-1.5 rounded-lg transition-colors"
            >
              Logout
            </button>
          </div>
        </div>
      </div>

      {/* Query Input */}
      <div className="px-6 py-4 border-b border-gray-800">
        <div className="flex flex-wrap gap-3 max-w-4xl mx-auto">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
            placeholder="Ask anything to compare across models..."
            className="flex-1 basis-48 min-w-0 bg-gray-900 text-white rounded-xl px-5 py-3 border border-gray-700 focus:outline-none focus:border-blue-500 text-sm"
          />
          <button
            onClick={handleSubmit}
            disabled={loading || !enabledModels.length}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-900 text-white px-8 py-3 rounded-xl font-semibold transition-colors text-sm"
          >
            {loading ? `Running (${elapsedSeconds}s)` : "→ Ask"}
          </button>
          {loading && (
            <button onClick={cancelQuery} className="border border-gray-600 rounded-lg px-4 py-3 text-sm text-gray-300 hover:bg-gray-800">
              Cancel
            </button>
          )}
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="mx-6 mt-4 p-4 bg-red-900 border border-red-700 rounded-xl text-red-200 text-sm">
          {error}
        </div>
      )}

      {/* Model Columns */}
      <div className="p-4">
        {loading && (
          <div
            className="grid gap-3"
            style={{
                gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 260px), 1fr))",
            }}
          >
            {enabledModels.map((id) => (
              <div
                key={id}
                className="bg-gray-900 rounded-xl p-4 animate-pulse h-64 border border-gray-800"
              >
                <p className="text-sm font-medium text-gray-300">{ALL_MODELS.find(model => model.id === id)?.label}</p>
                <p className="text-xs text-gray-500 mt-2">Awaiting result</p>
              </div>
            ))}
          </div>
        )}

        {result && (
          <>
            <div
              className="grid gap-3 mb-4"
              style={{
                  gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 260px), 1fr))",
              }}
            >
              {result.model_responses.map((response) => {
                const trust = result.trust_scores.find(
                  (t) => t.model_id === response.model_id,
                );
                const hallucination = result.hallucination_results.find(
                  (h) => h.model_id === response.model_id,
                );
                const model = ALL_MODELS.find(
                  (m) => m.id === response.model_id,
                );
                return (
                  <ModelColumn
                    key={response.model_id}
                    response={response}
                    trust={trust}
                    hallucination={hallucination}
                    color={model?.color || "#6b7280"}
                    query={query}
                  />
                );
              })}
            </div>
            <FinalAnswer
              finalAnswer={result.final_answer}
              explanation={result.explanation}
              comparison={result.comparison}
            />
          </>
        )}
      </div>
    </div>
  );
}
