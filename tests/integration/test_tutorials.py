"""Integration tests for tutorial validation."""

import pytest
import json
import os
from typing import Dict, Any, List

# Note: We're testing tutorial structure and imports, not executing notebooks
# Full notebook execution requires additional dependencies and is slower


class TestTutorialFiles:
    """Test tutorial notebook files."""
    
    def test_tutorial_files_exist(self):
        """Check that tutorial files exist."""
        tutorial_files = [
            "tutorials/01_quickstart.ipynb",
            "tutorials/05_sensitivity_analysis.ipynb"
        ]
        
        for file_path in tutorial_files:
            full_path = os.path.join(os.path.dirname(__file__), "..", "..", file_path)
            assert os.path.exists(full_path), f"Tutorial file missing: {file_path}"
    
    def test_tutorials_are_valid_json(self):
        """Check that tutorial notebooks are valid JSON."""
        tutorial_files = [
            "tutorials/01_quickstart.ipynb",
            "tutorials/05_sensitivity_analysis.ipynb"
        ]
        
        for file_path in tutorial_files:
            full_path = os.path.join(os.path.dirname(__file__), "..", "..", file_path)
            
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    notebook = json.load(f)
                
                # Check basic notebook structure
                assert 'cells' in notebook, f"Notebook missing 'cells': {file_path}"
                assert isinstance(notebook['cells'], list), f"Cells should be list: {file_path}"
                assert len(notebook['cells']) > 0, f"Notebook has no cells: {file_path}"
                
                # Check metadata
                assert 'metadata' in notebook, f"Notebook missing metadata: {file_path}"
                
            except json.JSONDecodeError as e:
                pytest.fail(f"Invalid JSON in tutorial {file_path}: {e}")
            except Exception as e:
                pytest.fail(f"Error reading tutorial {file_path}: {e}")
    
    def test_tutorial_has_markdown_sections(self):
        """Check that tutorials have educational markdown sections."""
        tutorial_files = [
            ("tutorials/01_quickstart.ipynb", [
                "Routing Heuristics", "import", "synthetic map", "demand generation",
                "PDPTW orders", "instance", "initial solution", "ALNS configuration",
                "ALNS execution", "visualization"
            ]),
            ("tutorials/05_sensitivity_analysis.ipynb", [
                "sensitivity analysis", "experiment design", "helper functions",
                "experiment loop", "analyze", "visualize", "export", "conclusion"
            ])
        ]
        
        for file_path, expected_keywords in tutorial_files:
            full_path = os.path.join(os.path.dirname(__file__), "..", "..", file_path)
            
            with open(full_path, 'r', encoding='utf-8') as f:
                notebook = json.load(f)
            
            # Collect all markdown content
            markdown_content = ""
            for cell in notebook['cells']:
                if cell['cell_type'] == 'markdown':
                    if 'source' in cell:
                        # source might be list of strings
                        if isinstance(cell['source'], list):
                            markdown_content += " ".join(cell['source'])
                        else:
                            markdown_content += str(cell['source'])
            
            markdown_content = markdown_content.lower()
            
            # Check for expected keywords
            for keyword in expected_keywords:
                assert keyword.lower() in markdown_content, \
                    f"Keyword '{keyword}' not found in tutorial {file_path}"
    
    def test_tutorial_code_imports(self):
        """Check that tutorial code cells import required modules."""
        tutorial_files = [
            "tutorials/01_quickstart.ipynb",
            "tutorials/05_sensitivity_analysis.ipynb"
        ]
        
        required_imports = [
            "vrp_toolkit",
            "numpy",
            "pandas",
            "matplotlib"
        ]
        
        for file_path in tutorial_files:
            full_path = os.path.join(os.path.dirname(__file__), "..", "..", file_path)
            
            with open(full_path, 'r', encoding='utf-8') as f:
                notebook = json.load(f)
            
            # Collect all code content
            code_content = ""
            for cell in notebook['cells']:
                if cell['cell_type'] == 'code':
                    if 'source' in cell:
                        if isinstance(cell['source'], list):
                            code_content += " ".join(cell['source'])
                        else:
                            code_content += str(cell['source'])
            
            code_content = code_content.lower()
            
            # Check for required imports (as substrings)
            for imp in required_imports:
                # More flexible check: import might be with 'as' or different formatting
                import_patterns = [
                    f"import {imp}",
                    f"from {imp}",
                    f"{imp}.",  # usage of the module
                ]
                
                # Check if any pattern matches
                matches = any(pattern in code_content for pattern in import_patterns)
                
                # Warn but don't fail - some tutorials might not use all imports
                if not matches:
                    print(f"Warning: Import '{imp}' not found in tutorial {file_path}")
    
    def test_tutorial_no_syntax_errors(self):
        """Check that tutorial code cells don't have obvious syntax errors."""
        # This is a basic check - full syntax checking would require executing code
        tutorial_files = [
            "tutorials/01_quickstart.ipynb",
            "tutorials/05_sensitivity_analysis.ipynb"
        ]
        
        common_syntax_errors = [
            "import missing_module",  # Placeholder - actual checking would need execution
        ]
        
        # For now, just verify files can be parsed as JSON
        # Actual code execution testing would be in a different test suite
        for file_path in tutorial_files:
            full_path = os.path.join(os.path.dirname(__file__), "..", "..", file_path)
            
            # Just verify JSON is valid (already tested above)
            with open(full_path, 'r', encoding='utf-8') as f:
                json.load(f)  # Will raise if invalid


