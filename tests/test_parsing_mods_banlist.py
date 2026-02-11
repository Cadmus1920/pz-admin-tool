import sys
import os
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from pz_admin_tool import PZServerAdmin
import tkinter.messagebox as mb

# Suppress messagebox dialogs during tests
mb.showinfo = lambda *a, **k: None
mb.showwarning = lambda *a, **k: None
mb.showerror = lambda *a, **k: None
mb.askyesno = lambda *a, **k: True


def test_mods_and_workshop_parsing():
    tmp = tempfile.mkdtemp()
    try:
        server_dir = os.path.join(tmp, 'Server')
        os.makedirs(server_dir, exist_ok=True)
        ini_path = os.path.join(server_dir, 'server.ini')
        with open(ini_path, 'w', encoding='utf-8') as f:
            f.write('Mods=modA;modB;modC\n')
            f.write('WorkshopItems=11111;22222;33333\n')

        app = PZServerAdmin()
        app.server_path.set(tmp)

        # Clear trees just in case
        for t in [app.mods_tree, app.workshop_tree]:
            for item in t.get_children():
                t.delete(item)

        app.refresh_mods()

        mods = [app.mods_tree.item(i)['values'][0] for i in app.mods_tree.get_children()]
        workshop = [app.workshop_tree.item(i)['values'][0] for i in app.workshop_tree.get_children()]

        assert mods == ['modA', 'modB', 'modC'], f'mods parsed incorrectly: {mods}'
        # Workshop IDs may be stored as ints by the tree; normalize to strings for comparison
        workshop_strs = [str(w) for w in workshop]
        assert workshop_strs == ['11111', '22222', '33333'], f'workshop parsed incorrectly: {workshop}'

        app.destroy()
        print('test_mods_and_workshop_parsing: OK')
    finally:
        shutil.rmtree(tmp)


def test_banlist_parsing():
    tmp = tempfile.mkdtemp()
    try:
        server_dir = os.path.join(tmp, 'Server')
        os.makedirs(server_dir, exist_ok=True)
        ban_path = os.path.join(server_dir, 'banlist.txt')
        with open(ban_path, 'w', encoding='utf-8') as f:
            f.write('# comment line\n')
            f.write('alice,1.2.3.4,cheating\n')
            f.write('bob\n')

        app = PZServerAdmin()
        app.server_path.set(tmp)

        # Clear banlist tree
        for item in app.banlist_tree.get_children():
            app.banlist_tree.delete(item)

        app.refresh_banlist()

        entries = [app.banlist_tree.item(i)['values'] for i in app.banlist_tree.get_children()]
        # entries are tuples (Username, IP, Reason, Date)
        assert any(e[0] == 'alice' and e[1] == '1.2.3.4' for e in entries), f"alice not parsed: {entries}"
        assert any(e[0] == 'bob' for e in entries), f"bob not parsed: {entries}"

        app.destroy()
        print('test_banlist_parsing: OK')
    finally:
        shutil.rmtree(tmp)


if __name__ == '__main__':
    test_mods_and_workshop_parsing()
    test_banlist_parsing()
    print('All parsing tests passed')
    raise SystemExit(0)
