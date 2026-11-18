from apps.marketing.forms import WaitlistForm

VALID = {"email": "dev@example.com", "product": "saas", "privacy": "on"}


def test_waitlist_form_valid_data_is_valid_and_not_spam():
    form = WaitlistForm(data=VALID)

    assert form.is_valid()
    assert not form.is_spam


def test_waitlist_form_without_privacy_acknowledgement_is_invalid():
    form = WaitlistForm(data={**VALID, "privacy": ""})

    assert not form.is_valid()
    assert "privacy" in form.errors


def test_waitlist_form_unknown_product_is_invalid():
    form = WaitlistForm(data={**VALID, "product": "linkinbio"})

    assert not form.is_valid()
    assert "product" in form.errors


def test_waitlist_form_filled_honeypot_is_spam():
    form = WaitlistForm(data={**VALID, "website": "http://spam.test"})

    assert form.is_valid()
    assert form.is_spam
