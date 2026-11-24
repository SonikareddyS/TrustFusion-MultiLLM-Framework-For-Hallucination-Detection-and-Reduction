from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class HallucinationLabel(str, Enum):
    reliable = "reliable"
    suspicious = "suspicious"
    hallucinated = "hallucinated"


class ModelResponse(BaseModel):
    model_id: str
    display_name: str
    raw_text: str
    normalized_text: str
    latency_ms: float
    error: Optional[str] = None


class ComparisonResult(BaseModel):
    contradictions: list[str]
    agreement_score: float
    missing_info_flags: list[str]
    vagueness_flags: list[str]
    consensus_scores: dict[str, float] = Field(default_factory=dict)
    similarity_scores: dict[str, float] = Field(default_factory=dict)


class EvidenceSource(BaseModel):
    title: str
    url: str
    provider: str
    text: str = Field(default="", exclude=True)


class ClaimVerification(BaseModel):
    claim: str
    status: str
    source_url: str | None = None
    evidence: str = ""
    confidence: float = 0.0


class VerificationResult(BaseModel):
    score: float = 0.0
    claims: list[ClaimVerification] = Field(default_factory=list)

    @property
    def supported(self) -> int:
        return sum(claim.status == "SUPPORTED" for claim in self.claims)

    @property
    def contradicted(self) -> int:
        return sum(claim.status == "CONTRADICTED" for claim in self.claims)


class HallucinationResult(BaseModel):
    model_id: str
    label: HallucinationLabel
    confidence: float
    reasons: list[str]


class TrustScore(BaseModel):
    model_id: str
    score: float
    agreement_component: float
    rag_component: float
    completeness_component: float
    consensus_component: float = 0.0
    similarity_component: float = 0.0
    supported_claims: int = 0
    contradicted_claims: int = 0
    unverified_claims: int = 0
    claims: list[ClaimVerification] = Field(default_factory=list)
    factual_override: bool = False


class FinalAnswer(BaseModel):
    text: str
    source_model_id: str
    corrections_applied: list[str]


class Explanation(BaseModel):
    verdict: str
    model_disagreements: list[str]
    rag_sources_used: list[EvidenceSource | str]
    hallucination_notes: list[str]
    retrieval_warnings: list[str] = Field(default_factory=list)


class QueryResponse(BaseModel):
    query: str
    session_id: Optional[str]
    model_responses: list[ModelResponse]
    comparison: ComparisonResult
    hallucination_results: list[HallucinationResult]
    trust_scores: list[TrustScore]
    final_answer: FinalAnswer
    explanation: Explanation
    total_latency_ms: float
