import Markdown from "./Markdown";

const LABEL_STYLES = {
  reliable: { bg: "#052e16", text: "#4ade80", border: "#166534" },
  suspicious: { bg: "#451a03", text: "#fbbf24", border: "#92400e" },
  hallucinated: { bg: "#450a0a", text: "#f87171", border: "#991b1b" },
};

export default function ModelColumn({ response, trust, hallucination }) {
  const percent = trust ? (trust.score * 100).toFixed(2) : "0.00";
  const label = response.error || trust?.contradicted_claims > 0 || (trust?.score ?? 0) < 0.5
    ? "hallucinated" : trust.score >= 0.8 ? "reliable" : "suspicious";
  const style = LABEL_STYLES[label];
  const trustColor = style.text;
  const breakdown = trust ? [
    ["Consensus", trust.consensus_component ?? trust.agreement_component],
    ["RAG Verification", trust.rag_component],
    ["Similarity", trust.similarity_component ?? 0],
    ["Verified Claim Coverage", trust.completeness_component],
  ] : [];

  return (
    <div
      className="bg-gray-900 rounded-lg border overflow-hidden flex flex-col min-w-0"
      style={{
        borderColor: style.border,
        borderTopColor: trustColor,
        borderTopWidth: "3px",
        minHeight: "420px",
      }}
    >
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-800 flex flex-wrap gap-2 items-center justify-between">
        <div className="flex items-center gap-2">
          <span
            className="w-2.5 h-2.5 rounded-full"
            style={{ backgroundColor: trustColor }}
          />
          <span className="font-semibold text-sm text-white">
            {response.display_name}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span
            className="text-xs font-bold px-2 py-0.5 rounded-full border"
            style={{
              color: trustColor,
              borderColor: trustColor + "44",
              backgroundColor: trustColor + "11",
            }}
          >
            {percent}%
          </span>
          <span
            className="text-xs font-medium px-2 py-0.5 rounded-full border"
            style={{
              color: style.text,
              borderColor: style.border,
              backgroundColor: style.bg,
            }}
          >
            {{ reliable: "Reliable / Correct", suspicious: "Suspicious / Doubtful", hallucinated: "Hallucinated / Incorrect" }[label]}
          </span>
        </div>
      </div>

      {/* Latency */}
      <div className="px-4 py-1.5 bg-gray-950 border-b border-gray-800">
        <span className="text-xs text-gray-500">
          ⚡ {Math.round(response.latency_ms)}ms
        </span>
      </div>

      {/* Response */}
      <div
        className="px-4 py-4 flex-1 overflow-y-auto"
        style={{ maxHeight: "380px" }}
      >
        {response.error ? (
          <div className="text-red-400 text-xs bg-red-950 rounded-lg p-3 border border-red-900">
            ⚠ {response.error}
          </div>
        ) : (
          <Markdown>{response.raw_text || response.normalized_text || "No response"}</Markdown>
        )}
      </div>

      {/* Trust breakdown */}
      {trust && (
        <div className="px-4 py-3 border-t border-gray-800 bg-gray-950">
          {breakdown.map(([name, value]) => (
            <div key={name} className="mb-2">
              <div className="flex justify-between gap-2 text-xs text-gray-400 mb-1">
                <span>{name}</span><span>{((value ?? 0) * 100).toFixed(2)}%</span>
              </div>
              <div className="w-full bg-gray-800 rounded-full h-1">
                <div className="h-1 rounded-full" style={{ width: `${(value ?? 0) * 100}%`, backgroundColor: trustColor }} />
              </div>
            </div>
          ))}
          <p className="text-xs text-gray-300">Verified: {trust.supported_claims ?? 0} / Contradicted: {trust.contradicted_claims ?? 0} / Unverified: {trust.unverified_claims ?? 0}</p>
          {trust.factual_override && <p className="text-xs text-red-300 mt-2">Factual safety cap applied</p>}
          <details className="text-xs text-gray-400 mt-3">
            <summary className="cursor-pointer">Claim evidence</summary>
            {trust.claims?.map((claim, index) => (
              <div key={index} className="mt-3">
                <p>{claim.status}: {claim.claim}</p>
                {claim.source_url && <a className="text-sky-300 underline" href={claim.source_url} target="_blank" rel="noopener noreferrer">Evidence source</a>}
                {claim.evidence && <blockquote className="mt-1 border-l border-gray-600 pl-2">{claim.evidence}</blockquote>}
              </div>
            ))}
          </details>
          {hallucination?.reasons?.map((reason) => <p key={reason} className="text-xs text-gray-500 mt-2">{reason}</p>)}
        </div>
      )}
    </div>
  );
}
