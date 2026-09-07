"""RAG eval gate: golden set + deterministic student + faithfulness gate.

Runs without API keys or a database: a keyword retriever ranks the
fixture corpus, a stub student answers from retrieved contexts with
``[N]`` markers (abstaining when nothing relevant is found), and the
structural scorer from ``app.core.eval_scoring`` grades every item.

CI contract: exit 0 only when mean faithfulness >= 0.85.
Swap ``retrieve``/``student_answer`` for the real pipeline (hybrid_search
+ LLM) to measure production quality with the same gate.
"""

import json
import os
import re
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.core.eval_scoring import GATE_THRESHOLD, gate_passed, mean_faithfulness, score_item  # noqa: E402

EVALS_DIR = Path(__file__).resolve().parent

STOPWORDS = {
    "qual", "quais", "como", "onde", "quando", "quanto", "quanta", "que",
    "para", "pelo", "pela", "dos", "das", "nos", "nas", "isso", "esta",
    "este", "entre", "sobre", "com", "sem", "por", "uma", "uns", "umas",
    "dos", "algo", "algo", "seu", "sua", "meus", "meu", "faz", "fica",
    "cabe", "fica", "the", "dos", "das",
}

ABSTAIN_ANSWER = (
    "Não encontrei fundamento nos documentos para responder a essa pergunta."
)


def content_tokens(text: str) -> set[str]:
    words = re.findall(r"[a-zà-ú0-9]+", text.lower())
    return {w for w in words if len(w) > 3 and w not in STOPWORDS}


def retrieve(question: str, corpus: list[dict], top_k: int = 3) -> list[dict]:
    """Keyword retriever: rank chunks by question-term overlap.

    Returns [] when even the best chunk shares fewer than 2 content
    tokens — the abstention trigger (mirrors "no relevant context").
    """
    query_tokens = content_tokens(question)
    ranked = sorted(
        corpus,
        key=lambda c: len(query_tokens & content_tokens(c["content"])),
        reverse=True,
    )
    if not ranked or len(query_tokens & content_tokens(ranked[0]["content"])) < 2:
        return []
    return [
        c
        for c in ranked[:top_k]
        if query_tokens & content_tokens(c["content"])
    ]


def student_answer(question: str, contexts: list[dict]) -> tuple[str, list[dict]]:
    """Stub student: echo retrieved contexts, citing every claim sentence.

    Models the grounded behavior the gate enforces: each sentence that
    states a claim carries its [N] marker; abstains when nothing was
    retrieved.
    """
    from app.core.eval_scoring import needs_citation, split_sentences

    if not contexts:
        return ABSTAIN_ANSWER, []
    sentences = []
    citations = []
    for i, chunk in enumerate(contexts, start=1):
        for sentence in split_sentences(chunk["content"]):
            if needs_citation(sentence):
                # Marker before terminal punctuation so it survives splitting.
                marked = re.sub(r"([.!?])$", f" [{i}]\\1", sentence)
                sentences.append(marked if marked != sentence else f"{sentence} [{i}]")
            else:
                sentences.append(sentence)
        citations.append({"ref": f"[{i}]", "chunk_id": chunk["id"]})
    return " ".join(sentences), citations


def evaluate_all(
    golden: list[dict], corpus: list[dict], student=student_answer
) -> list[dict]:
    scores = []
    for item in golden:
        contexts = retrieve(item["question"], corpus)
        answer, citations = student(item["question"], contexts)
        scores.append(
            score_item(
                item,
                answer,
                citations,
                [c["content"] for c in contexts],
            )
        )
    return scores


def main() -> int:
    golden = json.loads((EVALS_DIR / "golden_legal.json").read_text(encoding="utf-8"))[
        "items"
    ]
    corpus = json.loads((EVALS_DIR / "corpus_fixture.json").read_text(encoding="utf-8"))[
        "chunks"
    ]
    scores = evaluate_all(golden, corpus)
    mean_f = mean_faithfulness(scores)
    failures = [s["id"] for s in scores if s["faithfulness"] < 1.0]
    print(f"items={len(scores)} mean_faithfulness={mean_f:.3f} threshold={GATE_THRESHOLD}")
    if failures:
        print(f"non-perfect items: {', '.join(failures)}")
    for item_id in [i["id"] for i in golden if i.get("abstain_expected")]:
        row = next(s for s in scores if s["id"] == item_id)
        print(f"  {item_id}: abstained={row['abstained']} faithfulness={row['faithfulness']}")
    if not gate_passed(scores):
        print("GATE FAILED")
        return 1
    print("GATE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
