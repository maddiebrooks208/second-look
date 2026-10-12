"""Plain-code rules. These, not the model, decide the verdict."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

STOP, CAREFUL, OK = "Stop", "Be careful", "Looks OK"


@dataclass(frozen=True)
class Rule:
    id: str
    severity: str  # "high" or "medium"
    title: str
    why: str
    patterns: tuple[str, ...]


@dataclass
class Hit:
    rule: Rule
    evidence: list[str] = field(default_factory=list)


RULES: tuple[Rule, ...] = (
    Rule(
        "reverse-invoice", "high", "They want *you* to pay an invoice",
        "A real client pays you. An invoice or payment request sent to the worker "
        "(often called a fee, deposit or 'activation') is the reverse-invoice trap.",
        (r"\b(?:pay|settle|clear)\b[^.\n]{0,40}\binvoice\b",
         r"\binvoice\b[^.\n]{0,60}\b(?:sent to you|to your (?:email|paypal))",
         r"\b(?:registration|activation|onboarding|processing|verification) fee\b"),
    ),
    Rule(
        "pay-to-start", "high", "Pay first to get the job",
        "Being asked to buy a training kit, software, equipment or a 'starter pack' "
        "before you're paid is a classic advance-fee scam.",
        (r"\b(?:buy|purchase|pay for)\b[^.\n]{0,40}\b(?:training|kit|software|equipment|starter pack|license)\b",
         r"\b(?:refundable|reimbursed)\b[^.\n]{0,40}\b(?:after|once)\b"),
    ),
    Rule(
        "overpay-refund", "high", "Overpay and send back the difference",
        "Checks and transfers can bounce days later. If they overpay and ask you to "
        "refund the extra, the refund is the real money you lose.",
        (r"\b(?:send|refund|return|wire)\b[^.\n]{0,30}\b(?:the )?(?:difference|balance|extra|excess)\b",
         r"\b(?:cashier'?s check|certified check|money order)\b"),
    ),
    Rule(
        "odd-payment", "high", "Gift cards, crypto or wire only",
        "Gift cards, crypto and wire transfers can't be reversed, which is why scammers ask for them.",
        (r"\bgift ?cards?\b", r"\b(?:bitcoin|btc|usdt|crypto|western union|moneygram|zelle only)\b"),
    ),
    Rule(
        "share-secrets", "high", "Asks for logins, ID or bank details",
        "No client needs your passwords, one-time codes, ID scans or bank login to hire you.",
        (r"\b(?:password|login details|one[- ]time code|verification code|otp|ssn|social security)\b",
         r"\b(?:bank|online banking)\b[^.\n]{0,20}\b(?:login|password|details|account number)\b"),
    ),
    Rule(
        "off-platform", "medium", "Move off the platform before escrow",
        "Moving to WhatsApp, Telegram or personal email before a contract is funded "
        "removes the platform's payment protection.",
        (r"\b(?:whatsapp|telegram|signal|hangouts|wechat)\b",
         r"\b(?:outside|off) (?:of )?(?:the )?(?:platform|site|upwork|fiverr|freelancer)\b",
         r"\bpay you directly\b"),
    ),
    Rule(
        "pressure", "medium", "Rush and pressure",
        "Real deadlines exist, but 'right now or the job's gone' is meant to stop you checking.",
        (r"\b(?:urgent(?:ly)?|immediately|within (?:the )?(?:next )?\d+ (?:minutes|hours)|right now|asap)\b",),
    ),
    Rule(
        "big-free-test", "medium", "Large unpaid 'test task'",
        "A short paid trial is normal. A full deliverable 'as a test' is often free work that never gets paid.",
        (r"\b(?:unpaid|free)\b[^.\n]{0,20}\b(?:test|trial|sample)\b",
         r"\btest task\b"),
    ),
)


def scan(text: str, rules: tuple[Rule, ...] = RULES) -> list[Hit]:
    hits: list[Hit] = []
    for rule in rules:
        found: list[str] = []
        for pat in rule.patterns:
            for m in re.finditer(pat, text, flags=re.IGNORECASE):
                found.append(m.group(0).strip())
        if found:
            hits.append(Hit(rule, sorted(set(found), key=found.index)))
    return hits


def verdict(hits: list[Hit]) -> str:
    high = sum(1 for h in hits if h.rule.severity == "high")
    medium = sum(1 for h in hits if h.rule.severity == "medium")
    if high or medium >= 2:
        return STOP if high else CAREFUL
    return CAREFUL if medium else OK
