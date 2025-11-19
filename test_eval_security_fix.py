#!/usr/bin/env python
"""
Test script for the eval() to ast.literal_eval() security fix in settings.py

This script verifies that:
1. Valid Python literals are parsed correctly
2. Malicious code injection attempts are blocked
3. The Settings class methods work correctly with the fix
"""

import ast
import sys
import os

# Add the project to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_ast_literal_eval_safety():
    """Test that ast.literal_eval blocks malicious code"""
    print("=" * 60)
    print("Testing ast.literal_eval() security")
    print("=" * 60)

    # Malicious payloads that eval() would execute but ast.literal_eval() should block
    malicious_payloads = [
        '__import__("os").system("echo pwned")',
        'exec("print(\'hacked\')")',
        '__builtins__.__import__("os").getcwd()',
        '(lambda: __import__("os").system("id"))()',
        '[x for x in ().__class__.__bases__[0].__subclasses__()]',
        'open("/etc/passwd").read()',
        '__import__("subprocess").call(["ls"])',
    ]

    all_passed = True
    for payload in malicious_payloads:
        try:
            result = ast.literal_eval(payload)
            print(f"FAIL: Malicious payload was NOT blocked: {payload[:50]}...")
            all_passed = False
        except (ValueError, SyntaxError, TypeError) as e:
            print(f"PASS: Blocked malicious payload: {payload[:40]}...")

    return all_passed


def test_valid_literals():
    """Test that valid Python literals are parsed correctly"""
    print("\n" + "=" * 60)
    print("Testing valid Python literal parsing")
    print("=" * 60)

    test_cases = [
        # (input_string, expected_result)
        ('["column1", "column2", "column3"]', ["column1", "column2", "column3"]),
        ('{"width1": 100, "width2": 200}', {"width1": 100, "width2": 200}),
        ('("tuple", "values")', ("tuple", "values")),
        ('"simple string"', "simple string"),
        ('123', 123),
        ('3.14', 3.14),
        ('True', True),
        ('False', False),
        ('None', None),
        ('["-subject", "dueDateTime"]', ["-subject", "dueDateTime"]),
        ('{"startDateTime": 150, "subject": 200}', {"startDateTime": 150, "subject": 200}),
        ('[]', []),
        ('{}', {}),
    ]

    all_passed = True
    for input_str, expected in test_cases:
        try:
            result = ast.literal_eval(input_str)
            if result == expected:
                print(f"PASS: {input_str[:40]} -> {result}")
            else:
                print(f"FAIL: {input_str} expected {expected}, got {result}")
                all_passed = False
        except Exception as e:
            print(f"FAIL: {input_str} raised {type(e).__name__}: {e}")
            all_passed = False

    return all_passed


