from pathlib import Path


def test_admin_shell_forces_desktop_canvas_on_narrow_screens():
    source = Path('ung_president.py').read_text()
    assert 'min-width:1180px' in source
    assert '.admin-sidebar{width:260px;flex:0 0 260px' in source
    assert '.admin-main{width:920px;flex:0 0 920px' in source
    assert 'overflow-x:auto' in source
