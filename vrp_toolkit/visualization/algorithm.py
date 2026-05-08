"""Algorithm layer visualizations for Routing Heuristics.

This module provides visualizations for algorithm performance, including
operator statistics, convergence plots, and solution history analysis.
"""

from typing import List, Optional, Dict, Any, Tuple
import numpy as np
import matplotlib.pyplot as plt

from .base import BaseVisualizer


class AlgorithmVisualizer(BaseVisualizer):
    """Base class for algorithm visualizations.

    This class provides common visualization methods for algorithm performance
    and statistics.
    """

    def __init__(self, **kwargs):
        """Initialize algorithm visualizer."""
        super().__init__(**kwargs)

    def visualize(self, algorithm: Any, **kwargs):
        """Create visualization for an algorithm instance.

        Args:
            algorithm: Algorithm instance to visualize
            **kwargs: Visualization-specific parameters
        """
        raise NotImplementedError("Subclasses must implement visualize method")

    def plot_convergence(self, objective_values: List[float],
                         best_values: Optional[List[float]] = None,
                         title: str = 'Algorithm Convergence',
                         **kwargs):
        """Plot algorithm convergence over iterations.

        Args:
            objective_values: List of objective values over iterations
            best_values: List of best objective values found so far
            title: Plot title
            **kwargs: Additional plotting parameters
        """
        self.create_figure(figsize=(12, 6))

        iterations = range(len(objective_values))
        self._current_axes.plot(iterations, objective_values, 'b-',
                               linewidth=1, alpha=0.7, label='Current Objective')

        if best_values is not None and len(best_values) == len(objective_values):
            self._current_axes.plot(iterations, best_values, 'r-',
                                   linewidth=2, label='Best Objective')

        self._current_axes.set_xlabel('Iteration')
        self._current_axes.set_ylabel('Objective Value')
        self._current_axes.set_title(title)
        self._add_legend()
        self._add_grid()

        # Add horizontal line for final best value
        if objective_values:
            final_best = min(objective_values) if best_values is None else min(best_values)
            self._current_axes.axhline(y=final_best, color='g', linestyle='--',
                                      alpha=0.5, label=f'Final Best: {final_best:.2f}')
            self._add_legend()

    def plot_solution_history(self, solution_history: List[Tuple[Any, float]],
                              title: str = 'Solution History',
                              **kwargs):
        """Plot solution history from algorithm.

        Args:
            solution_history: List of (solution, objective_value) pairs
            title: Plot title
            **kwargs: Additional plotting parameters
        """
        if not solution_history:
            print("No solution history to plot")
            return

        objectives = [obj for _, obj in solution_history]
        self.plot_convergence(objectives, title=title, **kwargs)

    def plot_operator_performance(self, operator_names: List[str],
                                  scores: List[float],
                                  usage_counts: Optional[List[int]] = None,
                                  title: str = 'Operator Performance',
                                  **kwargs):
        """Plot operator performance metrics.

        Args:
            operator_names: List of operator names
            scores: List of operator scores
            usage_counts: List of operator usage counts (optional)
            title: Plot title
            **kwargs: Additional plotting parameters
        """
        self.create_figure(figsize=(12, 6))

        x_pos = np.arange(len(operator_names))
        width = 0.35

        if usage_counts is not None:
            # Plot both scores and usage counts
            ax1 = self._current_axes
            ax2 = ax1.twinx()

            bars1 = ax1.bar(x_pos - width/2, scores, width, alpha=0.8,
                           color='lightblue', label='Scores')
            bars2 = ax2.bar(x_pos + width/2, usage_counts, width, alpha=0.8,
                           color='lightcoral', label='Usage Counts')

            ax1.set_xlabel('Operators')
            ax1.set_ylabel('Scores', color='blue')
            ax2.set_ylabel('Usage Counts', color='red')

            ax1.tick_params(axis='y', labelcolor='blue')
            ax2.tick_params(axis='y', labelcolor='red')

            # Add value labels on bars
            for bar in bars1:
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.1f}', ha='center', va='bottom',
                        fontsize=8)

            for bar in bars2:
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height}', ha='center', va='bottom',
                        fontsize=8)

            # Combine legends
            lines1, labels1 = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

        else:
            # Plot only scores
            bars = self._current_axes.bar(x_pos, scores, alpha=0.8,
                                         color='lightblue')
            self._current_axes.set_xlabel('Operators')
            self._current_axes.set_ylabel('Scores')

            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                self._current_axes.text(bar.get_x() + bar.get_width()/2., height,
                                       f'{height:.1f}', ha='center', va='bottom',
                                       fontsize=10)

        self._current_axes.set_xticks(x_pos)
        self._current_axes.set_xticklabels(operator_names, rotation=45, ha='right')
        self._current_axes.set_title(title)
        self._add_grid()


