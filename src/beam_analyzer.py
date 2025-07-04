import numpy as np
from typing import List, Dict, Optional, Tuple, Union
import matplotlib.pyplot as plt

try:
    from .loads import UniformLoad, TriangularLoad
    from .supports import Support
    from .systembuilder import SystemBuilder
    from .systemsolver import SystemSolver
    from .reactionsolver import ReactionSolver
    from .plotter import BeamPlotter
    from .deflection_calculator import DeflectionCalculatorSI
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from loads import UniformLoad, TriangularLoad
    from supports import Support
    from systembuilder import SystemBuilder
    from systemsolver import SystemSolver
    from reactionsolver import ReactionSolver
    from plotter import BeamPlotter
    from deflection_calculator import DeflectionCalculatorSI


class BeamAnalyzer:
    """
    Main interface for beam analysis that provides a unified way to analyze continuous beams.
    
    This class combines all the functionality of the basic_mechanics package into a single
    easy-to-use interface. It uses SI units throughout: positions in meters, loads in N/m,
    and handles internal unit conversions for deflection calculations.
    
    Parameters
    ----------
    support_positions : List[float]
        List of support positions along the beam axis in meters.
    loads : List[Union[UniformLoad, TriangularLoad]]
        List of load objects (UniformLoad and/or TriangularLoad) with magnitudes in N/m.
    inertia : Optional[float], default None
        Moment of inertia in cm⁴. If None, deflection calculations will be skipped.
    e_modulus : float, default 210000
        Elastic modulus in N/mm² (default is typical for steel).
    num_points : int, default 2000
        Number of evaluation points for calculations and plotting.
    
    Attributes
    ----------
    support_positions : List[float]
        The support positions used in the analysis (in meters).
    loads : List[Union[UniformLoad, TriangularLoad]]
        The loads applied to the beam (magnitudes in N/m).
    inertia : Optional[float]
        Moment of inertia used for deflection calculations (in cm⁴).
    e_modulus : float
        Elastic modulus used for deflection calculations (in N/mm²).
    num_points : int
        Number of evaluation points.
    """
    
    def __init__(
        self,
        support_positions: List[float],
        loads: List[Union[UniformLoad, TriangularLoad]],
        inertia: Optional[float] = None,
        e_modulus: float = 210000,
        num_points: int = 2000
    ):
        # Validate inputs
        if len(support_positions) < 2:
            raise ValueError("At least 2 support positions are required")
        
        if not loads:
            raise ValueError("At least one load must be provided")
        
        # Store parameters
        self.support_positions = support_positions
        self.loads = loads
        self.inertia = inertia
        self.e_modulus = e_modulus
        self.num_points = num_points
        
        # Create support objects
        self.supports = [Support(pos) for pos in support_positions]
        
        # Initialize components
        self._system_builder = None
        self._system_solver = None
        self._reaction_solver = None
        self._beam_plotter = None
        self._deflection_calculator = None
        
        # Cache for results
        self._analysis_results = None
        
    def _initialize_components(self):
        """Initialize all analysis components."""
        if self._system_builder is None:
            self._system_builder = SystemBuilder(self.loads, self.supports)
            self._system_solver = SystemSolver(self._system_builder)
            self._reaction_solver = ReactionSolver(self._system_builder, self._system_solver)
            self._beam_plotter = BeamPlotter(
                self._system_builder, 
                self._system_solver, 
                self._reaction_solver, 
                self.num_points
            )
            
            if self.inertia is not None:
                self._deflection_calculator = DeflectionCalculatorSI(
                    self.loads,
                    self.support_positions,
                    self.e_modulus,
                    self.inertia,
                    self.num_points
                )
    
    def analyze(self) -> Dict:
        """
        Perform complete beam analysis.
        
        Returns
        -------
        Dict
            Dictionary containing all analysis results:
            - 'reactions': Dict mapping support positions to reaction forces
            - 'moments_at_supports': Dict mapping support positions to moments
            - 'max_moments_per_span': List of dicts with max moment info for each span
            - 'max_shear_per_span': List of dicts with max shear info for each span
            - 'max_deflection_per_span': List of dicts with max deflection info for each span (if inertia provided)
        """
        self._initialize_components()
        
        # Get basic results
        reactions = self._reaction_solver.calculate_support_reactions()
        moments_at_supports = self._system_solver.solve_moments()
        
        # Calculate max values per span
        max_moments_per_span = self._get_max_moments_per_span()
        max_shear_per_span = self._get_max_shear_per_span()
        
        # Initialize results
        results = {
            'reactions': reactions,
            'moments_at_supports': moments_at_supports,
            'max_moments_per_span': max_moments_per_span,
            'max_shear_per_span': max_shear_per_span,
        }
        
        # Add deflection results if inertia is provided
        if self.inertia is not None:
            max_deflection_per_span = self._get_max_deflection_per_span()
            results['max_deflection_per_span'] = max_deflection_per_span
        
        self._analysis_results = results
        return results
    
    def _get_max_moments_per_span(self) -> List[Dict]:
        """Calculate maximum moments in each span with their positions."""
        self._beam_plotter._ensure_fields()
        
        max_moments = []
        for i in range(len(self.support_positions) - 1):
            start_pos = self.support_positions[i]
            end_pos = self.support_positions[i + 1]
            
            # Find indices for this span
            span_mask = (self._beam_plotter._x >= start_pos) & (self._beam_plotter._x <= end_pos)
            span_x = self._beam_plotter._x[span_mask]
            span_moment = self._beam_plotter._moment[span_mask]
            
            if span_moment.size == 0:
                continue
            
            # Find maximum absolute moment
            max_idx = np.argmax(np.abs(span_moment))
            max_moment = span_moment[max_idx]
            max_position = span_x[max_idx]
            
            max_moments.append({
                'span_index': i,
                'span_start': start_pos,
                'span_end': end_pos,
                'max_moment': max_moment,
                'max_moment_position': max_position
            })
        
        return max_moments
    
    def _get_max_shear_per_span(self) -> List[Dict]:
        """Calculate maximum shear forces in each span with their positions."""
        self._beam_plotter._ensure_fields()
        
        max_shear = []
        for i in range(len(self.support_positions) - 1):
            start_pos = self.support_positions[i]
            end_pos = self.support_positions[i + 1]
            
            # Find indices for this span
            span_mask = (self._beam_plotter._x >= start_pos) & (self._beam_plotter._x <= end_pos)
            span_x = self._beam_plotter._x[span_mask]
            span_shear = self._beam_plotter._shear[span_mask]
            
            if span_shear.size == 0:
                continue
            
            # Find maximum absolute shear
            max_idx = np.argmax(np.abs(span_shear))
            max_shear_val = span_shear[max_idx]
            max_position = span_x[max_idx]
            
            max_shear.append({
                'span_index': i,
                'span_start': start_pos,
                'span_end': end_pos,
                'max_shear': max_shear_val,
                'max_shear_position': max_position
            })
        
        return max_shear
    
    def _get_max_deflection_per_span(self) -> List[Dict]:
        """Calculate maximum deflections in each span with their positions."""
        if self._deflection_calculator is None:
            raise ValueError("Deflection calculator not initialized. Provide inertia parameter.")
        
        deflection = self._deflection_calculator.deflection
        x = self._deflection_calculator.x_coordinates
        
        max_deflections = []
        for i in range(len(self.support_positions) - 1):
            start_pos = self.support_positions[i]
            end_pos = self.support_positions[i + 1]
            
            # Find indices for this span
            span_mask = (x >= start_pos) & (x <= end_pos)
            span_x = x[span_mask]
            span_deflection = deflection[span_mask]
            
            if span_deflection.size == 0:
                continue
            
            # Find maximum absolute deflection
            max_idx = np.argmax(np.abs(span_deflection))
            max_deflection = span_deflection[max_idx]
            max_position = span_x[max_idx]
            
            max_deflections.append({
                'span_index': i,
                'span_start': start_pos,
                'span_end': end_pos,
                'max_deflection': max_deflection,
                'max_deflection_position': max_position
            })
        
        return max_deflections
    
    def get_shear_values(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get all shear force values over the beam span.
        
        Returns
        -------
        Tuple[np.ndarray, np.ndarray]
            (x_coordinates, shear_values)
        """
        self._initialize_components()
        self._beam_plotter._ensure_fields()
        return self._beam_plotter._x, self._beam_plotter._shear
    
    def get_moment_values(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get all moment values over the beam span.
        
        Returns
        -------
        Tuple[np.ndarray, np.ndarray]
            (x_coordinates, moment_values)
        """
        self._initialize_components()
        self._beam_plotter._ensure_fields()
        return self._beam_plotter._x, self._beam_plotter._moment
    
    def get_deflection_values(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get all deflection values over the beam span.
        
        Returns
        -------
        Tuple[np.ndarray, np.ndarray]
            (x_coordinates, deflection_values)
        """
        if self.inertia is None:
            raise ValueError("Deflection values not available. Provide inertia parameter.")
        
        self._initialize_components()
        return self._deflection_calculator.x_coordinates, self._deflection_calculator.deflection
    
    def get_value_at_position(self, position: float) -> Dict:
        """
        Get shear, moment, and deflection values at a specific position.
        
        Parameters
        ----------
        position : float
            Position along the beam axis.
            
        Returns
        -------
        Dict
            Dictionary containing values at the specified position:
            - 'position': The input position
            - 'shear': Shear force at position
            - 'moment': Bending moment at position
            - 'deflection': Deflection at position (if inertia provided)
        """
        self._initialize_components()
        
        # Get shear and moment values
        x_coords, shear_values = self.get_shear_values()
        _, moment_values = self.get_moment_values()
        
        # Interpolate to get values at the specified position
        shear_at_pos = np.interp(position, x_coords, shear_values)
        moment_at_pos = np.interp(position, x_coords, moment_values)
        
        result = {
            'position': position,
            'shear': shear_at_pos,
            'moment': moment_at_pos
        }
        
        # Add deflection if available
        if self.inertia is not None:
            x_def, deflection_values = self.get_deflection_values()
            deflection_at_pos = np.interp(position, x_def, deflection_values)
            result['deflection'] = deflection_at_pos
        
        return result
    
    def plot_shear_diagram(self, save_path: Optional[str] = None, **kwargs) -> plt.Axes:
        """
        Plot the shear force diagram.
        
        Parameters
        ----------
        save_path : Optional[str], default None
            If provided, save the plot to this path.
        **kwargs
            Additional keyword arguments passed to the plotter.
            
        Returns
        -------
        plt.Axes
            The axes containing the plot.
        """
        self._initialize_components()
        ax = self._beam_plotter.plot_shear(**kwargs)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return ax
    
    def plot_moment_diagram(self, save_path: Optional[str] = None, **kwargs) -> plt.Axes:
        """
        Plot the bending moment diagram.
        
        Parameters
        ----------
        save_path : Optional[str], default None
            If provided, save the plot to this path.
        **kwargs
            Additional keyword arguments passed to the plotter.
            
        Returns
        -------
        plt.Axes
            The axes containing the plot.
        """
        self._initialize_components()
        ax = self._beam_plotter.plot_moment(**kwargs)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return ax
    
    def plot_deflection_diagram(self, save_path: Optional[str] = None, **kwargs) -> plt.Axes:
        """
        Plot the deflection diagram.
        
        Parameters
        ----------
        save_path : Optional[str], default None
            If provided, save the plot to this path.
        **kwargs
            Additional keyword arguments passed to the plotter.
            
        Returns
        -------
        plt.Axes
            The axes containing the plot.
        """
        if self.inertia is None:
            raise ValueError("Deflection plot not available. Provide inertia parameter.")
        
        self._initialize_components()
        ax = self._deflection_calculator.plot_deflection(**kwargs)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return ax
    
    def plot_all_diagrams(self, save_path: Optional[str] = None, figsize: Tuple[int, int] = (15, 10)) -> Tuple[plt.Figure, Tuple[plt.Axes, plt.Axes, plt.Axes]]:
        """
        Plot all diagrams (shear, moment, deflection) in a single figure.
        
        Parameters
        ----------
        save_path : Optional[str], default None
            If provided, save the plot to this path.
        figsize : Tuple[int, int], default (15, 10)
            Figure size (width, height).
            
        Returns
        -------
        Tuple[plt.Figure, Tuple[plt.Axes, plt.Axes, plt.Axes]]
            Figure and axes containing all three plots.
        """
        self._initialize_components()
        
        if self.inertia is not None:
            # Create figure with three subplots
            fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=figsize)
            
            # Plot shear diagram
            self._beam_plotter.plot_shear(ax=ax1)
            ax1.set_title('Shear Force Diagram')
            
            # Plot moment diagram
            self._beam_plotter.plot_moment(ax=ax2)
            ax2.set_title('Bending Moment Diagram')
            
            # Plot deflection diagram
            self._deflection_calculator.plot_deflection(ax=ax3)
            ax3.set_title('Deflection Diagram')
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
            
            return fig, (ax1, ax2, ax3)
        else:
            # Create figure with two subplots (no deflection)
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(figsize[0], figsize[1] * 2/3))
            
            # Plot shear diagram
            self._beam_plotter.plot_shear(ax=ax1)
            ax1.set_title('Shear Force Diagram')
            
            # Plot moment diagram
            self._beam_plotter.plot_moment(ax=ax2)
            ax2.set_title('Bending Moment Diagram')
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
            
            return fig, (ax1, ax2)