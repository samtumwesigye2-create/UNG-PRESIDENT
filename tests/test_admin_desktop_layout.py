from pathlib import Path


def test_admin_shell_forces_desktop_canvas_on_narrow_screens():
    source = Path('bootstrap.py').read_text()
    assert 'min-width:1180px' in source
    assert '.admin-sidebar{width:260px!important;flex:0 0 260px!important' in source
    assert '.admin-main{width:920px!important;flex:0 0 920px!important' in source
    assert 'overflow-x:auto!important' in source
