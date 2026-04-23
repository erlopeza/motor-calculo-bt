from pathlib import Path


def test_main_flags_graficos_documentados():
    content = Path("main.py").read_text(encoding="utf-8")
    assert "--graficos" in content
    assert "--proyecto" in content
    assert "--excel" in content
    assert "--no-pause" in content
    assert "# agregado graficos" in content
