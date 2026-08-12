from aurelix_core.governor import Governor, GovernorRoute


def test_capital_request_requires_owner() -> None:
    result = Governor().route(source="opportunity", action="run experiment", requires_capital=True, risk=2, production_change=False)
    assert result.route is GovernorRoute.OWNER_REQUIRED


def test_high_risk_is_blocked() -> None:
    result = Governor().route(source="agent", action="change production", requires_capital=False, risk=8, production_change=True)
    assert result.route is GovernorRoute.BLOCKED


def test_low_risk_request_is_policy_allowed_but_execution_stays_gated() -> None:
    result = Governor().route(source="research", action="collect evidence", requires_capital=False, risk=1, production_change=False)
    assert result.route is GovernorRoute.POLICY_ALLOWED
