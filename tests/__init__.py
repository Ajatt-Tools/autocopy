# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

# Pytest's assertion-rewriting loader intercepts test imports before Beartype's package hook.
# tests/conftest.py wraps collected test functions instead, preserving assertion rewriting.
