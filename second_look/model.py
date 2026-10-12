"""Local open-weight model layer (Gemma 3 1B via llama.cpp / llama-cpp-python).

The model never decides anything. It receives the verdict and the rule hits
that plain code already produced and is asked for (a) a short explanation and
(b) a polite reply draft. Everything it writes goes through `guard()`. If the
guard trips, or the model/runtime is missing, the fixed fallback text is used.
"""
from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass, field

from .rules import CAREFUL, OK, STOP, Hit

DEFAULT_MODEL_ENV = "SECOND_LOOK_MODEL"

FALLBACK_REPLY = {
    STOP: ("Thanks for reaching out. I keep all work and payment on the platform, through a funded "
           "contract or milestone. I don't cover any fees to start a job, and I keep my account "
           "details private. If you'd like to work together, I'm happy to continue there."),
    CAREFUL: ("Thanks for the message. Before I start, I'd like to keep our chat and the contract on the "
              "platform with a funded milestone. Happy to go from there."),
    OK: ("Thanks, this sounds good. I'm happy to start once the contract and first milestone are set up "
         "on the platform."),
}


def fallback_explanation(verdict: str, hits: list[Hit]) -> str:
    if not hits:
        return "No known payment-trap patterns were found. Still keep payment on the platform."
    titles = "; ".join(h.rule.title.replace("*", "") for h in hits)
    return f"Verdict: {verdict}. Patterns found: {titles}. A real client pays you, not the other way round."


EXPLAIN_SYSTEM = (
    "You explain scam-check results to a freelancer. The verdict is already decided by rules; "
    "state it and never contradict it. Write 2-3 plain sentences to the freelancer ('you') explaining "
    "what the client is asking for and why the findings matter. No greeting, no preamble, no quotes, "
    "no lists. Do not tell the freelancer to pay, buy, click, send or share anything."
)

REPLY_SYSTEM = (
    "You write the message a FREELANCER sends back to a CLIENT. Use the freelancer's voice ('I'). "
    "2 polite sentences, no greeting line, no sign-off, no placeholders. Keep the conversation, "
    "contract and payment on the platform (funded milestone or escrow). If the verdict is not "
    "'Looks OK', politely decline the risky part without accusing anyone. If it is 'Looks OK', "
    "accept warmly. Never include links or personal details. Output only the message."
)

# Few-shot turns: small models copy the shape of an example far better than they follow rules.
EXPLAIN_SHOTS = [
    ("VERDICT (fixed): Stop\nFINDINGS:\n- Gift cards, crypto or wire only: Gift cards, crypto and wire transfers can't be reversed. Evidence: 'gift card'\n\nCLIENT MESSAGE:\nBuy a $200 gift card for our office and we'll add it to your first invoice.",
     "Verdict: Stop. The client wants you to spend your own money on a gift card before they have paid you anything. Gift cards can't be traced or reversed, which is exactly why scammers ask for them."),
    ("VERDICT (fixed): Looks OK\nFINDINGS:\n- none\n\nCLIENT MESSAGE:\nCould you edit two blog posts this week? I'll fund a $90 milestone today.",
     "Verdict: Looks OK. This is an ordinary request with payment through a platform milestone, and none of the known trap patterns showed up."),
]
REPLY_SHOTS = [
    (EXPLAIN_SHOTS[0][0] + "\n\nWrite the freelancer's reply now.",
     "Thanks for the offer. I don't purchase anything up front, so if you'd like to work together please send the contract through the platform with a funded milestone."),
    (EXPLAIN_SHOTS[1][0] + "\n\nWrite the freelancer's reply now.",
     "Thanks, that works for me. I'll start as soon as the milestone is funded on the platform."),
]

# Things the drafted text must never tell the user to do.
_BANNED = [
    (r"\bpay(?:ing|s)?\b(?![- ]?(?:ments?\b))", "tells the user to pay"),
    (r"\b(?:send|wire|transfer|deposit|refund)\b[^.\n]{0,30}\b(?:money|funds|fee|payment|difference|deposit|\$)", "moves money"),
    (r"\b(?:buy|purchase)\b", "tells the user to buy something"),
    (r"\bgift ?cards?\b|\bcrypto\b|\bbitcoin\b", "mentions untraceable payment"),
    (r"\b(?:click|tap|open|follow|visit)\b[^.\n]{0,20}\b(?:link|url|here|attachment|website)\b", "tells the user to click"),
    (r"https?://|www\.|\b[\w-]+\.(?:com|net|org|io|ly)\b", "contains a link"),
    (r"\b(?:share|send|provide|give)\b[^.\n]{0,30}\b(?:password|login|code|otp|id\b|ssn|bank|account|address|phone|number|details|info)", "tells the user to share info"),
    (r"\bmy\b[^.\n]{0,15}\b(?:bank|account number|routing|password|login|ssn|social security|card number|home address)", "offers personal info"),
    (r"\b(?:whatsapp|telegram|signal|wechat)\b", "moves the chat off-platform"),
]
_TOO_SOFT = r"\b(?:legit(?:imate)?|safe to|is safe|nothing to worry|looks (?:fine|ok|good)|go ahead)\b"

# The explanation has to *describe* the scam ("they want you to pay a fee"), so it gets a
# narrower check: no instructions to act, no links, no softening.
_EXPLAIN_BANNED = [
    (r"\b(?:you should|go ahead and|please|need to|make sure (?:to|you)|proceed (?:to|with)(?: the)?|complete the)\s+(?:pay|send|buy|purchase|click|share|transfer|provide|deposit|verification|payment)", "tells the user to act"),
    (r"https?://|www\.", "contains a link"),
]


