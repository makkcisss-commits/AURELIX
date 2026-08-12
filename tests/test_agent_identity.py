from aurelix_runtime.agent_identity import create_identity, derive_agent_id


def test_identity_is_stable_for_same_contract() -> None:
    a = create_identity(role="research", owner="owner", tools=("web.read",), environment="sandbox")
    b = create_identity(role="research", owner="owner", tools=("web.read",), environment="sandbox")
    assert a.agent_id == b.agent_id


def test_identity_changes_when_tools_change() -> None:
    a = derive_agent_id(role="research", owner="owner", tools=("web.read",), environment="sandbox")
    b = derive_agent_id(role="research", owner="owner", tools=("web.read", "db.write"), environment="sandbox")
    assert a != b
