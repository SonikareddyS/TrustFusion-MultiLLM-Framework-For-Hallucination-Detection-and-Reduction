import sys
import unittest
import asyncio
import json
import os
from pathlib import Path
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from models.response import (
    ClaimVerification, ComparisonResult, ModelResponse, VerificationResult,
)
from core.trust.scorer import compute_trust_scores
from core.comparison.engine import run_comparison
from core.rag.dynamic import extract_topics, fetch_dynamic_sources
from core.rag.retriever import retrieve_evidence
from core.rag.validator import verify_responses, extract_claims
from core.synthesis.generator import synthesize_verified_answer
from models.response import EvidenceSource


def evaluate(query, texts, sources):
    responses = [ModelResponse(model_id=f"model-{index}", display_name=f"Model {index}",
                               raw_text=text, normalized_text=text, latency_ms=0)
                 for index, text in enumerate(texts)]
    chunks = retrieve_evidence(query, sources)
    comparison, _ = run_comparison(responses, query, len(responses))
    verifications = verify_responses(responses, chunks, query)
    scores = compute_trust_scores(responses, [], comparison, verifications=verifications)
    final = synthesize_verified_answer(verifications, len(responses))
    print(json.dumps({"query": query, "sources": list({chunk.source.url for chunk in chunks}),
                      "scores": [{"model": score.model_id, "trust": round(score.score, 4),
                                  "consensus": round(score.consensus_component, 4),
                                  "verification": round(score.rag_component, 4),
                                  "similarity": round(score.similarity_component, 4),
                                  "supported": score.supported_claims,
                                  "contradicted": score.contradicted_claims,
                                  "unverified": score.unverified_claims,
                                  "label": "RED" if score.score < .5 or score.contradicted_claims
                                  else "GREEN" if score.score >= .8 else "AMBER"}
                                 for score in scores], "final_answer": final.text}, indent=2))
    return scores, final, chunks


class TrustFormulaTests(unittest.TestCase):
    def test_initials_and_provider_citations_do_not_fragment_claims(self):
        text = ('The current Chief Minister is D.\u202fK.\u202fShivakumar.'
                '\u3010{"url":"https://example.com/","excerpt":"untrusted citation copy"}\u3011\n'
                'He assumed office in June 2026. https://example.com/profile')
        self.assertEqual(extract_claims(text), [
            "The current Chief Minister is D. K. Shivakumar.",
            "He assumed office in June 2026.",
        ])

    def test_current_officeholder_search_excludes_question_and_formatting(self):
        self.assertEqual(extract_topics(
            "Who is the current chief minister of Karnataka? Answer briefly using current evidence."),
            ["chief minister of Karnataka"])
        self.assertEqual(extract_topics("who is the prime minister of india"),
                         ["prime minister of india"])

    def test_markdown_questions_and_headers_are_not_factual_claims(self):
        claims = extract_claims("## What is Artificial Intelligence?\n\n"
                                "**Medical Diagnostics and Personalized Medicine**\n\n"
                                "| Human Skill | AI Equivalent |\n| --- | --- |\n"
                                "| Understanding language | Natural language processing |\n\n"
                                "Artificial intelligence is used in medical diagnosis.")
        self.assertEqual(len(claims), 2)
        self.assertFalse(any("What is" in claim or "AI Equivalent" in claim for claim in claims))

    def test_exact_formula_and_factual_override(self):
        response = ModelResponse(model_id="test", display_name="test", raw_text="Fact",
                                 normalized_text="Fact", latency_ms=0)
        comparison = ComparisonResult(contradictions=[], agreement_score=1,
                                      missing_info_flags=[], vagueness_flags=[],
                                      consensus_scores={"test": 1}, similarity_scores={"test": 0.9})
        for verified, contradicted, expected in [(1.0, False, 0.98), (0.0, False, 0.49),
                                                (0.9, True, 0.49)]:
            result = VerificationResult(score=verified, claims=[ClaimVerification(
                claim="Fact", status="CONTRADICTED" if contradicted else "SUPPORTED")])
            score = compute_trust_scores([response], [], comparison,
                                         verifications={"test": result})[0]
            self.assertAlmostEqual(score.score, expected)


