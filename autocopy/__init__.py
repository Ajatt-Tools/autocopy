# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

try:
    # https://github.com/beartype/beartype
    from beartype.claw import beartype_this_package

    beartype_this_package()
except ImportError:
    print("Note: beartype is disabled in this session.")

import sys

from aqt import mw


def start_addon() -> None:
    """Import and initialize Anki-only add-on components in dependency order."""
    # These imports require Anki. Keep them here so standalone imports remain safe.
    from . import clipboard_monitor, main, menus

    main.init()
    menus.init()
    clipboard_monitor.init()


# Match AJT_Japanese startup without installing UI callbacks during test collection.
if mw and "pytest" not in sys.modules:
    start_addon()
