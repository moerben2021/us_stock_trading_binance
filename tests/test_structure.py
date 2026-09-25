"""Test project structure initialization"""
import os
import sys

def test_project_structure():
    """Test that all required directories and files exist"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Test directories exist
    required_dirs = [
        'core', 'strategies', 'integrations', 'storage', 'config', 'utils',
        'configs', 'configs/accounts', 'configs/manual_trades', 'configs/manual_trades/archive',
        'secrets', 'logs', 'data',
        'tests', 'tests/core', 'tests/strategies', 'tests/integrations', 'tests/storage', 'tests/config', 'tests/utils'
    ]

    for dir_name in required_dirs:
        dir_path = os.path.join(base_dir, dir_name)
        assert os.path.isdir(dir_path), f"Directory not found: {dir_name}"

    # Test __init__.py files exist
    required_init_files = [
        'core/__init__.py', 'strategies/__init__.py', 'integrations/__init__.py',
        'storage/__init__.py', 'config/__init__.py', 'utils/__init__.py'
    ]

    for init_file in required_init_files:
        file_path = os.path.join(base_dir, init_file)
        assert os.path.isfile(file_path), f"Init file not found: {init_file}"

    # Test .gitkeep files exist
    required_gitkeeps = [
        'configs/.gitkeep', 'secrets/.gitkeep', 'logs/.gitkeep', 'data/.gitkeep'
    ]

    for gitkeep in required_gitkeeps:
        file_path = os.path.join(base_dir, gitkeep)
        assert os.path.isfile(file_path), f"Gitkeep file not found: {gitkeep}"

    # Test requirements.txt exists
    req_file = os.path.join(base_dir, 'requirements.txt')
    assert os.path.isfile(req_file), "requirements.txt not found"

    # Test .gitignore exists
    gitignore_file = os.path.join(base_dir, '.gitignore')
    assert os.path.isfile(gitignore_file), ".gitignore not found"

    # Test README.md exists
    readme_file = os.path.join(base_dir, 'README.md')
    assert os.path.isfile(readme_file), "README.md not found"

    print("All structure tests passed!")

if __name__ == '__main__':
    test_project_structure()