class EvidenceAccuracyTests(unittest.TestCase):
    def test_claim_guidance_keeps_original_query_filter(self):
        sources = [EvidenceSource(title="AI", provider="wikipedia",
                                  url="https://en.wikipedia.org/wiki/Artificial_intelligence",
                                  text="Artificial intelligence is used in medical diagnosis."),
                   EvidenceSource(title="Quantum mechanics", provider="wikipedia",
                                  url="https://en.wikipedia.org/wiki/Quantum_mechanics",
                                  text="Quantum mechanics describes atoms and subatomic particles.")]
        chunks = retrieve_evidence("What are applications of artificial intelligence?", sources,
                                   claim_queries=["Quantum mechanics describes atoms and subatomic particles."])
        self.assertTrue(chunks)
        self.assertFalse(any("Quantum" in chunk.source.title for chunk in chunks))

    def test_1_factual_ai_query(self):
        query = "Explain Artificial Intelligence and describe three real-world applications."
        text = ("Artificial intelligence is the ability of machines to perform tasks that normally require human intelligence. "
                "Artificial intelligence is used in medical diagnosis. "
                "Artificial intelligence is used in self-driving cars. "
                "Artificial intelligence is used in recommendation systems.")
        sources = [EvidenceSource(title="Artificial intelligence", provider="wikipedia",
                                  url="https://en.wikipedia.org/wiki/Artificial_intelligence", text=text),
                   EvidenceSource(title="What is artificial intelligence?", provider="web",
                                  url="https://www.ibm.com/think/topics/artificial-intelligence", text=text),
                   EvidenceSource(title="Quantum mechanics", provider="wikipedia",
                                  url="https://en.wikipedia.org/wiki/Quantum_mechanics",
                                  text="Quantum mechanics describes physical properties of atoms and subatomic particles.")]
        self.assertEqual(extract_topics(query)[0], "Artificial Intelligence")
        from core.rag import validator
        with patch.object(validator, "predict_nli", wraps=validator.predict_nli) as predict:
            scores, final, chunks = evaluate(query, [text, text, text], sources)
        self.assertEqual(predict.call_count, 1)
        self.assertTrue(chunks)
        self.assertEqual({chunk.source.provider for chunk in chunks}, {"wikipedia", "web"})
        self.assertFalse(any("Quantum" in chunk.source.title for chunk in chunks))
        self.assertTrue(all(score.score >= .8 for score in scores))
        self.assertIn("Source", final.text)

    def test_2_false_date_is_red_and_excluded(self):
        truth = "Apollo 11 landed on the Moon in 1969."
        falsehood = "Apollo 11 landed on the Moon in 1989."
        sources = [EvidenceSource(title="Apollo 11", provider="wikipedia",
                                  url="https://en.wikipedia.org/wiki/Apollo_11", text=truth)]
        scores, final, _ = evaluate("In what year did Apollo 11 land on the Moon?",
                                    [truth, truth, falsehood], sources)
        self.assertTrue(all(score.score >= .8 for score in scores[:2]))
        self.assertLess(scores[2].score, .5)
        self.assertLess(scores[2].rag_component, .35)
        self.assertGreater(scores[2].contradicted_claims, 0)
        self.assertNotIn("1989", final.text)
        self.assertIn("1969", final.text)

    def test_3_vague_answer_not_complete(self):
        truth = "Artificial intelligence is used in medical diagnosis."
        sources = [EvidenceSource(title="Artificial intelligence", provider="wikipedia",
                                  url="https://en.wikipedia.org/wiki/Artificial_intelligence", text=truth)]
        scores, _, _ = evaluate("Describe applications of artificial intelligence.",
                                [truth, truth, "It is useful for many things, perhaps."], sources)
        self.assertLess(scores[2].rag_component, 1)
        self.assertLess(scores[2].completeness_component, 1)
        self.assertLess(scores[2].score, .8)

    def test_no_evidence_is_never_reliable(self):
        scores, final, chunks = evaluate("What is AI?", ["AI can diagnose disease."] * 3, [])
        self.assertFalse(chunks)
        self.assertTrue(all(score.score < .5 and score.rag_component == 0 for score in scores))
        self.assertIn("Insufficient", final.text)

    @unittest.skipUnless(os.environ.get("TRUSTFUSION_LIVE_TEST") == "1", "set TRUSTFUSION_LIVE_TEST=1 for live network gate")
    def test_live_ai_articles(self):
        query = "Explain Artificial Intelligence and describe three real-world applications."
        sources, warnings = asyncio.run(fetch_dynamic_sources(query))
        chunks = retrieve_evidence(query, sources)
        print("LIVE WARNINGS:", warnings)
        print("LIVE SOURCES:", [(chunk.source.title, chunk.source.url) for chunk in chunks])
        self.assertEqual({chunk.source.provider for chunk in chunks}, {"wikipedia", "web"})
        self.assertFalse(any("Quantum mechanics" in chunk.source.title for chunk in chunks))


