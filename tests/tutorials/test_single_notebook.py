"""
Test a single notebook with detailed error output
"""
import sys
import os
from pathlib import Path
import nbformat
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError

# Get paths
SCRIPT_DIR = Path(__file__).parent
TUTORIALS_DIR = SCRIPT_DIR.parent.parent / "tutorials"
VRP_TOOLKIT_DIR = SCRIPT_DIR.parent.parent

# Add routing-heuristics to path
sys.path.insert(0, str(VRP_TOOLKIT_DIR))

def test_notebook(notebook_name):
    """Test a single notebook with full error details"""
    notebook_path = TUTORIALS_DIR / notebook_name

    print(f"Testing: {notebook_path}")
    print(f"Working directory: {TUTORIALS_DIR}")
    print()

    try:
        # Read the notebook
        with open(notebook_path, 'r', encoding='utf-8') as f:
            nb = nbformat.read(f, as_version=4)

        # Create client
        client = NotebookClient(
            nb,
            timeout=300,
            kernel_name='python3',
            resources={'metadata': {'path': str(TUTORIALS_DIR)}}
        )

        # Execute the notebook
        client.execute()

        print("SUCCESS: Notebook executed without errors")
        return True

    except CellExecutionError as e:
        print("CELL EXECUTION ERROR:")
        print(f"  Cell index: {e.cell_index}")
        print(f"  Error name: {e.ename}")
        print(f"  Error value: {e.evalue}")
        print()
        print("Full traceback:")
        print(e.traceback)
        return False

    except Exception as e:
        print(f"UNEXPECTED ERROR: {type(e).__name__}")
        print(f"Message: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_single_notebook.py <notebook_name>")
        print("Example: python test_single_notebook.py 01_quickstart.ipynb")
        sys.exit(1)

    notebook_name = sys.argv[1]
    success = test_notebook(notebook_name)
    sys.exit(0 if success else 1)
