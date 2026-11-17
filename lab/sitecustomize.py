"""Loaded by CPython before uvicorn. Product tree stays unmodified."""

import lab_patch

lab_patch.install_import_hook()
