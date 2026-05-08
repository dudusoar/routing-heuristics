"""Problem layer visualizations for Routing Heuristics.

This module provides visualizations for VRP problem solutions, including
route plotting, time window visualizations, and solution quality analysis.
"""

from typing import List, Optional, Dict, Any, Tuple, Union
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict

from .base import BaseVisualizer

try:
    from vrp_toolkit.problems.pdptw import PDPTWSolution
    PDPTW_AVAILABLE = True
except ImportError:
    PDPTW_AVAILABLE = False

try:
    from vrp_toolkit.algorithms.base import VRPSolution, PDPTWSolutionAdapter
    VRP_INTERFACES_AVAILABLE = True
except ImportError:
    VRP_INTERFACES_AVAILABLE = False


class ProblemVisualizer(BaseVisualizer):
    """Base class for problem solution visualizations.

    This class provides common visualization methods for VRP solutions.
    """

    def __init__(self, **kwargs):
        """Initialize problem visualizer."""
        super().__init__(**kwargs)

    def visualize(self, solution: Any, **kwargs):
        """Create visualization for a VRP solution.

        Args:
            solution: VRP solution to visualize
            **kwargs: Visualization-specific parameters
        """
        raise NotImplementedError("Subclasses must implement visualize method")

    def plot_routes(self, routes: List[List[int]], coordinates: Dict[int, Tuple[float, float]],
                    vehicle_ids: Optional[List[int]] = None, **kwargs):
        """Plot vehicle routes on a map.

        Args:
            routes: List of vehicle routes (each route is a list of node indices)
            coordinates: Dictionary mapping node indices to (x, y) coordinates
            vehicle_ids: List of vehicle IDs to plot (default: all vehicles)
            **kwargs: Additional plotting parameters
        """
        self.create_figure()

        if vehicle_ids is None:
            vehicle_ids = list(range(len(routes)))

        # Plot nodes
        node_x = [coord[0] for coord in coordinates.values()]
        node_y = [coord[1] for coord in coordinates.values()]
        self._current_axes.scatter(node_x, node_y, c='black', s=50, alpha=0.7, label='Nodes')

        # Plot routes with different colors
        colors = self._get_color_cycle(len(vehicle_ids))

        for i, vehicle_id in enumerate(vehicle_ids):
            if vehicle_id >= len(routes):
                continue

            route = routes[vehicle_id]
            route_coords = [coordinates.get(node, (0, 0)) for node in route]
            route_x = [coord[0] for coord in route_coords]
            route_y = [coord[1] for coord in route_coords]

            self._current_axes.plot(route_x, route_y, color=colors[i], linewidth=2,
                                    label=f'Vehicle {vehicle_id}', alpha=0.8)

            # Plot direction arrows
            if len(route) > 1:
                for j in range(len(route) - 1):
                    start = route_coords[j]
                    end = route_coords[j + 1]
                    mid_x = (start[0] + end[0]) / 2
                    mid_y = (start[1] + end[1]) / 2
                    dx = end[0] - start[0]
                    dy = end[1] - start[1]

                    # Normalize for arrow length
                    length = np.sqrt(dx**2 + dy**2)
                    if length > 0:
                        dx_norm = dx / length * 0.1
                        dy_norm = dy / length * 0.1
                        self._current_axes.arrow(mid_x - dx_norm/2, mid_y - dy_norm/2,
                                                dx_norm, dy_norm,
                                                head_width=0.05, head_length=0.1,
                                                fc=colors[i], ec=colors[i], alpha=0.6)

        self._current_axes.set_xlabel('X Coordinate')
        self._current_axes.set_ylabel('Y Coordinate')
        self.set_title('Vehicle Routes')
        self._add_legend()
        self._add_grid()

    def plot_time_windows(self, time_windows: Dict[int, Tuple[float, float]],
                          arrival_times: Optional[Dict[int, float]] = None,
                          **kwargs):
        """Plot time window constraints and arrival times.

        Args:
            time_windows: Dictionary mapping node indices to (start_time, end_time)
            arrival_times: Dictionary mapping node indices to arrival times
            **kwargs: Additional plotting parameters
        """
        self.create_figure(figsize=(12, 6))

        nodes = list(time_windows.keys())
        indices = range(len(nodes))

        # Plot time windows as horizontal bars
        for i, node in enumerate(nodes):
            start, end = time_windows[node]
            self._current_axes.barh(i, end - start, left=start, height=0.6,
                                    alpha=0.5, color='lightblue', edgecolor='black')

            # Plot arrival times if available
            if arrival_times and node in arrival_times:
                arrival = arrival_times[node]
                self._current_axes.plot(arrival, i, 'ro', markersize=8,
                                        label='Arrival Time' if i == 0 else '')

        self._current_axes.set_yticks(indices)
        self._current_axes.set_yticklabels([f'Node {node}' for node in nodes])
        self._current_axes.set_xlabel('Time')
        self._current_axes.set_ylabel('Nodes')
        self.set_title('Time Windows and Arrival Times')

        if arrival_times:
            self._add_legend()

        self._add_grid()


