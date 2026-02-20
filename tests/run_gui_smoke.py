import sys
import sys
import os

# Ensure repo root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from pz_admin_tool import PZServerAdmin

import pytest

def test_gui_smoke():
    app = PZServerAdmin()
    app.after(2000, app.destroy)
    try:
        app.mainloop()
    except Exception as e:
        pytest.fail(f'GUI smoke test failed: {e}')