class ProviderConfigurationTests(unittest.TestCase):
    def test_defaults_use_distinct_available_model_configurations(self):
        from config.model_registry import MODEL_REGISTRY
        from core.llm.executor import _CLIENT_MAP
        from models.request import QueryRequest

        enabled = QueryRequest(query="Test").enabled_models
        self.assertEqual(set(enabled), {"gpt-oss-120b", "qwen-3.8-27b", "gemma-3-27b"})
        provider_models = [_CLIENT_MAP[model_id]._groq_model for model_id in enabled]
        self.assertEqual(len(set(provider_models)), 3)
        for model_id in enabled:
            self.assertEqual(_CLIENT_MAP[model_id].display_name, MODEL_REGISTRY[model_id].display_name)
        self.assertFalse(MODEL_REGISTRY["mistral-large"].enabled_by_default)


class QueryLatencyTests(unittest.IsolatedAsyncioTestCase):
    async def test_slow_web_search_retains_completed_wikipedia(self):
        from core.rag import dynamic

        async def stalled_request(*args, **kwargs):
            await asyncio.Event().wait()

        with patch.object(dynamic, "SOURCE_TIMEOUT_SECONDS", 0.15), \
             patch.object(dynamic, "search_wikipedia", new=AsyncMock(return_value=["Prime Minister of India"])), \
             patch.object(dynamic, "fetch_wikipedia_content", new=AsyncMock(return_value="Narendra Modi is the prime minister of India.")), \
             patch.object(dynamic.httpx, "AsyncClient") as factory:
            factory.return_value.__aenter__.return_value.get = AsyncMock(side_effect=stalled_request)
            sources, warnings = await asyncio.wait_for(dynamic.fetch_dynamic_sources(
                "Who is the prime minister of India?"), timeout=2)
        self.assertEqual(len(sources), 1)
        self.assertEqual(sources[0].provider, "wikipedia")
        self.assertTrue(any("exceeded" in warning for warning in warnings))

    async def test_slow_provider_cannot_block_fast_results(self):
        from core.llm import executor
        from core.llm.base import LLMOutput

        class FastClient:
            model_id = "gpt-oss-120b"

            async def generate(self, prompt, max_tokens):
                return LLMOutput(model_id=self.model_id, text="Fast answer", latency_ms=0)

        class SlowClient:
            model_id = "qwen-3.8-27b"

            async def generate(self, prompt, max_tokens):
                await asyncio.Event().wait()

        with patch.dict(executor._CLIENT_MAP, {FastClient.model_id: FastClient(),
                                               SlowClient.model_id: SlowClient()}), \
             patch.object(executor.settings, "llm_timeout", 0.02):
            outputs = await asyncio.wait_for(executor.execute_parallel(
                "Test", [FastClient.model_id, SlowClient.model_id]), timeout=0.5)
        self.assertEqual(outputs[0].text, "Fast answer")
        self.assertIn("deadline", outputs[1].error)


class AuthenticationTests(unittest.TestCase):
    def test_password_hashing_accepts_long_passwords(self):
        from core.auth.auth_handler import hash_password, verify_password
        password = "long-password-check-" * 10
        hashed = hash_password(password)
        self.assertTrue(verify_password(password, hashed))
        self.assertFalse(verify_password("incorrect", hashed))

    def test_registration_database_failure_is_readable_and_cors_enabled(self):
        from fastapi.testclient import TestClient
        from main import app
        from pymongo.errors import ServerSelectionTimeoutError
        with patch("api.routes.auth.create_user", new=AsyncMock(
                side_effect=ServerSelectionTimeoutError("unavailable"))), TestClient(app) as client:
            response = client.post("/api/auth/register", headers={"Origin": "http://127.0.0.1:5173"},
                                   json={"username": "registration-test", "email": "test@example.com",
                                         "password": "temporary-test-password"})
        self.assertEqual(response.status_code, 503)
        self.assertIn("Database unavailable", response.json()["detail"])
        self.assertEqual(response.headers["access-control-allow-origin"], "http://127.0.0.1:5173")


