import re
from utils.logger import get_logger

logger = get_logger(__name__)

CONTRADICTION_PAIRS = [
    (r"\bnever won\b", r"\bhas won\b|\bdid win\b|\bwon the\b"),
    (r"\bhas not won\b|\bhave not won\b", r"\bhas won\b|\bhave won\b"),
    (r"\bdoes not exist\b", r"\bexists\b|\bdoes exist\b"),
    (r"\bno\b", r"\byes\b"),
    (r"\bfalse\b", r"\btrue\b"),
    (r"\bincorrect\b", r"\bcorrect\b"),
    (r"\bnot true\b", r"\bis true\b"),
]

# Minimum word count to consider for contradiction detection
MIN_WORDS_FOR_CONTRADICTION = 30


def clean_for_contradiction(text: str) -> str:
    """Remove thinking tags before checking contradictions."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    text = re.sub(r"<thinking>.*?</thinking>", "", text, flags=re.DOTALL)
    return text.strip()


def detect_contradictions(
    responses: dict[str, str],
    similarity_pairs: list = None,
) -> list[str]:
    contradictions = []
    model_ids = list(responses.keys())
    texts = list(responses.values())

    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):

            # Clean thinking tags first
            text_a = clean_for_contradiction(texts[i]).lower()
            text_b = clean_for_contradiction(texts[j]).lower()

            # Skip very short texts
            if (len(text_a.split()) < MIN_WORDS_FOR_CONTRADICTION or
                    len(text_b.split()) < MIN_WORDS_FOR_CONTRADICTION):
                continue

            # Skip if similarity is high
            if similarity_pairs:
                for pair in similarity_pairs:
                    if pair[0] == i and pair[1] == j:
                        if pair[2] > 0.4:
                            continue

            for neg_pattern, pos_pattern in CONTRADICTION_PAIRS:
                a_has_neg = bool(re.search(neg_pattern, text_a))
                b_has_pos = bool(re.search(pos_pattern, text_b))
                b_has_neg = bool(re.search(neg_pattern, text_b))
                a_has_pos = bool(re.search(pos_pattern, text_a))

                if (a_has_neg and b_has_pos) or (b_has_neg and a_has_pos):
                    contradiction = (
                        f"{model_ids[i]} and {model_ids[j]} "
                        f"give conflicting information"
                    )
                    if contradiction not in contradictions:
                        contradictions.append(contradiction)
                    break

    return contradictions


def detect_vagueness(text: str) -> bool:
    text = clean_for_contradiction(text)
    vague_patterns = [
        r"\bi (don't|do not) know\b",
        r"\bi('m| am) not sure\b",
        r"\bit depends\b",
        r"\bmaybe\b",
        r"\bperhaps\b",
    ]
    text_lower = text.lower()
    return any(bool(re.search(p, text_lower)) for p in vague_patterns)


def detect_missing_info(text: str, query: str) -> bool:
    text = clean_for_contradiction(text)
    if len(text.split()) < 10:
        return True
    query_keywords = [
        w.lower() for w in query.split()
        if len(w) > 4
    ]
    text_lower = text.lower()
    matched = sum(1 for k in query_keywords if k in text_lower)
    if query_keywords:
        return (matched / len(query_keywords)) < 0.3
    return False