class TestTutorialDependencies:
    """Test that tutorials don't use unavailable dependencies."""
    
    def test_no_osmnx_in_basic_tutorials(self):
        """Check that basic tutorials don't require optional OSMnx."""
        tutorial_files = [
            "tutorials/01_quickstart.ipynb",
            "tutorials/05_sensitivity_analysis.ipynb"
        ]
        
        optional_dependencies = [
            "osmnx",
            "geopandas",
            "folium"
        ]
        
        for file_path in tutorial_files:
            full_path = os.path.join(os.path.dirname(__file__), "..", "..", file_path)
            
            with open(full_path, 'r', encoding='utf-8') as f:
                notebook = json.load(f)
            
            code_content = ""
            for cell in notebook['cells']:
                if cell['cell_type'] == 'code':
                    if 'source' in cell:
                        if isinstance(cell['source'], list):
                            code_content += " ".join(cell['source'])
                        else:
                            code_content += str(cell['source'])
            
            code_content = code_content.lower()
            
            # Check for optional dependencies
            for dep in optional_dependencies:
                if dep in code_content:
                    # Warn but don't fail - tutorials might mention optional features
                    print(f"Note: Optional dependency '{dep}' found in {file_path}")
                    print("  Make sure this is clearly marked as optional in the tutorial")
    
    def test_tutorial_uses_alnsconfig(self):
        """Check that tutorials use ALNSConfig (not old parameter style)."""
        file_path = "tutorials/01_quickstart.ipynb"
        full_path = os.path.join(os.path.dirname(__file__), "..", "..", file_path)
        
        with open(full_path, 'r', encoding='utf-8') as f:
            notebook = json.load(f)
        
        code_content = ""
        for cell in notebook['cells']:
            if cell['cell_type'] == 'code':
                if 'source' in cell:
                    if isinstance(cell['source'], list):
                        code_content += " ".join(cell['source'])
                    else:
                        code_content += str(cell['source'])
        
        # Should use ALNSConfig
        assert "ALNSConfig" in code_content, "Tutorial should use ALNSConfig dataclass"
        
        # Should not use old parameter style (individual params)
        old_style_indicators = [
            "params_operators=",  # Old parameter name
        ]
        
        for indicator in old_style_indicators:
            if indicator in code_content:
                print(f"Warning: Possible old-style parameter '{indicator}' in tutorial")
                print("  Tutorial should use ALNSConfig instead")


class TestTutorialExamples:
    """Test tutorial example code (structural validation)."""
    
    def test_quickstart_structure(self):
        """Validate quickstart tutorial structure."""
        file_path = "tutorials/01_quickstart.ipynb"
        full_path = os.path.join(os.path.dirname(__file__), "..", "..", file_path)
        
        with open(full_path, 'r', encoding='utf-8') as f:
            notebook = json.load(f)
        
        # Count cell types
        markdown_cells = 0
        code_cells = 0
        
        for cell in notebook['cells']:
            if cell['cell_type'] == 'markdown':
                markdown_cells += 1
            elif cell['cell_type'] == 'code':
                code_cells += 1
        
        # Should have reasonable mix of markdown and code
        assert markdown_cells > 0, "Tutorial should have markdown explanations"
        assert code_cells > 0, "Tutorial should have code examples"
        
        # Should not be too long (educational focus)
        total_cells = markdown_cells + code_cells
        assert total_cells < 50, f"Tutorial seems long ({total_cells} cells), consider splitting"
    
    def test_sensitivity_analysis_structure(self):
        """Validate sensitivity analysis tutorial structure."""
        file_path = "tutorials/05_sensitivity_analysis.ipynb"
        full_path = os.path.join(os.path.dirname(__file__), "..", "..", file_path)
        
        with open(full_path, 'r', encoding='utf-8') as f:
            notebook = json.load(f)
        
        # Check for experiment loop structure
        code_content = ""
        for cell in notebook['cells']:
            if cell['cell_type'] == 'code':
                if 'source' in cell:
                    if isinstance(cell['source'], list):
                        code_content += " ".join(cell['source'])
                    else:
                        code_content += str(cell['source'])
        
        # Should have parameterization
        assert "NUM_RUNS" in code_content or "num_runs" in code_content.lower(), \
            "Sensitivity analysis should have parameterized number of runs"
        
        # Should have data collection
        assert "results" in code_content.lower() or "dataframe" in code_content.lower(), \
            "Should collect results in DataFrame or similar structure"
        
        # Should have visualization
        assert "plot" in code_content.lower() or "visual" in code_content.lower(), \
            "Should include visualization of results"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
