import re

file_path = 'tests/test_tools.py'

with open(file_path, 'r') as f:
    content = f.read()

# Define the replacements for each handler
replacements = {
    'TestPlankaGetWorkspace': "with patch('planka_mcp.handlers.workspace.api_client', mock_planka_api_client), \
             patch('planka_mcp.handlers.workspace.cache', mock_cache)",
    'TestPlankaListCards': "with patch('planka_mcp.handlers.cards.api_client', mock_planka_api_client)",
    'TestPlankaFindAndGetCard': "with patch('planka_mcp.handlers.search.api_client', mock_planka_api_client), \
             patch('planka_mcp.handlers.search.cache', mock_cache)",
    'TestPlankaGetCard': "with patch('planka_mcp.handlers.cards.api_client', mock_planka_api_client), \
             patch('planka_mcp.handlers.cards.cache', mock_cache)",
    'TestPlankaCreateCard': "with patch('planka_mcp.handlers.cards.api_client', mock_planka_api_client), \
             patch('planka_mcp.handlers.cards.cache', mock_cache)",
    'TestPlankaUpdateCard': "with patch('planka_mcp.handlers.cards.api_client', mock_planka_api_client), \
             patch('planka_mcp.handlers.cards.cache', mock_cache)",
    'TestPlankaAddTask': "with patch('planka_mcp.handlers.tasks_labels.api_client', mock_planka_api_client), \
             patch('planka_mcp.handlers.tasks_labels.cache', mock_cache)",
    'TestPlankaUpdateTask': "with patch('planka_mcp.handlers.tasks_labels.api_client', mock_planka_api_client), \
             patch('planka_mcp.handlers.tasks_labels.cache', mock_cache)",
    'TestCacheBehavior': "with patch('planka_mcp.instances.api_client', mock_planka_api_client), \
             patch('planka_mcp.instances.cache', mock_cache)",
    'TestEdgeCases': "with patch('planka_mcp.handlers.workspace.api_client', mock_planka_api_client), \
             patch('planka_mcp.handlers.workspace.cache', mock_cache)",
    'TestPlankaAddCardLabel': "with patch('planka_mcp.handlers.tasks_labels.api_client', mock_planka_api_client), \
             patch('planka_mcp.handlers.tasks_labels.cache', mock_cache)",
    'TestPlankaRemoveCardLabel': "with patch('planka_mcp.handlers.tasks_labels.api_client', mock_planka_api_client), \
             patch('planka_mcp.handlers.tasks_labels.cache', mock_cache)"
}

# Regex to find all test classes and their content
class_pattern = re.compile(r"(class\s+(TestPlanka\w+):.*?)(?=class\s+TestPlanka|\Z)", re.DOTALL)

new_content = ""
last_end = 0

for match in class_pattern.finditer(content):
    class_name = match.group(2)
    class_content = match.group(1)
    start, end = match.span()
    
    new_content += content[last_end:start]
    
    if class_name in replacements:
        # The pattern to find the patch statements
        patch_pattern = re.compile(r"with patch\('planka_mcp.instances.api_client', mock_planka_api_client\), \\?\s*\n?\s*patch\('planka_mcp.instances.cache', mock_cache\):|with patch\('planka_mcp.instances.api_client', mock_planka_api_client\):")
        
        # Replace the patch statements
        new_class_content = patch_pattern.sub(replacements[class_name], class_content)
        new_content += new_class_content
    else:
        new_content += class_content
        
    last_end = end

new_content += content[last_end:]

with open(file_path, 'w') as f:
    f.write(new_content)
