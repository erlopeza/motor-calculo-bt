import pytest
from gui.headless import hay_display

requiere_display = pytest.mark.skipif(not hay_display(), reason="sin display (headless)")


def test_hay_display_es_bool():
    assert isinstance(hay_display(), bool)