class PDPTWVisualizer(ProblemVisualizer):
    """Visualizer for PDPTW solutions.

    This class provides specialized visualizations for PDPTW solutions,
    including pickup-delivery pairs and charging station visits.
    """

    def __init__(self, **kwargs):
        """Initialize PDPTW visualizer."""
        super().__init__(**kwargs)

    def visualize(self, solution: Union['PDPTWSolution', 'VRPSolution'], vehicle_ids: Optional[List[int]] = None,
                  show_labels: bool = True, **kwargs):
        """Create comprehensive visualization for PDPTW solution.

        This method creates a 2x2 grid of visualizations:
        1. Route map with pickup-delivery connections
        2. Time window compliance
        3. Vehicle load over time
        4. Battery usage over time

        Args:
            solution: PDPTW solution to visualize (PDPTWSolution or VRPSolution adapter)
            vehicle_ids: List of vehicle IDs to plot (default: all selected vehicles)
            show_labels: Whether to show node labels on the route map
            **kwargs: Additional visualization parameters
        """
        # Handle VRPSolution adapter if provided
        if VRP_INTERFACES_AVAILABLE and isinstance(solution, VRPSolution):
            # Try to extract original PDPTWSolution from adapter
            if hasattr(solution, 'original_solution'):
                solution = solution.original_solution
            else:
                # If not an adapter, we cannot visualize generic VRPSolution
                raise TypeError(
                    f"PDPTWVisualizer requires PDPTWSolution or PDPTWSolutionAdapter. "
                    f"Got {type(solution).__name__}"
                )

        # Check if we have a valid PDPTWSolution
        if not PDPTW_AVAILABLE or not isinstance(solution, PDPTWSolution):
            raise TypeError(
                f"PDPTWVisualizer requires PDPTWSolution. Got {type(solution).__name__}"
            )

        # Create 2x2 subplot grid
        self.create_figure(figsize=(16, 12), nrows=2, ncols=2)

        # Plot 1: Route map
        self._plot_route_map(solution, vehicle_ids, show_labels,
                             ax=self._current_axes[0, 0])

        # Plot 2: Time window compliance
        self._plot_time_compliance(solution, vehicle_ids,
                                   ax=self._current_axes[0, 1])

        # Plot 3: Vehicle load over time
        self._plot_vehicle_load(solution, vehicle_ids,
                                ax=self._current_axes[1, 0])

        # Plot 4: Battery usage over time
        self._plot_battery_usage(solution, vehicle_ids,
                                 ax=self._current_axes[1, 1])

        self._current_figure.suptitle('PDPTW Solution Analysis', fontsize=16)
        plt.tight_layout()

    def _plot_route_map(self, solution: Union['PDPTWSolution', 'VRPSolution'],
                        vehicle_ids: Optional[List[int]],
                        show_labels: bool,
                        ax: plt.Axes):
        """Plot route map with pickup-delivery connections.

        This method replicates the functionality of the original plot_solution
        method but with improved organization and optional enhancements.
        """
        instance = solution.instance

        # Get selected vehicles
        selected_vehicles = solution.get_selected_vehicles()
        if not selected_vehicles:
            ax.text(0.5, 0.5, 'No selected vehicles', ha='center', va='center')
            return

        if vehicle_ids is None:
            vehicle_ids = selected_vehicles
        else:
            vehicle_ids = [vid for vid in vehicle_ids if vid in selected_vehicles]

        if not vehicle_ids:
            ax.text(0.5, 0.5, 'No valid vehicle IDs', ha='center', va='center')
            return

        # Create location-order mapping
        location_orders = defaultdict(list)
        for order_id in range(1, instance.n + 1):
            pickup_coord = instance.pickup_points[order_id - 1]
            delivery_coord = instance.delivery_points[order_id - 1]
            location_orders[pickup_coord].append(f"P{order_id}")
            location_orders[delivery_coord].append(f"D{order_id}")

        # Plot nodes
        ax.scatter(instance.depot[0], instance.depot[1],
                  c='red', marker='s', s=100, label='Depot')
        ax.scatter([p[0] for p in instance.pickup_points],
                  [p[1] for p in instance.pickup_points],
                  c='blue', marker='o', s=100, label='Pickup')
        ax.scatter([d[0] for d in instance.delivery_points],
                  [d[1] for d in instance.delivery_points],
                  c='green', marker='d', s=100, label='Delivery')

        if instance.charging != instance.depot:
            ax.scatter(instance.charging[0], instance.charging[1],
                      c='purple', marker='^', s=100, label='Charging Station')

        # Add labels if requested
        if show_labels:
            ax.annotate('Depot', (instance.depot[0], instance.depot[1]),
                       textcoords='offset points', xytext=(0, 10), ha='center')

            for location, orders in location_orders.items():
                label = ', '.join(orders)
                ax.annotate(f"[{label}]", (location[0], location[1]),
                           textcoords='offset points', xytext=(0, 5),
                           ha='center', fontsize=8)

        # Plot routes with different colors
        colors = plt.cm.get_cmap('viridis', len(vehicle_ids))
        for i, vehicle_id in enumerate(vehicle_ids):
            route = solution.routes[vehicle_id]
            color = colors(i)

            route_points = [instance.depot]
            for node in route[1:-1]:
                if node <= instance.n:
                    route_points.append(instance.pickup_points[node - 1])
                elif node <= 2 * instance.n:
                    route_points.append(instance.delivery_points[node - instance.n - 1])
                else:
                    route_points.append(instance.charging)
            route_points.append(instance.depot)

            route_x = [point[0] for point in route_points]
            route_y = [point[1] for point in route_points]

            ax.plot(route_x, route_y, color=color, linestyle='-',
                   linewidth=1.5, alpha=0.8, label=f'Vehicle {vehicle_id + 1}')

        ax.set_xlabel('X coordinate')
        ax.set_ylabel('Y coordinate')
        ax.set_title('Route Map')
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)

    def _plot_time_compliance(self, solution: Union['PDPTWSolution', 'VRPSolution'],
                              vehicle_ids: Optional[List[int]],
                              ax: plt.Axes):
        """Plot time window compliance for each vehicle."""
        # This is a placeholder - actual implementation would need access to
        # arrival times and time window data from the solution
        ax.text(0.5, 0.5, 'Time Compliance Plot\n(Implementation pending)',
                ha='center', va='center', transform=ax.transAxes)
        ax.set_title('Time Window Compliance')
        ax.set_xlabel('Node Index')
        ax.set_ylabel('Time')
        ax.grid(True, alpha=0.3)

    def _plot_vehicle_load(self, solution: Union['PDPTWSolution', 'VRPSolution'],
                           vehicle_ids: Optional[List[int]],
                           ax: plt.Axes):
        """Plot vehicle load over time for each vehicle."""
        # This is a placeholder - actual implementation would need access to
        # load data over time from the solution
        ax.text(0.5, 0.5, 'Vehicle Load Plot\n(Implementation pending)',
                ha='center', va='center', transform=ax.transAxes)
        ax.set_title('Vehicle Load Over Time')
        ax.set_xlabel('Time')
        ax.set_ylabel('Load')
        ax.grid(True, alpha=0.3)

    def _plot_battery_usage(self, solution: Union['PDPTWSolution', 'VRPSolution'],
                            vehicle_ids: Optional[List[int]],
                            ax: plt.Axes):
        """Plot battery usage over time for each vehicle."""
        # This is a placeholder - actual implementation would need access to
        # battery data over time from the solution
        ax.text(0.5, 0.5, 'Battery Usage Plot\n(Implementation pending)',
                ha='center', va='center', transform=ax.transAxes)
        ax.set_title('Battery Usage Over Time')
        ax.set_xlabel('Time')
        ax.set_ylabel('Battery Level')
        ax.grid(True, alpha=0.3)

    # Backward compatibility method
    def plot_solution(self, solution: Union['PDPTWSolution', 'VRPSolution'],
                      vehicle_ids: Optional[List[int]] = None,
                      show_labels: bool = True):
        """Plot solution routes (backward compatibility).

        This method provides backward compatibility with the original
        plot_solution method in PDPTWSolution class.

        Args:
            solution: PDPTW solution to plot (PDPTWSolution or VRPSolution adapter)
            vehicle_ids: List of vehicle IDs to plot (default: all selected vehicles)
            show_labels: Whether to show node labels
        """
        # Handle VRPSolution adapter if provided
        if VRP_INTERFACES_AVAILABLE and isinstance(solution, VRPSolution):
            # Try to extract original PDPTWSolution from adapter
            if hasattr(solution, 'original_solution'):
                solution = solution.original_solution
            else:
                # If not an adapter, we cannot visualize generic VRPSolution
                raise TypeError(
                    f"PDPTWVisualizer.plot_solution requires PDPTWSolution or PDPTWSolutionAdapter. "
                    f"Got {type(solution).__name__}"
                )

        # Check if we have a valid PDPTWSolution
        if not PDPTW_AVAILABLE or not isinstance(solution, PDPTWSolution):
            raise TypeError(
                f"PDPTWVisualizer.plot_solution requires PDPTWSolution. Got {type(solution).__name__}"
            )

        self.create_figure(figsize=(12, 10))
        self._plot_route_map(solution, vehicle_ids, show_labels, ax=self._current_axes)
        self.set_title('PDPTW Solution')
        self.show()
