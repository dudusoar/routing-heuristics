"""Data layer visualizations for Routing Heuristics.

This module provides visualizations for VRP data, including maps,
demand distributions, and travel time matrices.
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from .base import BaseVisualizer

try:
    import seaborn as sns
    SEABORN_AVAILABLE = True
except ImportError:
    SEABORN_AVAILABLE = False


class DataVisualizer(BaseVisualizer):
    """Base class for data visualizations.

    This class provides common visualization methods for VRP data.
    """

    def __init__(self, **kwargs):
        """Initialize data visualizer."""
        super().__init__(**kwargs)

    def visualize(self, data: Any, **kwargs):
        """Create visualization for VRP data.

        Args:
            data: Data to visualize
            **kwargs: Visualization-specific parameters
        """
        raise NotImplementedError("Subclasses must implement visualize method")

    def plot_coordinates(self, coordinates: Dict[int, Tuple[float, float]],
                         node_types: Optional[Dict[int, str]] = None,
                         type_colors: Optional[Dict[str, str]] = None,
                         show_labels: bool = True,
                         title: str = 'Node Coordinates',
                         **kwargs):
        """Plot node coordinates on a 2D map.

        Args:
            coordinates: Dictionary mapping node indices to (x, y) coordinates
            node_types: Dictionary mapping node indices to type labels
            type_colors: Dictionary mapping type labels to colors
            show_labels: Whether to show node labels
            title: Plot title
            **kwargs: Additional plotting parameters
        """
        self.create_figure(figsize=(10, 10))

        if type_colors is None:
            type_colors = {
                'depot': 'red',
                'destination': 'red',
                'charging_station': 'green',
                'restaurant': 'blue',
                'customer': 'orange',
                'apartment': 'blue',
                'university building': 'green',
                'default': 'gray'
            }

        # Group nodes by type if types are provided
        if node_types is not None:
            nodes_by_type = {}
            for node, node_type in node_types.items():
                if node in coordinates:
                    nodes_by_type.setdefault(node_type, []).append(node)

            # Plot each type with its color
            for node_type, nodes in nodes_by_type.items():
                color = type_colors.get(node_type, type_colors['default'])
                node_coords = [coordinates[node] for node in nodes]
                x_coords = [coord[0] for coord in node_coords]
                y_coords = [coord[1] for coord in node_coords]

                self._current_axes.scatter(x_coords, y_coords,
                                          c=color, s=100, alpha=0.7,
                                          label=node_type, edgecolors='black')

                # Add labels if requested
                if show_labels:
                    for node, (x, y) in zip(nodes, node_coords):
                        self._current_axes.annotate(str(node), (x, y),
                                                   xytext=(5, 5),
                                                   textcoords='offset points',
                                                   fontsize=8)
        else:
            # Plot all nodes with the same color
            x_coords = [coord[0] for coord in coordinates.values()]
            y_coords = [coord[1] for coord in coordinates.values()]

            self._current_axes.scatter(x_coords, y_coords,
                                      c='blue', s=100, alpha=0.7,
                                      edgecolors='black')

            # Add labels if requested
            if show_labels:
                for node, (x, y) in coordinates.items():
                    self._current_axes.annotate(str(node), (x, y),
                                               xytext=(5, 5),
                                               textcoords='offset points',
                                               fontsize=8)

        self._current_axes.set_xlabel('X Coordinate')
        self._current_axes.set_ylabel('Y Coordinate')
        self._current_axes.set_title(title)

        if node_types is not None:
            self._add_legend()

        self._add_grid()

    def plot_distance_matrix(self, distance_matrix: np.ndarray,
                             title: str = 'Distance Matrix',
                             show_values: bool = False,
                             **kwargs):
        """Plot distance matrix as a heatmap.

        Args:
            distance_matrix: Square distance matrix
            title: Plot title
            show_values: Whether to show distance values in cells
            **kwargs: Additional plotting parameters
        """
        self.create_figure(figsize=(10, 8))

        if SEABORN_AVAILABLE:
            sns.heatmap(distance_matrix, cmap="YlOrRd", annot=show_values,
                       fmt=".1f", square=True, cbar_kws={'label': 'Distance'})
        else:
            # Fallback to matplotlib
            im = self._current_axes.imshow(distance_matrix, cmap='YlOrRd',
                                          aspect='auto')
            plt.colorbar(im, ax=self._current_axes, label='Distance')

            if show_values:
                for i in range(distance_matrix.shape[0]):
                    for j in range(distance_matrix.shape[1]):
                        text = self._current_axes.text(j, i, f'{distance_matrix[i, j]:.1f}',
                                                      ha="center", va="center",
                                                      color="black", fontsize=8)

        self._current_axes.set_xlabel('Destination Node')
        self._current_axes.set_ylabel('Source Node')
        self._current_axes.set_title(title)


class MapVisualizer(DataVisualizer):
    """Visualizer for map data.

    This class provides specialized visualizations for map data,
    including synthetic and real-world maps.
    """

    def __init__(self, **kwargs):
        """Initialize map visualizer."""
        super().__init__(**kwargs)

    def visualize(self, map_instance: Any,
                  plot_type: str = 'basic',
                  **kwargs):
        """Create visualization for map instance.

        Args:
            map_instance: Map instance to visualize (RealMap or RealDataMap)
            plot_type: Type of visualization ('basic', 'detailed', or 'all')
            **kwargs: Additional visualization parameters
        """
        if plot_type == 'all':
            self.create_figure(figsize=(16, 12), nrows=2, ncols=2)

            # Plot 1: Basic map
            self._plot_basic_map(map_instance, ax=self._current_axes[0, 0], **kwargs)

            # Plot 2: Node type distribution
            self._plot_node_type_distribution(map_instance, ax=self._current_axes[0, 1])

            # Plot 3: Distance matrix
            if hasattr(map_instance, 'distance_matrix'):
                self._plot_distance_matrix(map_instance.distance_matrix,
                                          ax=self._current_axes[1, 0])

            # Plot 4: Node degree distribution
            self._plot_node_degree(map_instance, ax=self._current_axes[1, 1])

            self._current_figure.suptitle(f'Map Analysis: {type(map_instance).__name__}',
                                         fontsize=16)
            plt.tight_layout()

        elif plot_type == 'basic':
            self._plot_basic_map(map_instance, **kwargs)
        elif plot_type == 'detailed':
            self._plot_detailed_map(map_instance, **kwargs)
        else:
            raise ValueError(f"Unknown plot_type: {plot_type}")

    def _plot_basic_map(self, map_instance: Any,
                        ax: Optional[plt.Axes] = None,
                        show_index: bool = True,
                        **kwargs):
        """Plot basic map visualization.

        This method provides backward compatibility with the original
        plot_map methods in RealMap and RealDataMap classes.
        """
        if ax is None:
            self.create_figure(figsize=(10, 10))
            ax = self._current_axes

        # Check map instance type and call appropriate method
        if hasattr(map_instance, 'plot_map'):
            # Use the existing plot_map method if available
            # Note: This would need to be adapted to work with given axes
            print("Using existing plot_map method")
            # For now, we'll implement our own version
            pass

        # Extract coordinates and node types
        coordinates = getattr(map_instance, 'coordinates', {})
        node_type_dict = getattr(map_instance, 'node_type_dict', {})

        if not coordinates:
            ax.text(0.5, 0.5, 'No coordinates available', ha='center', va='center')
            return

        # Plot using base method
        self.plot_coordinates(coordinates, node_type_dict,
                             show_labels=show_index, title='Map Visualization',
                             ax=ax, **kwargs)

        if ax == self._current_axes:
            self.show()

    def _plot_detailed_map(self, map_instance: Any,
                           ax: Optional[plt.Axes] = None,
                           **kwargs):
        """Plot detailed map visualization with additional information."""
        if ax is None:
            self.create_figure(figsize=(12, 10))
            ax = self._current_axes

        # This would be a more detailed version with additional features
        # For now, just call basic map
        self._plot_basic_map(map_instance, ax=ax, **kwargs)

        # Add additional information if available
        if hasattr(map_instance, 'restaurants'):
            ax.text(0.02, 0.98, f'Restaurants: {len(map_instance.restaurants)}',
                   transform=ax.transAxes, fontsize=10,
                   verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        if hasattr(map_instance, 'customers'):
            ax.text(0.02, 0.94, f'Customers: {len(map_instance.customers)}',
                   transform=ax.transAxes, fontsize=10,
                   verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        if ax == self._current_axes:
            self.show()

    def _plot_node_type_distribution(self, map_instance: Any,
                                     ax: Optional[plt.Axes] = None):
        """Plot node type distribution as a bar chart."""
        if ax is None:
            self.create_figure(figsize=(8, 6))
            ax = self._current_axes

        node_type_dict = getattr(map_instance, 'node_type_dict', {})
        if not node_type_dict:
            ax.text(0.5, 0.5, 'No node type data available',
                   ha='center', va='center')
            return

        # Count nodes by type
        from collections import Counter
        type_counts = Counter(node_type_dict.values())

        # Create bar chart
        types = list(type_counts.keys())
        counts = [type_counts[t] for t in types]

        x_pos = np.arange(len(types))
        bars = ax.bar(x_pos, counts, alpha=0.8, color='lightblue')

        # Add value labels
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{count}', ha='center', va='bottom', fontsize=10)

        ax.set_xlabel('Node Type')
        ax.set_ylabel('Count')
        ax.set_title('Node Type Distribution')
        ax.set_xticks(x_pos)
        ax.set_xticklabels(types, rotation=45, ha='right')
        ax.grid(True, alpha=0.3, axis='y')

        if ax == self._current_axes:
            self.show()

    def _plot_node_degree(self, map_instance: Any,
                          ax: Optional[plt.Axes] = None):
        """Plot node degree distribution."""
        if ax is None:
            self.create_figure(figsize=(8, 6))
            ax = self._current_axes

        if not hasattr(map_instance, 'distance_matrix'):
            ax.text(0.5, 0.5, 'No distance matrix available',
                   ha='center', va='center')
            return

        # Calculate node degrees (non-zero connections)
        distance_matrix = map_instance.distance_matrix
        degrees = np.sum(distance_matrix > 0, axis=1)

        # Create histogram
        ax.hist(degrees, bins=20, alpha=0.7, color='lightgreen',
               edgecolor='black')
        ax.set_xlabel('Node Degree (Number of Connections)')
        ax.set_ylabel('Frequency')
        ax.set_title('Node Degree Distribution')
        ax.grid(True, alpha=0.3)

        # Add statistics
        ax.text(0.02, 0.98, f'Mean: {degrees.mean():.1f}\nStd: {degrees.std():.1f}',
               transform=ax.transAxes, fontsize=10,
               verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        if ax == self._current_axes:
            self.show()


class DemandVisualizer(DataVisualizer):
    """Visualizer for demand data.

    This class provides specialized visualizations for demand data,
    including heatmaps and time series analysis.
    """

    def __init__(self, **kwargs):
        """Initialize demand visualizer."""
        super().__init__(**kwargs)

    def visualize(self, demand_data: Any,
                  plot_type: str = 'heatmap',
                  **kwargs):
        """Create visualization for demand data.

        Args:
            demand_data: Demand data to visualize (DemandGenerator or DataFrame)
            plot_type: Type of visualization ('heatmap', 'timeseries', or 'all')
            **kwargs: Additional visualization parameters
        """
        if plot_type == 'all':
            self.create_figure(figsize=(16, 12), nrows=2, ncols=2)

            # Plot 1: Heatmap
            self._plot_demand_heatmap(demand_data, ax=self._current_axes[0, 0], **kwargs)

            # Plot 2: Time series
            self._plot_demand_timeseries(demand_data, ax=self._current_axes[0, 1])

            # Plot 3: Distribution
            self._plot_demand_distribution(demand_data, ax=self._current_axes[1, 0])

            # Plot 4: Cumulative demand
            self._plot_cumulative_demand(demand_data, ax=self._current_axes[1, 1])

            self._current_figure.suptitle('Demand Data Analysis', fontsize=16)
            plt.tight_layout()

        elif plot_type == 'heatmap':
            self._plot_demand_heatmap(demand_data, **kwargs)
        elif plot_type == 'timeseries':
            self._plot_demand_timeseries(demand_data, **kwargs)
        else:
            raise ValueError(f"Unknown plot_type: {plot_type}")

    def _plot_demand_heatmap(self, demand_data: Any,
                             ax: Optional[plt.Axes] = None,
                             **kwargs):
        """Plot demand heatmap.

        This method provides backward compatibility with the original
        plot_demand_heatmap method in DemandGenerator class.
        """
        if ax is None:
            self.create_figure(figsize=(12, 8))
            ax = self._current_axes

        # Extract demand table
        if hasattr(demand_data, 'demand_table'):
            demand_table = demand_data.demand_table
        elif isinstance(demand_data, pd.DataFrame):
            demand_table = demand_data
        else:
            ax.text(0.5, 0.5, 'No demand table available',
                   ha='center', va='center')
            return

        # Extract numerical data (skip first two columns if they contain identifiers)
        if len(demand_table.columns) > 2:
            # Assume first two columns are identifiers
            heatmap_data = demand_table.iloc[:, 2:]
            row_labels = demand_table.iloc[:, 0].astype(str) + '-' + demand_table.iloc[:, 1].astype(str)
        else:
            heatmap_data = demand_table
            row_labels = [f'Row {i}' for i in range(len(demand_table))]

        if SEABORN_AVAILABLE:
            sns.heatmap(heatmap_data, cmap="YlOrRd", annot=True, fmt="d",
                       ax=ax, cbar_kws={'label': 'Demand'})
            ax.set_yticklabels(row_labels, rotation=0)
        else:
            # Fallback to matplotlib
            im = ax.imshow(heatmap_data.values, cmap='YlOrRd', aspect='auto')
            plt.colorbar(im, ax=ax, label='Demand')

            # Add value labels
            for i in range(heatmap_data.shape[0]):
                for j in range(heatmap_data.shape[1]):
                    ax.text(j, i, f'{heatmap_data.iloc[i, j]:.0f}',
                           ha="center", va="center", color="black", fontsize=8)

            ax.set_yticks(range(len(row_labels)))
            ax.set_yticklabels(row_labels)

        ax.set_xlabel('Time Intervals')
        ax.set_ylabel('Restaurant-Customer Pairs')
        ax.set_title('Demand Heatmap')

        if ax == self._current_axes:
            self.show()

    def _plot_demand_timeseries(self, demand_data: Any,
                                ax: Optional[plt.Axes] = None):
        """Plot demand time series."""
        if ax is None:
            self.create_figure(figsize=(12, 6))
            ax = self._current_axes

        # Extract demand table
        if hasattr(demand_data, 'demand_table'):
            demand_table = demand_data.demand_table
        elif isinstance(demand_data, pd.DataFrame):
            demand_table = demand_data
        else:
            ax.text(0.5, 0.5, 'No demand table available',
                   ha='center', va='center')
            return

        # Extract numerical data
        if len(demand_table.columns) > 2:
            # Assume first two columns are identifiers
            time_series_data = demand_table.iloc[:, 2:]
            pair_labels = demand_table.iloc[:, 0].astype(str) + '-' + demand_table.iloc[:, 1].astype(str)
        else:
            time_series_data = demand_table
            pair_labels = [f'Pair {i}' for i in range(len(demand_table))]

        # Plot each pair as a line
        time_intervals = range(time_series_data.shape[1])
        colors = self._get_color_cycle(len(pair_labels))

        for i, (label, row) in enumerate(zip(pair_labels, time_series_data.itertuples(index=False))):
            if isinstance(row, tuple):
                # Convert namedtuple or regular tuple to list
                values = list(row)
            else:
                values = row

            ax.plot(time_intervals, values, color=colors[i],
                   linewidth=2, alpha=0.7, label=label)

        ax.set_xlabel('Time Interval')
        ax.set_ylabel('Demand')
        ax.set_title('Demand Time Series')
        ax.legend(loc='best', fontsize=8)
        ax.grid(True, alpha=0.3)

        if ax == self._current_axes:
            self.show()

    def _plot_demand_distribution(self, demand_data: Any,
                                  ax: Optional[plt.Axes] = None):
        """Plot demand distribution histogram."""
        if ax is None:
            self.create_figure(figsize=(8, 6))
            ax = self._current_axes

        # Extract all demand values
        if hasattr(demand_data, 'demand_table'):
            demand_table = demand_data.demand_table
        elif isinstance(demand_data, pd.DataFrame):
            demand_table = demand_data
        else:
            ax.text(0.5, 0.5, 'No demand table available',
                   ha='center', va='center')
            return

        # Flatten all demand values
        if len(demand_table.columns) > 2:
            demand_values = demand_table.iloc[:, 2:].values.flatten()
        else:
            demand_values = demand_table.values.flatten()

        # Remove zeros for better visualization
        demand_values = demand_values[demand_values > 0]

        if len(demand_values) == 0:
            ax.text(0.5, 0.5, 'No non-zero demand values',
                   ha='center', va='center')
            return

        # Create histogram
        ax.hist(demand_values, bins=20, alpha=0.7, color='lightcoral',
               edgecolor='black')
        ax.set_xlabel('Demand Value')
        ax.set_ylabel('Frequency')
        ax.set_title('Demand Value Distribution')
        ax.grid(True, alpha=0.3)

        # Add statistics
        ax.text(0.02, 0.98, f'Mean: {demand_values.mean():.1f}\nStd: {demand_values.std():.1f}',
               transform=ax.transAxes, fontsize=10,
               verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        if ax == self._current_axes:
            self.show()

    def _plot_cumulative_demand(self, demand_data: Any,
                                ax: Optional[plt.Axes] = None):
        """Plot cumulative demand over time."""
        if ax is None:
            self.create_figure(figsize=(8, 6))
            ax = self._current_axes

        # Extract demand table
        if hasattr(demand_data, 'demand_table'):
            demand_table = demand_data.demand_table
        elif isinstance(demand_data, pd.DataFrame):
            demand_table = demand_data
        else:
            ax.text(0.5, 0.5, 'No demand table available',
                   ha='center', va='center')
            return

        # Calculate cumulative demand
        if len(demand_table.columns) > 2:
            time_series_data = demand_table.iloc[:, 2:]
        else:
            time_series_data = demand_table

        cumulative_demand = time_series_data.sum(axis=0).cumsum()

        # Plot cumulative demand
        time_intervals = range(len(cumulative_demand))
        ax.plot(time_intervals, cumulative_demand, 'b-',
               linewidth=2, marker='o', markersize=4)
        ax.fill_between(time_intervals, 0, cumulative_demand,
                       alpha=0.3, color='blue')

        ax.set_xlabel('Time Interval')
        ax.set_ylabel('Cumulative Demand')
        ax.set_title('Cumulative Demand Over Time')
        ax.grid(True, alpha=0.3)

        if ax == self._current_axes:
            self.show()
