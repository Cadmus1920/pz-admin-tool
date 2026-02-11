import sys
import os

# Ensure repo root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from pz_admin_tool import PZServerAdmin

if __name__ == '__main__':
    app = PZServerAdmin()
    # Close after 2 seconds
    app.after(2000, app.destroy)
    try:
        app.mainloop()
        print('GUI smoke test completed')
    except Exception as e:
        print('GUI smoke test failed with exception:', e)
        raise