class ALNSVisualizer(AlgorithmVisualizer):
    """Visualizer for ALNS algorithm.

    This class provides specialized visualizations for ALNS algorithm,
    including operator scores, usage statistics, and adaptive behavior.
    """

    def __init__(self, **kwargs):
        """Initialize ALNS visualizer."""
        super().__init__(**kwargs)

    def visualize(self, alns_instance: Any,
                  plot_type: str = 'all',
                  **kwargs):
        """Create comprehensive visualization for ALNS instance.

        Args:
            alns_instance: ALNS instance to visualize
            plot_type: Type of visualization ('scores', 'theta', 'convergence', or 'all')
            **kwargs: Additional visualization parameters
        """
        if plot_type == 'all':
            self.create_figure(figsize=(16, 12), nrows=2, ncols=2)

            # Plot 1: Operator scores
            self._plot_operator_scores(alns_instance, ax=self._current_axes[0, 0])

            # Plot 2: Operator usage (theta)
            self._plot_operator_theta(alns_instance, ax=self._current_axes[0, 1])

            # Plot 3: Score convergence
            self._plot_score_convergence(alns_instance, ax=self._current_axes[1, 0])

            # Plot 4: Temperature schedule
            self._plot_temperature_schedule(alns_instance, ax=self._current_axes[1, 1])

            self._current_figure.suptitle('ALNS Algorithm Analysis', fontsize=16)
            plt.tight_layout()

        elif plot_type == 'scores':
            self._plot_operator_scores(alns_instance, **kwargs)
        elif plot_type == 'theta':
            self._plot_operator_theta(alns_instance, **kwargs)
        elif plot_type == 'convergence':
            self._plot_score_convergence(alns_instance, **kwargs)
        else:
            raise ValueError(f"Unknown plot_type: {plot_type}")

    def _plot_operator_scores(self, alns_instance: Any,
                              ax: Optional[plt.Axes] = None,
                              **kwargs):
        """Plot operator scores over segments.

        This method replicates the functionality of the original plot_scores
        method but with improved organization.
        """
        if ax is None:
            self.create_figure(figsize=(12, 6))
            ax = self._current_axes

        segments = range(alns_instance.removal_scores.shape[0])

        # Plot removal scores
        for i in range(len(alns_instance.removal_list)):
            label = self._get_operator_label('removal', i, alns_instance)
            ax.plot(segments, alns_instance.removal_scores[:, i],
                   label=label, linewidth=2, alpha=0.8)

        # Plot repair scores
        for i in range(len(alns_instance.repair_list)):
            label = self._get_operator_label('repair', i, alns_instance)
            ax.plot(segments, alns_instance.repair_scores[:, i],
                   label=label, linewidth=2, alpha=0.8, linestyle='--')

        ax.set_xlabel('Segment')
        ax.set_ylabel('Scores')
        ax.set_title('Operator Scores Over Segments')
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)

        if ax == self._current_axes:
            self.show()

    def _plot_operator_theta(self, alns_instance: Any,
                             ax: Optional[plt.Axes] = None,
                             **kwargs):
        """Plot operator usage counts (theta) over segments.

        This method replicates the functionality of the original plot_theta
        method but with improved organization.
        """
        if ax is None:
            self.create_figure(figsize=(12, 6))
            ax = self._current_axes

        segments = range(alns_instance.removal_theta.shape[0])

        # Plot removal theta
        for i in range(len(alns_instance.removal_list)):
            label = self._get_operator_label('removal', i, alns_instance)
            ax.plot(segments, alns_instance.removal_theta[:, i],
                   label=label, linewidth=2, alpha=0.8)

        # Plot repair theta
        for i in range(len(alns_instance.repair_list)):
            label = self._get_operator_label('repair', i, alns_instance)
            ax.plot(segments, alns_instance.repair_theta[:, i],
                   label=label, linewidth=2, alpha=0.8, linestyle='--')

        ax.set_xlabel('Segment')
        ax.set_ylabel('Theta (Usage Count)')
        ax.set_title('Operator Usage Count Over Segments')
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)

        if ax == self._current_axes:
            self.show()

    def _plot_score_convergence(self, alns_instance: Any,
                                ax: Optional[plt.Axes] = None,
                                **kwargs):
        """Plot score convergence over segments."""
        if ax is None:
            self.create_figure(figsize=(12, 6))
            ax = self._current_axes

        # Calculate average scores per segment
        segments = range(alns_instance.removal_scores.shape[0])

        if alns_instance.removal_scores.size > 0:
            avg_removal_scores = alns_instance.removal_scores.mean(axis=1)
            ax.plot(segments, avg_removal_scores, 'b-', linewidth=2,
                   label='Average Removal Scores', alpha=0.8)

        if alns_instance.repair_scores.size > 0:
            avg_repair_scores = alns_instance.repair_scores.mean(axis=1)
            ax.plot(segments, avg_repair_scores, 'r-', linewidth=2,
                   label='Average Repair Scores', alpha=0.8)

        ax.set_xlabel('Segment')
        ax.set_ylabel('Average Score')
        ax.set_title('Average Operator Score Convergence')
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)

        if ax == self._current_axes:
            self.show()

    def _plot_temperature_schedule(self, alns_instance: Any,
                                   ax: Optional[plt.Axes] = None,
                                   **kwargs):
        """Plot simulated annealing temperature schedule."""
        if ax is None:
            self.create_figure(figsize=(12, 6))
            ax = self._current_axes

        # Calculate temperature decay
        segments = range(100)  # Plot first 100 segments for clarity
        temperatures = [alns_instance.start_temp * (alns_instance.cooling_rate ** i)
                       for i in segments]

        ax.plot(segments, temperatures, 'g-', linewidth=2, alpha=0.8)
        ax.set_xlabel('Segment')
        ax.set_ylabel('Temperature')
        ax.set_title('Simulated Annealing Temperature Schedule')
        ax.grid(True, alpha=0.3)
        ax.set_yscale('log')  # Log scale for exponential decay

        if ax == self._current_axes:
            self.show()

    def _get_operator_label(self, operator_type: str, index: int,
                            alns_instance: Any) -> str:
        """Get human-readable label for operator.

        Args:
            operator_type: 'removal' or 'repair'
            index: Operator index
            alns_instance: ALNS instance

        Returns:
            Operator label string
        """
        # This mapping replicates the original labeling logic
        if operator_type == 'removal':
            if index == 0:
                return 'Shaw Removal'
            elif index == 1:
                return 'Random Removal'
            elif index == 2:
                return 'Worst Removal'
            else:
                return 'SISR Removal'
        else:  # repair
            if index == 0:
                return 'Greedy Insertion'
            else:
                return 'Regret Insertion'

    # Backward compatibility methods
    def plot_scores(self, alns_instance: Any):
        """Plot operator scores (backward compatibility).

        This method provides backward compatibility with the original
        plot_scores method in ALNS class.

        Args:
            alns_instance: ALNS instance to plot
        """
        self._plot_operator_scores(alns_instance)

    def plot_theta(self, alns_instance: Any):
        """Plot operator usage counts (backward compatibility).

        This method provides backward compatibility with the original
        plot_theta method in ALNS class.

        Args:
            alns_instance: ALNS instance to plot
        """
        self._plot_operator_theta(alns_instance)
