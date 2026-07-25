*** Begin Patch
*** Add File: tests/integration/compat_imports/test_tools_reexport.py
+#!/usr/bin/env python3
+"""Smoke test: legacy import compatibility for tools package.
+This small test is intended to be executed in CI pre-merge and nightly runs.
+It attempts legacy import patterns that older MCP entrypoints rely on and
+exits with non-zero on failure so the CI can block the release.
+"""
+import sys
+try:
+    # legacy import pattern
+    from tools import register_presentation_tools
+    print('OK')
+    sys.exit(0)
+except Exception as e:
+    print('FAIL', e)
+    sys.exit(2)
+
*** End Patch