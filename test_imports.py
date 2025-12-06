#!/usr/bin/env python3
"""
Test basic imports of the refactored modules.
This script checks that the module structure imports correctly.
"""
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("Testing module imports...")

# Test imports from each module
modules_to_test = [
    ("planka_mcp.models", ["ResponseFormat", "DetailLevel", "GetWorkspaceInput"]),
    ("planka_mcp.cache", ["CacheEntry", "PlankaCache"]),
    ("planka_mcp.api_client", ["PlankaAPIClient", "initialize_auth"]),
    ("planka_mcp.utils", ["ResponseFormatter", "PaginationHelper", "handle_api_error"]),
    ("planka_mcp.handlers", [
        "planka_get_workspace", "planka_list_cards", "planka_find_and_get_card",
        "planka_get_card", "planka_create_card", "planka_update_card",
        "planka_add_task", "planka_update_task", "planka_add_card_label",
        "planka_remove_card_label", "fetch_workspace_data"
    ]),
    ("planka_mcp.server", ["mcp", "api_client", "cache", "initialize_server", "cleanup_server"]),
]

success_count = 0
total_count = 0

for module_name, imports_to_test in modules_to_test:
    try:
        module = __import__(module_name)
        print(f"✓ {module_name} imports successfully")
        success_count += 1

        # Test individual imports
        for import_name in imports_to_test:
            try:
                getattr(module, import_name)
                print(f"  ✓ {import_name} available")
            except AttributeError:
                print(f"  ✗ {import_name} not found in {module_name}")
    except ImportError as e:
        print(f"✗ Failed to import {module_name}: {e}")
    except Exception as e:
        print(f"✗ Error importing {module_name}: {e}")

    total_count += 1

print(f"\nImport test results: {success_count}/{total_count} modules imported successfully")

# Test circular dependency avoidance
print("\n\nChecking for circular dependencies...")
try:
    # Try to import modules in different orders
    import planka_mcp.models as models
    import planka_mcp.utils as utils
    import planka_mcp.cache as cache
    import planka_mcp.api_client as api_client
    import planka_mcp.handlers.workspace as workspace
    import planka_mcp.handlers.cards as cards
    import planka_mcp.server as server

    print("✓ No circular import errors detected")

    # Check that utils doesn't import handlers
    utils_attrs = dir(utils)
    if 'planka_get_workspace' not in utils_attrs and 'planka_list_cards' not in utils_attrs:
        print("✓ utils.py doesn't import handlers (unidirectional dependencies)")
    else:
        print("✗ utils.py imports handlers - potential circular dependency")

except Exception as e:
    print(f"✗ Circular dependency check failed: {e}")

print("\n\nTesting backward compatibility bridge...")
try:
    import planka_mcp as original_interface
    print("✓ Original planka_mcp.py imports successfully")

    # Check that all expected exports are available
    expected_exports = [
        'mcp', 'api_client', 'cache',
        'planka_get_workspace', 'planka_list_cards', 'planka_find_and_get_card',
        'planka_get_card', 'planka_create_card', 'planka_update_card',
        'planka_add_task', 'planka_update_task', 'planka_add_card_label',
        'planka_remove_card_label', 'fetch_workspace_data',
        'ResponseFormat', 'DetailLevel', 'ResponseContext',
        'GetWorkspaceInput', 'ListCardsInput', 'GetCardInput',
        'CreateCardInput', 'UpdateCardInput', 'FindAndGetCardInput',
        'AddTaskInput', 'UpdateTaskInput', 'AddCardLabelInput',
        'RemoveCardLabelInput', 'CacheEntry', 'PlankaCache',
        'handle_api_error', 'ResponseFormatter', 'PaginationHelper'
    ]

    missing_exports = []
    for export in expected_exports:
        if not hasattr(original_interface, export):
            missing_exports.append(export)

    if missing_exports:
        print(f"✗ Missing exports: {missing_exports}")
    else:
        print("✓ All expected exports available")

except Exception as e:
    print(f"✗ Backward compatibility test failed: {e}")

print("\n\nModule structure summary:")
print("✓ models.py: Enums and Pydantic models")
print("✓ cache.py: Cache system classes")
print("✓ api_client.py: API client and authentication")
print("✓ utils.py: Response formatting, pagination, error handling")
print("✓ handlers/: Tool implementations grouped by functionality")
print("✓ server.py: Main entry point and MCP initialization")
print("✓ planka_mcp.py: Backward compatibility bridge")