from second_look.rules import CAREFUL, OK, STOP, scan, verdict


def ids(text):
    return {h.rule.id for h in scan(text)}


def test_reverse_invoice_is_stop():
    msg = "Welcome aboard! Please pay the onboarding fee invoice sent to your PayPal so we can release the brief."
    assert "reverse-invoice" in ids(msg)
    assert verdict(scan(msg)) == STOP


def test_overpay_refund():
    msg = "I mailed a cashier's check for $1,900. Keep $400 and send back the difference to my assistant."
    assert {"overpay-refund"} <= ids(msg)


def test_off_platform_plus_pressure_is_careful():
    msg = "Let's continue on Telegram, I need this urgently."
    assert ids(msg) == {"off-platform", "pressure"}
    assert verdict(scan(msg)) == CAREFUL


def test_normal_brief_is_ok():
    msg = ("Hi! We need 5 product descriptions for our candle shop, about 120 words each. "
           "Budget $150 through the platform's milestone. Can you deliver by Friday?")
    assert ids(msg) == set()
    assert verdict(scan(msg)) == OK
