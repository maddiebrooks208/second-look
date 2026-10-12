import pytest

from second_look.model import FALLBACK_REPLY, advise, clean, guard
from second_look.rules import CAREFUL, OK, STOP, scan, verdict

UNSAFE = [
    "Sure, I'll pay the invoice today so we can get started.",
    "Please click the link to confirm your account.",
    "Open the attachment and follow the steps.",
    "Here is my bank account number for the deposit.",
    "I can share my login details if that helps.",
    "Happy to send the difference back once the check clears.",
    "I'll buy the starter kit this afternoon.",
    "Let's continue on WhatsApp.",
    "Details at https://example.com/verify",
    "Can I pay with gift cards?",
]
SAFE = [
    "Thanks for reaching out. I keep all work and payment on the platform through a funded milestone.",
    "I don't take on fees to start a job, but I'm happy to continue on the platform.",
]


@pytest.mark.parametrize("text", UNSAFE)
def test_guard_blocks(text):
    assert guard(text, STOP)


@pytest.mark.parametrize("text", SAFE)
def test_guard_allows_safe_reply(text):
    assert guard(text, STOP) is None


def test_guard_is_strict_about_the_word_pay():
    # Even "I won't pay" is rejected: the guard prefers a false alarm (fixed reply) to a miss.
    assert guard("I won't pay that fee.", STOP)


def test_guard_blocks_softening_flagged_verdict():
    assert guard("This looks legit, you can go ahead.", STOP)
    assert guard("This looks legit.", OK) is None


@pytest.mark.parametrize("v", [STOP, CAREFUL, OK])
def test_fallback_replies_pass_their_own_guard(v):
    assert guard(FALLBACK_REPLY[v], v) is None


def test_missing_model_uses_fallback():
    msg = "Please pay the onboarding fee invoice."
    hits = scan(msg)
    a = advise(msg, verdict(hits), hits, model_path="/nope/missing.gguf")
    assert a.source == "fallback" and a.reply == FALLBACK_REPLY[STOP]


def test_no_model_flag():
    a = advise("hi", OK, [], model_path="/nope", use_model=False)
    assert a.source == "fallback" and a.meta["reason"] == "--no-model"


def test_clean():
    assert clean('REPLY: "**No thanks.** [Your Name]"') == "No thanks."


def test_explanation_guard():
    from second_look.model import guard_explanation
    assert guard_explanation("Verdict: Stop. They want you to pay a fee first.", STOP) is None
    assert guard_explanation("Verdict: Stop. Please send your login to them.", STOP)
    assert guard_explanation("Verdict: Stop. This is a standard security protocol.", STOP)
    assert guard_explanation("Verdict: Looks OK. Fine.", STOP)  # wrong verdict


def test_reply_quality():
    from second_look.model import reply_quality
    assert reply_quality("Okay, I understand.", STOP)
    assert reply_quality("I'd prefer to keep everything on the platform with a funded milestone.", STOP) is None
    assert reply_quality("Sorry, I'm unable to take this on right now, thanks anyway.", OK)
