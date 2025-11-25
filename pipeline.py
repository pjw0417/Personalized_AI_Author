# pipeline.py
import json
from typing import Any, Dict, List, Optional, Tuple

from langchain_core.output_parsers import StrOutputParser

from questionnaire import UserProfile
from llm_config import get_llm
from rag_store import get_vectorstore
from prompts import plan_prompt, draft_prompt, edit_prompt, critique_prompt, rewrite_prompt

parser = StrOutputParser()

# Retrieval tuning
RAG_TOP_K = 3  # final number of chunks injected into the prompt
RAG_CANDIDATE_K = 10  # initial pool for filtering
RAG_SCORE_THRESHOLD = 0.4  # lower (closer) is better for Chroma distances

def estimate_words(pages: int, words_per_page: int = 350) -> int:
    return pages * words_per_page

def get_rag_context(profile: UserProfile, extra_query: Optional[str] = None, k: int = 2) -> str:
    """
    Use the vector DB to grab a few relevant passages for inspiration.
    If the DB isn't built yet, just return an empty string.
    """
    db = get_vectorstore()
    if db is None:
        return ""

    query_parts = [
        profile.preferred_theme,
        profile.purpose_of_reading,
        profile.mood_today,
        profile.favorite_author,
        profile.special_request,
    ]
    if extra_query:
        query_parts.append(extra_query)

    query = " | ".join([q for q in query_parts if q])
    # Fetch a wider pool, then keep only high-similarity and diverse sources.
    scored = db.similarity_search_with_score(query, k=RAG_CANDIDATE_K)

    filtered: List[Any] = []
    for doc, score in scored:
        if score <= RAG_SCORE_THRESHOLD:
            filtered.append(doc)

    # Fallback to top candidates if nothing cleared the threshold.
    if not filtered:
        filtered = [doc for doc, _ in scored[:k or RAG_TOP_K]]

    # Prefer diversity by book title and cap total chunks.
    chosen: List[Any] = []
    seen_titles = set()
    max_chunks = k or RAG_TOP_K
    for doc in filtered:
        title = doc.metadata.get("title") if hasattr(doc, "metadata") else None
        if title and title in seen_titles and len(chosen) >= max_chunks:
            continue
        chosen.append(doc)
        if title:
            seen_titles.add(title)
        if len(chosen) >= max_chunks:
            break

    return "\n\n".join([doc.page_content for doc in chosen])

# --- STEP 1: PLANNING ---

def run_planning(profile: UserProfile) -> str:
    llm = get_llm(temperature=0.7)
    chain = plan_prompt | llm | parser
    return chain.invoke(vars(profile))

# --- STEP 2: DRAFTING (with RAG context) ---

def run_drafting(profile: UserProfile, plan: str) -> str:
    llm = get_llm(temperature=0.9)
    chain = draft_prompt | llm | parser

    approx_words = estimate_words(profile.length_in_pages)
    rag_context = get_rag_context(profile, extra_query="literary style inspiration", k=5)

    variables: Dict[str, object] = {
        **vars(profile),
        "plan": plan,
        "approx_word_count": approx_words,
        "rag_context": rag_context,
    }
    return chain.invoke(variables)

# --- STEP 3: EDITING ---

def run_editing(profile: UserProfile, draft: str) -> str:
    llm = get_llm(temperature=0.6)
    chain = edit_prompt | llm | parser
    return chain.invoke({
        **vars(profile),
        "draft": draft,
    })

# --- STEP 4: CRITIQUE + MICRO REWRITE ---

def ensure_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(v) for v in value if str(v).strip()]
    if not value:
        return []
    return [str(value)]

