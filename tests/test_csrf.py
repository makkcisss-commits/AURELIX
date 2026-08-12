from aurelix_core.csrf import issue_csrf_token, valid_csrf


def test_csrf_token_round_trip() -> None:
    token = issue_csrf_token()
    assert token
    assert valid_csrf(token, token)
    assert not valid_csrf(token, "different")
    assert not valid_csrf(None, token)
