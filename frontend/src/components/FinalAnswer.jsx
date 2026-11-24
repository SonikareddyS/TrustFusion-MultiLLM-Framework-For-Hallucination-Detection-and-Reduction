import Markdown from "./Markdown";

export default function FinalAnswer({ finalAnswer, explanation, comparison }) {
  const agreement = Math.round(comparison.agreement_score * 100);
  const ragTriggered = explanation.rag_sources_used?.length > 0;

  const agreementColor =
    agreement >= 80 ? "#4ade80" : agreement >= 50 ? "#fbbf24" : "#f87171";

  return (
    <div className="bg-gray-900 rounded-xl border border-blue-900 overflow-hidden">
      {/* Header */}
      <div className="px-5 py-3 border-b border-gray-800 flex flex-wrap gap-3 items-center justify-between bg-blue-950">
        <div className="flex flex-wrap items-center gap-3">
          <span className="text-blue-400 font-bold text-sm">
            ✓ Final Answer
          </span>
          <span className="text-xs text-gray-500">
            Verified synthesis
          </span>
          {ragTriggered && (
            <span className="text-xs bg-amber-900 text-amber-300 px-2 py-0.5 rounded-full border border-amber-700">
              ⚡ RAG Active
            </span>
          )}
          <span className="text-xs bg-blue-900 text-blue-300 px-2 py-0.5 rounded-full border border-blue-700">
            🗳 Consensus Active
          </span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-gray-400">Agreement</span>
          <div className="flex items-center gap-2">
            <div className="w-24 bg-gray-800 rounded-full h-1.5">
              <div
                className="h-1.5 rounded-full"
                style={{
                  width: `${agreement}%`,
                  backgroundColor: agreementColor,
                }}
              />
            </div>
            <span
              className="text-xs font-bold"
              style={{ color: agreementColor }}
            >
              {agreement}%
            </span>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-5 grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div className="lg:col-span-2 space-y-3 min-w-0">
          {/* Final Answer Text */}
          <Markdown>{finalAnswer.text}</Markdown>

          {/* Consensus Voting Panel */}
          {finalAnswer.corrections_applied?.length > 0 && (
            <section className="border-t border-red-900 pt-3">
              <h3 className="text-xs font-semibold text-red-300 mb-2">Contradicted claims excluded</h3>
              {finalAnswer.corrections_applied.map((claim, index) => (
                <p key={index} className="text-xs text-gray-400 mb-1">{claim}</p>
              ))}
            </section>
          )}

          {/* RAG Sources */}
          {ragTriggered && (
            <div className="bg-amber-950 rounded-lg p-3 border border-amber-800">
              <p className="text-xs text-amber-400 font-medium mb-2">
                📖 RAG Sources Used
              </p>
              {explanation.rag_sources_used.map((source, i) => (
                <p key={i} className="text-xs text-amber-200 mb-1 break-words">
                  {typeof source === "string" ? source : (
                    <a href={/^https?:\/\//i.test(source.url) ? source.url : undefined}
                      target="_blank" rel="noopener noreferrer" className="underline">
                      {source.title} ({source.provider})
                    </a>
                  )}
                </p>
              ))}
            </div>
          )}

          {explanation.retrieval_warnings?.map((warning) => (
            <p key={warning} className="text-xs text-amber-300 border-l-2 border-amber-600 pl-3">{warning}</p>
          ))}

          {/* Hallucination Details */}
          {explanation.hallucination_notes?.length > 0 && (
            <div className="bg-red-950 rounded-lg p-3 border border-red-800">
              <p className="text-xs text-red-400 font-medium mb-2">
                ⚠ Hallucination Details
              </p>
              {explanation.hallucination_notes.map((note, i) => (
                <p key={i} className="text-xs text-red-200 mb-1">
                  • {note}
                </p>
              ))}
            </div>
          )}
        </div>

        {/* Verdict Panel */}
        <div className="space-y-3">
          <div className="bg-gray-950 rounded-lg p-4 border border-gray-800">
            <p className="text-xs text-gray-500 font-medium mb-2 uppercase tracking-wider">
              Verdict
            </p>
            <p className="text-gray-300 text-xs leading-relaxed">
              {explanation.verdict}
            </p>
          </div>

          {/* Agreement Meter */}
          <div className="bg-gray-950 rounded-lg p-4 border border-gray-800">
            <p className="text-xs text-gray-500 font-medium mb-3 uppercase tracking-wider">
              Model Agreement
            </p>
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-gray-400">Consensus</span>
              <span
                className="text-xs font-bold"
                style={{ color: agreementColor }}
              >
                {agreement}%
              </span>
            </div>
            <div className="w-full bg-gray-800 rounded-full h-2">
              <div
                className="h-2 rounded-full"
                style={{
                  width: `${agreement}%`,
                  backgroundColor: agreementColor,
                }}
              />
            </div>
            <div className="flex justify-between mt-2">
              <span className="text-xs text-red-400">Conflict</span>
              <span className="text-xs text-green-400">Consensus</span>
            </div>
          </div>

          {/* Contradictions */}
          {explanation.model_disagreements?.length > 0 && (
            <div className="bg-orange-950 rounded-lg p-3 border border-orange-800">
              <p className="text-xs text-orange-400 font-medium mb-2 uppercase tracking-wider">
                Contradictions
              </p>
              {explanation.model_disagreements.map((d, i) => (
                <p key={i} className="text-xs text-orange-300 mb-1">
                  ⚡ {d}
                </p>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