class PipelineAPITests(unittest.TestCase):
    def test_query_route_has_overall_deadline(self):
        from fastapi.testclient import TestClient
        from main import app

        async def stalled_pipeline(request):
            await asyncio.Event().wait()

        with patch("api.routes.query.run_pipeline", side_effect=stalled_pipeline), \
             patch("api.routes.query.QUERY_TIMEOUT_SECONDS", 0.05), TestClient(app) as client:
            response = client.post("/api/query", json={"query": "Test", "enabled_models": ["test"]},
                                   headers={"Origin": "http://127.0.0.1:5173"})
        self.assertEqual(response.status_code, 504)
        self.assertIn("timed out", response.json()["detail"])
        self.assertEqual(response.headers["access-control-allow-origin"], "http://127.0.0.1:5173")

    def test_query_route_uses_verification_even_when_rag_flag_is_false(self):
        from fastapi.testclient import TestClient
        from main import app
        from core.llm.base import LLMOutput

        truth = "Apollo 11 landed on the Moon in 1969."
        falsehood = "Apollo 11 landed on the Moon in 1989."
        sources = [EvidenceSource(title="Apollo 11", provider="wikipedia",
                                  url="https://en.wikipedia.org/wiki/Apollo_11", text=truth)]
        outputs = [LLMOutput(model_id=f"model-{index}", text=text, latency_ms=0)
                   for index, text in enumerate([truth, truth, falsehood])]

        async def generate_from_evidence(prompt, enabled_model_ids):
            self.assertEqual(fetch.await_count, 1)
            self.assertIn(truth, prompt)
            self.assertIn(sources[0].url, prompt)
            self.assertIn("Current UTC date:", prompt)
            self.assertIn("do not fill gaps from training memory", prompt)
            return outputs

        with patch("core.pipeline.execute_parallel", new=AsyncMock(side_effect=generate_from_evidence)), \
             patch("core.pipeline.fetch_dynamic_sources", new=AsyncMock(return_value=(sources, []))) as fetch, \
             patch("api.routes.query.save_query_result", new=AsyncMock()), \
             TestClient(app) as client:
            self.assertEqual(client.get("/health").status_code, 200)
            response = client.post("/api/query", json={
                "query": "In what year did Apollo 11 land on the Moon?",
                "enabled_models": [output.model_id for output in outputs], "use_rag": False,
            })
        self.assertEqual(response.status_code, 200, response.text)
        fetch.assert_awaited_once()
        result = response.json()
        self.assertEqual([item["label"] for item in result["hallucination_results"]],
                         ["reliable", "reliable", "hallucinated"])
        self.assertNotIn("1989", result["final_answer"]["text"])
        self.assertEqual(result["final_answer"]["source_model_id"], "verified-synthesis")
        self.assertEqual(result["explanation"]["rag_sources_used"][0]["url"], sources[0].url)
        self.assertNotIn("text", result["explanation"]["rag_sources_used"][0])

    def test_missing_evidence_prompt_requires_abstention(self):
        from fastapi.testclient import TestClient
        from main import app

        with patch("core.pipeline.execute_parallel", new=AsyncMock(return_value=[])) as generate, \
             patch("core.pipeline.fetch_dynamic_sources", new=AsyncMock(return_value=([], []))), \
             patch("api.routes.query.save_query_result", new=AsyncMock()), TestClient(app) as client:
            response = client.post("/api/query", json={"query": "Who is the current chief minister?"})
        self.assertEqual(response.status_code, 200, response.text)
        prompt = generate.call_args.kwargs["prompt"]
        self.assertIn("Evidence (JSON): []", prompt)
        self.assertIn("the current answer cannot be verified", prompt)
        self.assertFalse(response.json()["explanation"]["rag_sources_used"])


if __name__ == "__main__":
    unittest.main(verbosity=2)