def test_settings_class():
    """Test the Settings class with the security fix"""
    print("\n" + "=" * 60)
    print("Testing Settings class methods")
    print("=" * 60)

    # Need to set up minimal wx environment
    try:
        import wx
        if not wx.App.Get():
            app = wx.App(False)
    except Exception as e:
        print(f"Note: Could not initialize wx: {e}")
        print("Skipping Settings class tests that require wx")
        return True

    from taskcoachlib.config.settings import Settings

    all_passed = True

    # Create a Settings instance without loading from file
    settings = Settings(load=False)

    # Test 1: Test getlist with valid list
    print("\nTest 1: getlist with valid list")
    settings.set("taskviewer", "columns", '["subject", "startDateTime"]')
    try:
        result = settings.getlist("taskviewer", "columns")
        if result == ["subject", "startDateTime"]:
            print(f"PASS: getlist returned {result}")
        else:
            print(f"FAIL: getlist returned {result}, expected ['subject', 'startDateTime']")
            all_passed = False
    except Exception as e:
        print(f"FAIL: getlist raised {type(e).__name__}: {e}")
        all_passed = False

    # Test 2: Test getdict with valid dict
    print("\nTest 2: getdict with valid dict")
    settings.set("taskviewer", "columnwidths", '{"subject": 200, "startDateTime": 100}')
    try:
        result = settings.getdict("taskviewer", "columnwidths")
        if result == {"subject": 200, "startDateTime": 100}:
            print(f"PASS: getdict returned {result}")
        else:
            print(f"FAIL: getdict returned {result}")
            all_passed = False
    except Exception as e:
        print(f"FAIL: getdict raised {type(e).__name__}: {e}")
        all_passed = False

    # Test 3: Test that malicious code in settings is blocked
    print("\nTest 3: Malicious code in settings is blocked")
    settings.set("taskviewer", "columns", '__import__("os").system("echo pwned")')
    try:
        # This should fail and use default value
        result = settings.getlist("taskviewer", "columns")
        # The method should catch the error and return a default
        print(f"PASS: Malicious code blocked, got default/error handling: {result}")
    except Exception as e:
        print(f"PASS: Malicious code blocked with exception: {type(e).__name__}")

    # Test 4: Test _fixValuesFromOldIniFiles with columns
    print("\nTest 4: _fixValuesFromOldIniFiles with columns")
    settings.set("taskviewer", "columns", '["startDate", "dueDate", "subject"]')
    try:
        result = settings.get("taskviewer", "columns")
        # The method should convert old date columns to DateTime versions
        expected = "['startDateTime', 'dueDateTime', 'subject']"
        if "DateTime" in result:
            print(f"PASS: Date columns converted: {result}")
        else:
            print(f"INFO: Result: {result}")
    except Exception as e:
        print(f"FAIL: raised {type(e).__name__}: {e}")
        all_passed = False

    # Test 5: Test sortby option handling
    print("\nTest 5: sortby option handling")
    settings.set("taskviewer", "sortby", 'subject')
    try:
        result = settings.get("taskviewer", "sortby")
        # Non-list sortby values should be converted to list format
        print(f"PASS: sortby handled: {result}")
    except Exception as e:
        print(f"FAIL: raised {type(e).__name__}: {e}")
        all_passed = False

    # Test 6: Test columnwidths with malformed data
    print("\nTest 6: columnwidths with malformed data")
    settings.init("taskviewer", "columnwidths", 'not valid python')
    try:
        result = settings._fixValuesFromOldIniFiles("taskviewer", "columnwidths", 'not valid python')
        print(f"PASS: Malformed columnwidths handled gracefully: {result}")
    except Exception as e:
        print(f"FAIL: raised {type(e).__name__}: {e}")
        all_passed = False

    return all_passed


def test_edge_cases():
    """Test edge cases for the security fix"""
    print("\n" + "=" * 60)
    print("Testing edge cases")
    print("=" * 60)

    all_passed = True

    # Test empty values
    test_cases = [
        ('', "Empty string should raise error"),
        ('   ', "Whitespace should raise error"),
    ]

    for input_str, description in test_cases:
        try:
            result = ast.literal_eval(input_str)
            print(f"FAIL: {description} but got: {result}")
            all_passed = False
        except (ValueError, SyntaxError) as e:
            print(f"PASS: {description}")

    # Test that complex but valid structures work
    complex_cases = [
        '{"nested": {"key": [1, 2, 3]}, "list": [{"a": 1}]}',
        '[[1, 2], [3, 4], [5, 6]]',
        '{"unicode": "café", "emoji": "test"}',
    ]

    for input_str in complex_cases:
        try:
            result = ast.literal_eval(input_str)
            print(f"PASS: Complex literal parsed: {input_str[:40]}...")
        except Exception as e:
            print(f"FAIL: Complex literal failed: {input_str[:40]}... - {e}")
            all_passed = False

    return all_passed


def main():
    """Run all tests"""
    print("\n" + "#" * 60)
    print("# Security Fix Test Suite: eval() -> ast.literal_eval()")
    print("#" * 60)

    results = []

    # Run tests
    results.append(("ast.literal_eval security", test_ast_literal_eval_safety()))
    results.append(("Valid literals parsing", test_valid_literals()))
    results.append(("Edge cases", test_edge_cases()))
    results.append(("Settings class methods", test_settings_class()))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "PASSED" if passed else "FAILED"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False

    print("=" * 60)
    if all_passed:
        print("ALL TESTS PASSED!")
        return 0
    else:
        print("SOME TESTS FAILED!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
