from nexus_agent.session import detect_session

def test_x11_session_is_supported(monkeypatch):
    monkeypatch.setenv("XDG_SESSION_TYPE", "x11")
    monkeypatch.setenv("DISPLAY", ":0")
    result = detect_session()
    assert result.kind == "x11"
    assert result.supported_for_mvp is True

def test_wayland_is_not_marked_supported(monkeypatch):
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.delenv("DISPLAY", raising=False)
    result = detect_session()
    assert result.kind == "wayland"
    assert result.supported_for_mvp is False

def test_unknown_session_is_not_supported(monkeypatch):
    monkeypatch.delenv("XDG_SESSION_TYPE", raising=False)
    monkeypatch.delenv("DISPLAY", raising=False)
    result = detect_session()
    assert result.kind == "unknown"
    assert result.supported_for_mvp is False
