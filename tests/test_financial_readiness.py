from aurelix_core.server import _financial_execution_status


def test_financial_execution_is_not_claimed_from_configuration(monkeypatch):
    monkeypatch.setenv("AURELIX_FINANCIAL_PROVIDER", "fake-or-unimplemented-provider")

    assert _financial_execution_status() == "FINANCIAL_EXECUTION_NOT_CONNECTED"