def guard(text: str, verdict: str) -> str | None:
    """Strict check for the reply draft. Return a reason if unsafe, else None."""
    for pat, reason in _BANNED:
        m = re.search(pat, text, flags=re.IGNORECASE)
        if m:
            return f"{reason}: {m.group(0)!r}"
    if verdict != OK and re.search(_TOO_SOFT, text, flags=re.IGNORECASE):
        return "softens a flagged verdict"
    if verdict != OK and re.search(r"\bdirectly\b", text, flags=re.IGNORECASE):
        return "agrees to deal directly"
    return None


def guard_explanation(text: str, verdict: str) -> str | None:
    for pat, reason in _EXPLAIN_BANNED:
        m = re.search(pat, text, flags=re.IGNORECASE)
        if m:
            return f"explanation {reason}: {m.group(0)!r}"
    if verdict != OK and re.search(_TOO_SOFT, text, flags=re.IGNORECASE):
        return "explanation softens a flagged verdict"
    if verdict != OK and re.search(r"\bstandard (?:security|payment|request|process|protocol)|standard practice for freelancers", text, re.I):
        return "explanation calls a flagged pattern normal"
    if not text.lower().startswith(f"verdict: {verdict.lower()}"):
        return "explanation does not state the fixed verdict"
    return None


def reply_quality(reply: str, verdict: str) -> str | None:
    if len(reply.split()) < 8:
        return f"reply too short: {reply!r}"
    if verdict != OK and not re.search(r"platform|milestone|escrow|contract", reply, re.I):
        return "reply doesn't keep things on the platform"
    if verdict == OK and re.search(r"unable|can(?:no|')t|decline", reply, re.I):
        return "reply turns down a normal request"
    return None


def build_prompt(message: str, verdict: str, hits: list[Hit]) -> str:
    lines = [f"VERDICT (fixed): {verdict}", "FINDINGS:"]
    lines += [f"- {h.rule.title.replace('*', '')}: {h.rule.why} Evidence: {', '.join(repr(e) for e in h.evidence)}" for h in hits] or ["- none"]
    lines += ["", "CLIENT MESSAGE:", message.strip()[:1500]]
    return "\n".join(lines)


def clean(s: str) -> str:
    s = re.sub(r"^(?:EXPLANATION|REPLY|Reply|Explanation)\s*:\s*", "", s.strip())
    s = re.sub(r"\[[^\]]*\]", "", s)  # drop [Your Name] style placeholders
    return re.sub(r"[*_#]+", "", s).strip().strip('"“”').strip()


@dataclass
class Advice:
    explanation: str
    reply: str
    source: str  # "model" or "fallback"
    meta: dict = field(default_factory=dict)


_LLM_CACHE: dict[str, object] = {}


def advise(message: str, verdict: str, hits: list[Hit], model_path: str | None = None,
           max_tokens: int = 220, use_model: bool = True) -> Advice:
    model_path = model_path or os.environ.get(DEFAULT_MODEL_ENV)
    fb = Advice(fallback_explanation(verdict, hits), FALLBACK_REPLY[verdict], "fallback")
    if not use_model:
        fb.meta = {"reason": "--no-model"}
        return fb
    if not model_path or not os.path.exists(model_path):
        fb.meta = {"reason": "model file not found"}
        return fb
    try:
        from llama_cpp import Llama
    except ImportError:
        fb.meta = {"reason": "llama-cpp-python not installed"}
        return fb
    t0 = time.perf_counter()
    llm = _LLM_CACHE.get(model_path)
    if llm is None:
        llm = Llama(model_path=model_path, n_ctx=2048, n_threads=os.cpu_count() or 4, verbose=False, seed=7)
        _LLM_CACHE[model_path] = llm
    t_load = time.perf_counter() - t0
    facts = build_prompt(message, verdict, hits)

    def ask(system: str, shots, user: str) -> tuple[str, int]:
        msgs = [{"role": "system", "content": system}]
        for q, a in shots:
            msgs += [{"role": "user", "content": q}, {"role": "assistant", "content": a}]
        o = llm.create_chat_completion(messages=msgs + [{"role": "user", "content": user}],
                                       max_tokens=max_tokens // 2, temperature=0.2, seed=7)
        return o["choices"][0]["message"]["content"].strip(), o.get("usage", {}).get("completion_tokens", 0)

    t1 = time.perf_counter()
    raw_e, n1 = ask(EXPLAIN_SYSTEM, EXPLAIN_SHOTS, facts)
    raw_r, n2 = ask(REPLY_SYSTEM, REPLY_SHOTS, facts + "\n\nWrite the freelancer's reply now.")
    meta = {"model": os.path.basename(model_path), "load_s": round(t_load, 2),
            "gen_s": round(time.perf_counter() - t1, 2), "completion_tokens": n1 + n2,
            "raw_explanation": raw_e, "raw_reply": raw_r}
    explanation, reply = clean(raw_e), clean(raw_r)
    # Each half is judged on its own: a good explanation survives a rejected reply.
    e_problem = guard_explanation(explanation, verdict) if explanation else "empty explanation"
    r_problem = (guard(reply, verdict) or reply_quality(reply, verdict)) if reply else "empty reply"
    if e_problem:
        explanation = fb.explanation
    if r_problem:
        reply = fb.reply
    meta["explanation_source"] = "fallback" if e_problem else "model"
    meta["reply_source"] = "fallback" if r_problem else "model"
    reasons = [f"guard tripped: {x}" for x in (e_problem, r_problem) if x]
    if reasons:
        meta["reason"] = "; ".join(reasons)
    if e_problem and r_problem:
        fb.meta = meta
        return fb
    if e_problem or r_problem:
        return Advice(explanation, reply, "mixed", meta)
    return Advice(explanation, reply, "model", meta)
