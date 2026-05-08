"""Base visualization classes for Routing Heuristics.

This module provides abstract base classes and utility functions for creating
consistent and reusable visualizations across Routing Heuristics.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List, Tuple
import matplotlib.pyplot as plt
import numpy as np


class BaseVisualizer(ABC):
    """Abstract base class for all visualizers.

    This class defines the common interface for visualizers and provides
    utility methods for creating consistent visualizations.
    """

    def __init__(self, title: Optional[str] = None, figsize: Tuple[int, int] = (12, 8)):
        """Initialize base visualizer.

        Args:
            title: Default title for visualizations
            figsize: Default figure size (width, height) in inches
        """
        self.title = title
        self.figsize = figsize
        self._current_figure = None
        self._current_axes = None

    def create_figure(self, figsize: Optional[Tuple[int, int]] = None,
                      nrows: int = 1, ncols: int = 1, **kwargs) -> plt.Figure:
        """Create a new figure with specified dimensions.

        Args:
            figsize: Figure size (width, height) in inches
            nrows: Number of rows for subplots
            ncols: Number of columns for subplots
            **kwargs: Additional arguments passed to plt.subplots()

        Returns:
            matplotlib Figure object
        """
        if figsize is None:
            figsize = self.figsize

        self._current_figure, self._current_axes = plt.subplots(
            nrows=nrows, ncols=ncols, figsize=figsize, **kwargs
        )
        return self._current_figure

    def set_title(self, title: Optional[str] = None):
        """Set figure title.

        Args:
            title: Title for the figure (uses default if None)
        """
        if title is None:
            title = self.title

        if self._current_figure is not None and title:
            if isinstance(self._current_axes, np.ndarray):
                # For subplots, set title on the first axes
                self._current_axes.flat[0].set_title(title)
            else:
                self._current_axes.set_title(title)

    def show(self):
        """Display the current figure."""
        if self._current_figure is not None:
            plt.tight_layout()
            plt.show()

    def save(self, filename: str, dpi: int = 300, **kwargs):
        """Save the current figure to file.

        Args:
            filename: Path to save the figure
            dpi: Resolution in dots per inch
            **kwargs: Additional arguments passed to plt.savefig()
        """
        if self._current_figure is not None:
            plt.savefig(filename, dpi=dpi, bbox_inches='tight', **kwargs)

    def close(self):
        """Close the current figure."""
        if self._current_figure is not None:
            plt.close(self._current_figure)
            self._current_figure = None
            self._current_axes = None

    @abstractmethod
    def visualize(self, data: Any, **kwargs):
        """Create visualization for given data.

        Args:
            data: Data to visualize
            **kwargs: Visualization-specific parameters
        """
        pass

    def _get_color_cycle(self, n_colors: int) -> List[str]:
        """Get a color cycle for plotting multiple items.

        Args:
            n_colors: Number of distinct colors needed

        Returns:
            List of color strings
        """
        cmap = plt.cm.get_cmap('viridis', n_colors)
        return [cmap(i) for i in range(n_colors)]

    def _add_legend(self, location: str = 'best', fontsize: int = 10):
        """Add legend to current axes.

        Args:
            location: Legend location
            fontsize: Legend font size
        """
        if self._current_axes is not None:
            if isinstance(self._current_axes, np.ndarray):
                # For subplots, add legend to the first axes
                self._current_axes.flat[0].legend(loc=location, fontsize=fontsize)
            else:
                self._current_axes.legend(loc=location, fontsize=fontsize)

    def _add_grid(self, alpha: float = 0.3):
        """Add grid to current axes.

        Args:
            alpha: Grid transparency (0-1)
        """
        if self._current_axes is not None:
            if isinstance(self._current_axes, np.ndarray):
                for ax in self._current_axes.flat:
                    ax.grid(True, alpha=alpha)
            else:
                self._current_axes.grid(True, alpha=alpha)


class InteractiveVisualizer(BaseVisualizer):
    """Base class for interactive visualizations.

    This class extends BaseVisualizer with interactive capabilities
    and widget support for Jupyter notebooks.
    """

    def __init__(self, **kwargs):
        """Initialize interactive visualizer."""
        super().__init__(**kwargs)
        self._widgets = {}

    def add_slider(self, name: str, min_val: float, max_val: float,
                   default: float, description: str = ''):
        """Add an interactive slider widget.

        Args:
            name: Widget name (used as key)
            min_val: Minimum value
            max_val: Maximum value
            default: Default value
            description: Widget description
        """
        try:
            from ipywidgets import FloatSlider
            self._widgets[name] = FloatSlider(
                value=default,
                min=min_val,
                max=max_val,
                step=(max_val - min_val) / 100,
                description=description,
                continuous_update=False
            )
        except ImportError:
            print("ipywidgets not installed. Install with: pip install ipywidgets")

    def add_dropdown(self, name: str, options: List[str],
                     default: str, description: str = ''):
        """Add an interactive dropdown widget.

        Args:
            name: Widget name (used as key)
            options: List of available options
            default: Default option
            description: Widget description
        """
        try:
            from ipywidgets import Dropdown
            self._widgets[name] = Dropdown(
                options=options,
                value=default,
                description=description
            )
        except ImportError:
            print("ipywidgets not installed. Install with: pip install ipywidgets")

    def get_widgets(self) -> Dict[str, Any]:
        """Get all registered widgets.

        Returns:
            Dictionary of widget names to widget objects
        """
        return self._widgets
