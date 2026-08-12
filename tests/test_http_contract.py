from aurelix_core.http_contract import health_response, readiness_response, safe_error_response


def test_health_response_is_minimal() -> None:
    response = health_response()
    assert response.status == 200
    assert response.body == {"status": "ok", "service": "aurelix-private-api"}


def test_readiness_response_hides_internal_details() -> None:
    assert readiness_response(True).status == 200
    assert readiness_response(False).status == 503
    assert readiness_response(False).body == {"status": "not_ready"}


def test_error_response_does_not_expose_exception_details() -> None:
    response = safe_error_response(401, "authentication_failed")
    assert response.body == {"error": "authentication_failed"}