def parse_critique_response(raw: str) -> Dict[str, Any]:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Fallback if the model fails to follow JSON instructions
        data = {
            "summary": raw.strip(),
            "strengths": ["unparsed"],
            "weaknesses": ["Needs manual review"],
            "alignment": ["Needs manual review"],
            "actions": ["Re-run critique with JSON output."],
            "quality_score": 0,
            "evidence_snippets": [],
        }

    # Ensure required keys exist and have sensible defaults
    data.setdefault("summary", "")
    data.setdefault("strengths", [])
    data.setdefault("weaknesses", [])
    data.setdefault("alignment", [])
    data.setdefault("actions", [])
    data.setdefault("evidence_snippets", [])

    return data

def format_critique_report(critique: Dict[str, Any], round_number: int) -> str:
    score = critique.get("quality_score", "N/A")
    strengths = "\n".join(f"- {item}" for item in ensure_list(critique.get("strengths")))
    weaknesses = "\n".join(f"- {item}" for item in ensure_list(critique.get("weaknesses")))
    alignment = "\n".join(f"- {item}" for item in ensure_list(critique.get("alignment")))
    actions = "\n".join(f"- {item}" for item in ensure_list(critique.get("actions")))

    return (
        f"Round {round_number} Critique\n"
        f"Quality Score: {score}/10\n"
        f"Summary: {critique.get('summary', '').strip()}\n"
        f"Strengths:\n{strengths}\n"
        f"Weaknesses:\n{weaknesses}\n"
        f"Alignment Notes:\n{alignment}\n"
        f"Action Items:\n{actions}\n"
    ).strip()

def run_structured_critique(profile: UserProfile, final_text: str) -> Dict[str, Any]:
    llm = get_llm(temperature=0.5)
    chain = critique_prompt | llm | parser
    raw_response = chain.invoke({
        **vars(profile),
        "final_text": final_text,
    })
    critique = parse_critique_response(raw_response)
    return critique

def run_micro_rewrite(profile: UserProfile, current_text: str, weaknesses: List[str]) -> str:
    llm = get_llm(temperature=0.5)
    chain = rewrite_prompt | llm | parser
    focus_block = "\n".join(f"- {w}" for w in weaknesses) if weaknesses else "none"
    return chain.invoke({
        **vars(profile),
        "current_text": current_text,
        "critique_focus": focus_block,
    })

def should_stop_revision(score: float, weaknesses: List[str], threshold: float) -> bool:
    no_real_weaknesses = not weaknesses or all(w.lower() == "none" for w in weaknesses)
    return score >= threshold or no_real_weaknesses

def refine_with_critique(
    profile: UserProfile,
    edited_text: str,
    max_rounds: int = 2,
    quality_threshold: float = 8.5,
) -> Tuple[str, str]:
    current_text = edited_text
    critique_reports: List[str] = []

    for round_idx in range(max_rounds):
        critique = run_structured_critique(profile, current_text)
        critiques_list = ensure_list(critique.get("weaknesses"))
        try:
            score = float(critique.get("quality_score", 0))
        except (TypeError, ValueError):
            score = 0.0

        critique_reports.append(format_critique_report(critique, round_idx + 1))

        normalized_weaknesses = [
            w.strip() for w in critiques_list if w.strip() and w.strip().lower() != "none"
        ]

        if round_idx == max_rounds - 1 or should_stop_revision(score, normalized_weaknesses, quality_threshold):
            break

        current_text = run_micro_rewrite(profile, current_text, normalized_weaknesses)

    combined_report = "\n\n".join(critique_reports)
    return current_text, combined_report

# --- FULL PIPELINE ---

def generate_book_for_user(profile: UserProfile) -> Dict[str, str]:
    """
    High-level function that does:
        plan -> draft -> edit -> iterative critique/rewrite
    Returns all intermediate results.
    """
    plan = run_planning(profile)
    draft = run_drafting(profile, plan)
    edited_text = run_editing(profile, draft)
    final_text, critique_report = refine_with_critique(profile, edited_text)

    return {
        "plan": plan,
        "draft": draft,
        "final_text": final_text,
        "critique": critique_report,
    }
