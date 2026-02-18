import numpy as np
import matplotlib.pyplot as plt
from typing import Optional, Tuple, List

try:
    from .systembuilder import SystemBuilder
    from .systemsolver import SystemSolver
    from .reactionsolver import ReactionSolver
    from .plotter import BeamPlotter
    from .loads import UniformLoad, TriangularLoad
except ImportError:
    # Support direct execution when the package import fails
    from systembuilder import SystemBuilder
    from systemsolver import SystemSolver
    from reactionsolver import ReactionSolver
    from plotter import BeamPlotter
    from loads import UniformLoad, TriangularLoad


class DeflectionCalculator:
    """
    Calculates beam deflection based on bending moment results.
    
    Uses double integration of the moment diagram to compute deflection.
    The deflection is calculated using the relationship: d²y/dx² = M/(EI)
    where M is the bending moment, E is the elastic modulus, and I is the moment of inertia.
    
    Note: The system now accepts loads in N/m and support positions in m, but all internal
    calculations are performed in mm for consistency with the existing codebase.
    
    Parameters
    ----------
    beam_plotter : BeamPlotter
        The BeamPlotter instance that contains the solved system and moment data.
    e_modulus : float, default 210000
        Elastic modulus in N/mm² (default is typical for steel).
    inertia : float
        Moment of inertia in cm⁴ (will be converted to mm⁴ internally).
    num_points : int, default 2000
        Number of evaluation points for deflection calculation.
    """
    
    def __init__(
        self,
        beam_plotter: BeamPlotter,
        e_modulus: float = 210000,
        inertia: float = 1.0,
        num_points: int = 2000
    ) -> None:
        self.beam_plotter = beam_plotter
        self.e_modulus = e_modulus  # N/mm²
        self.inertia_cm4 = inertia  # cm⁴
        self.inertia_mm4 = inertia * 10000  # Convert cm⁴ to mm⁴
        self.num_points = max(100, num_points)
        
        # Cache the moment data
        self._ensure_moment_data()
        
        # Initialize deflection arrays
        self._deflection: np.ndarray | None = None
        self._slope: np.ndarray | None = None
        
    def _ensure_moment_data(self):
        """Ensure that moment data is available from the beam plotter."""
        if self.beam_plotter._moment is None:
            self.beam_plotter._ensure_fields()
    
    def _calculate_deflection(self):
        """
        Calculate deflection using double integration of the moment diagram.
        
        The deflection is calculated span-by-span to respect the boundary conditions
        at supports (deflection = 0 at supports).
        """
        if self._deflection is not None:
            return  # Already calculated
            
        x = self.beam_plotter._x
        moment = self.beam_plotter._moment
        support_positions = self.beam_plotter.support_positions
        
        # Initialize arrays
        self._deflection = np.zeros_like(moment)
        self._slope = np.zeros_like(moment)
        
        # Calculate M/(EI) for integration
        m_over_ei = moment / (self.e_modulus * self.inertia_mm4)
        
        # Process each span separately to respect boundary conditions
        for i in range(len(support_positions) - 1):
            start_pos = support_positions[i]
            end_pos = support_positions[i + 1]
            
            # Find indices for this span
            span_mask = (x >= start_pos) & (x <= end_pos)
            span_x = x[span_mask]
            span_m_over_ei = m_over_ei[span_mask]
            
            if span_x.size < 2:
                continue
                
            # First integration: slope = ∫(M/(EI))dx
            # Use cumulative trapezoidal integration
            dx = np.diff(span_x)
            if dx.size > 0:
                # Calculate slope using trapezoidal integration
                slope_increments = (span_m_over_ei[:-1] + span_m_over_ei[1:]) / 2 * dx
                span_slope = np.concatenate([[0], np.cumsum(slope_increments)])
                
                # Second integration: deflection = ∫slope dx
                deflection_increments = (span_slope[:-1] + span_slope[1:]) / 2 * dx
                span_deflection = np.concatenate([[0], np.cumsum(deflection_increments)])
                
                # Apply boundary conditions: deflection = 0 at supports
                # Linear correction to ensure deflection = 0 at end support
                if span_deflection.size > 1:
                    # Calculate correction needed at end support
                    end_deflection = span_deflection[-1]
                    # Apply linear correction across the span
                    correction_ramp = np.linspace(0, -end_deflection, span_deflection.size)
                    span_deflection += correction_ramp
                    
                    # Also correct slope to maintain consistency
                    slope_correction = -end_deflection / (end_pos - start_pos)
                    slope_ramp = np.linspace(0, slope_correction, span_slope.size)
                    span_slope += slope_ramp
                
                # Store results
                self._slope[span_mask] = span_slope
                self._deflection[span_mask] = span_deflection
    
    @property
    def deflection(self) -> np.ndarray:
        """Return the calculated deflection values."""
        if self._deflection is None:
            self._calculate_deflection()
        return self._deflection.copy()
    
    @property
    def slope(self) -> np.ndarray:
        """Return the calculated slope values."""
        if self._slope is None:
            self._calculate_deflection()
        return self._slope
    
    @property
    def x_coordinates(self) -> np.ndarray:
        """Return the x-coordinates used for calculation."""
        return self.beam_plotter._x
    
    def get_max_deflection(self) -> Tuple[float, float]:
        """
        Get the maximum deflection and its location.
        
        Returns
        -------
        tuple
            (max_deflection_mm, x_position_mm)
        """
        deflection = self.deflection
        x = self.x_coordinates
        
        # Find maximum absolute deflection
        max_idx = np.argmax(np.abs(deflection))
        max_deflection = deflection[max_idx]
        x_position = x[max_idx]
        
        return max_deflection, x_position
    
    def plot_deflection(self, ax: Optional[plt.Axes] = None, **kwargs) -> plt.Axes:
        """
        Plot the deflection diagram.
        
        Parameters
        ----------
        ax : plt.Axes, optional
            Matplotlib axes to plot on. If None, creates a new figure.
        **kwargs
            Additional keyword arguments passed to plt.plot().
            
        Returns
        -------
        plt.Axes
            The axes containing the plot.
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 6))
        
        deflection = self.deflection
        x = self.x_coordinates
        
        # Default styling
        default_kwargs = {
            'color': 'red',
            'linewidth': 2,
            'label': 'Deflection'
        }
        default_kwargs.update(kwargs)
        
        ax.plot(x, deflection, **default_kwargs)
        ax.set_xlabel('Position [mm]')
        ax.set_ylabel('Deflection [mm]')
        ax.set_title('Beam Deflection Diagram')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # Add span background
        self.beam_plotter._add_span_background(ax)
        
        return ax
    
    def plot_slope(self, ax: Optional[plt.Axes] = None, **kwargs) -> plt.Axes:
        """
        Plot the slope diagram.
        
        Parameters
        ----------
        ax : plt.Axes, optional
            Matplotlib axes to plot on. If None, creates a new figure.
        **kwargs
            Additional keyword arguments passed to plt.plot().
            
        Returns
        -------
        plt.Axes
            The axes containing the plot.
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 6))
        
        slope = self.slope
        x = self.x_coordinates
        
        # Default styling
        default_kwargs = {
            'color': 'purple',
            'linewidth': 2,
            'label': 'Slope'
        }
        default_kwargs.update(kwargs)
        
        ax.plot(x, slope, **default_kwargs)
        ax.set_xlabel('Position [mm]')
        ax.set_ylabel('Slope [rad]')
        ax.set_title('Beam Slope Diagram')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # Add span background
        self.beam_plotter._add_span_background(ax)
        
        return ax
    
    def plot_all(self, figsize=(12, 8)) -> Tuple[plt.Figure, Tuple[plt.Axes, plt.Axes]]:
        """
        Create a comprehensive plot showing both deflection and slope.
        
        Parameters
        ----------
        figsize : tuple, default (12, 8)
            Figure size (width, height) in inches.
            
        Returns
        -------
        tuple
            (figure, (deflection_ax, slope_ax))
        """
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize)
        
        # Plot deflection
        self.plot_deflection(ax1)
        
        # Plot slope
        self.plot_slope(ax2)
        
        plt.tight_layout()
        return fig, (ax1, ax2)
    
    def get_deflection_at_position(self, position: float) -> float:
        """
        Get deflection at a specific position.
        
        Parameters
        ----------
        position : float
            Position along the beam in mm.
            
        Returns
        -------
        float
            Deflection at the specified position in mm.
        """
        x = self.x_coordinates
        deflection = self.deflection
        
        # Find the closest point
        idx = np.argmin(np.abs(x - position))
        return deflection[idx]
    
    def get_slope_at_position(self, position: float) -> float:
        """
        Get slope at a specific position.
        
        Parameters
        ----------
        position : float
            Position along the beam in mm.
            
        Returns
        -------
        float
            Slope at the specified position in radians.
        """
        x = self.x_coordinates
        slope = self.slope
        
        # Find the closest point
        idx = np.argmin(np.abs(x - position))
        return slope[idx]


class DeflectionCalculatorSI:
    """
    SI unit version of DeflectionCalculator that accepts loads in N/m and positions in m.
    
    This class converts SI units to the internal mm system and then uses the standard
    DeflectionCalculator for calculations.
    
    Parameters
    ----------
    loads : List[UniformLoad or TriangularLoad]
        List of loads with magnitudes in N/m and positions in m
    support_positions : List[float]
        Support positions in m
    e_modulus : float, default 210000
        Elastic modulus in N/mm² (default is typical for steel).
    inertia : float
        Moment of inertia in cm⁴ (will be converted to mm⁴ internally).
    num_points : int, default 2000
        Number of evaluation points for deflection calculation.
    """
    
    def __init__(
        self,
        loads: List,
        support_positions: List[float],
        e_modulus: float = 210000,
        inertia: float = 1.0,
        num_points: int = 2000
    ) -> None:
        # Convert loads from N/m to N/mm and positions from m to mm
        converted_loads = self._convert_loads_to_mm(loads)
        converted_supports = self._convert_supports_to_mm(support_positions)
        
        # Build and solve the system with converted units
        builder = SystemBuilder(converted_loads, converted_supports)
        solver = SystemSolver(builder)
        reaction_solver = ReactionSolver(builder, solver)
        plotter = BeamPlotter(builder, solver, reaction_solver)
        
        # Create the internal deflection calculator
        self.deflection_calc = DeflectionCalculator(
            plotter, e_modulus, inertia, num_points
        )
        
        # Store original SI units for reference
        self.original_loads = loads
        self.original_support_positions = support_positions
        
    def _convert_loads_to_mm(self, loads: List) -> List:
        """Convert loads from N/m and m to N/mm and mm."""
        converted_loads = []
        
        for load in loads:
            if isinstance(load, UniformLoad):
                # Convert magnitude from N/m to N/mm (divide by 1000)
                # Convert positions from m to mm (multiply by 1000)
                converted_load = UniformLoad(
                    magnitude=load.magnitude / 1000.0,
                    start=load.start * 1000.0,
                    end=load.end * 1000.0
                )
            elif isinstance(load, TriangularLoad):
                # Convert magnitudes from N/m to N/mm (divide by 1000)
                # Convert positions from m to mm (multiply by 1000)
                converted_load = TriangularLoad(
                    magnitude_start=load.magnitude_start / 1000.0,
                    magnitude_end=load.magnitude_end / 1000.0,
                    start=load.start * 1000.0,
                    end=load.end * 1000.0
                )
            else:
                raise ValueError(f"Unsupported load type: {type(load)}")
            
            converted_loads.append(converted_load)
        
        return converted_loads
    
    def _convert_supports_to_mm(self, support_positions: List[float]) -> List:
        """Convert support positions from m to mm."""
        try:
            from .supports import Support
        except ImportError:
            from supports import Support
        return [Support(pos * 1000.0) for pos in support_positions]
    
    @property
    def deflection(self) -> np.ndarray:
        """Return the calculated deflection values in mm."""
        return self.deflection_calc.deflection
    
    @property
    def slope(self) -> np.ndarray:
        """Return the calculated slope values in radians."""
        return self.deflection_calc.slope
    
    @property
    def x_coordinates(self) -> np.ndarray:
        """Return the x-coordinates used for calculation in mm."""
        return self.deflection_calc.x_coordinates
    
    def get_max_deflection(self) -> Tuple[float, float]:
        """
        Get the maximum deflection and its location.
        
        Returns
        -------
        tuple
            (max_deflection_mm, x_position_mm)
        """
        return self.deflection_calc.get_max_deflection()
    
    def plot_deflection(self, ax: Optional[plt.Axes] = None, **kwargs) -> plt.Axes:
        """
        Plot the deflection diagram with x-axis in meters.
        
        Parameters
        ----------
        ax : plt.Axes, optional
            Matplotlib axes to plot on. If None, creates a new figure.
        **kwargs
            Additional keyword arguments passed to plt.plot().
            
        Returns
        -------
        plt.Axes
            The axes containing the plot.
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 6))
        
        deflection = self.deflection
        x_mm = self.x_coordinates
        x_m = x_mm / 1000.0  # Convert mm to m
        
        # Default styling
        default_kwargs = {
            'color': 'red',
            'linewidth': 2,
            'label': 'Deflection'
        }
        default_kwargs.update(kwargs)
        
        ax.plot(x_m, deflection, **default_kwargs)
        ax.set_xlabel('Position [m]')
        ax.set_ylabel('Deflection [mm]')
        ax.set_title('Beam Deflection Diagram (SI Units)')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # Add span background (convert support positions to m)
        support_positions_m = [pos / 1000.0 for pos in self.deflection_calc.beam_plotter.support_positions]
        self._add_span_background_si(ax, support_positions_m)
        
        return ax
    
    def plot_slope(self, ax: Optional[plt.Axes] = None, **kwargs) -> plt.Axes:
        """
        Plot the slope diagram with x-axis in meters.
        
        Parameters
        ----------
        ax : plt.Axes, optional
            Matplotlib axes to plot on. If None, creates a new figure.
        **kwargs
            Additional keyword arguments passed to plt.plot().
            
        Returns
        -------
        plt.Axes
            The axes containing the plot.
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 6))
        
        slope = self.slope
        x_mm = self.x_coordinates
        x_m = x_mm / 1000.0  # Convert mm to m
        
        # Default styling
        default_kwargs = {
            'color': 'purple',
            'linewidth': 2,
            'label': 'Slope'
        }
        default_kwargs.update(kwargs)
        
        ax.plot(x_m, slope, **default_kwargs)
        ax.set_xlabel('Position [m]')
        ax.set_ylabel('Slope [rad]')
        ax.set_title('Beam Slope Diagram (SI Units)')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # Add span background (convert support positions to m)
        support_positions_m = [pos / 1000.0 for pos in self.deflection_calc.beam_plotter.support_positions]
        self._add_span_background_si(ax, support_positions_m)
        
        return ax
    
    def plot_all(self, figsize=(12, 8)) -> Tuple[plt.Figure, Tuple[plt.Axes, plt.Axes]]:
        """
        Create a comprehensive plot showing both deflection and slope with x-axis in meters.
        
        Parameters
        ----------
        figsize : tuple, default (12, 8)
            Figure size (width, height) in inches.
            
        Returns
        -------
        tuple
            (figure, (deflection_ax, slope_ax))
        """
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize)
        
        # Plot deflection with SI units
        self.plot_deflection(ax1)
        
        # Plot slope with SI units
        self.plot_slope(ax2)
        
        plt.tight_layout()
        return fig, (ax1, ax2)
    
    def get_deflection_at_position(self, position: float) -> float:
        """
        Get deflection at a specific position.
        
        Parameters
        ----------
        position : float
            Position along the beam in m.
            
        Returns
        -------
        float
            Deflection at the specified position in mm.
        """
        # Convert position from m to mm
        position_mm = position * 1000.0
        return self.deflection_calc.get_deflection_at_position(position_mm)
    
    def get_slope_at_position(self, position: float) -> float:
        """
        Get slope at a specific position.
        
        Parameters
        ----------
        position : float
            Position along the beam in m.
            
        Returns
        -------
        float
            Slope at the specified position in radians.
        """
        # Convert position from m to mm
        position_mm = position * 1000.0
        return self.deflection_calc.get_slope_at_position(position_mm)
    
    def _add_span_background_si(self, ax: plt.Axes, support_positions_m: List[float]):
        """
        Add span background to the plot with support positions in meters.
        
        Parameters
        ----------
        ax : plt.Axes
            The axes to add the background to.
        support_positions_m : List[float]
            Support positions in meters.
        """
        if len(support_positions_m) < 2:
            return
            
        # Get the y-axis limits
        y_min, y_max = ax.get_ylim()
        
        # Add alternating background colors for each span
        for i in range(len(support_positions_m) - 1):
            start_pos = support_positions_m[i]
            end_pos = support_positions_m[i + 1]
            
            # Alternate colors for visual distinction
            color = 'lightblue' if i % 2 == 0 else 'lightgreen'
            alpha = 0.2
            
            # Add rectangle for this span
            rect = plt.Rectangle((start_pos, y_min), end_pos - start_pos, y_max - y_min,
                               facecolor=color, alpha=alpha, edgecolor='none', zorder=-1)
            ax.add_patch(rect)
            
            # Add span label at the top with padding
            span_center = (start_pos + end_pos) / 2
            ax.text(span_center, y_max - (y_max - y_min) * 0.15, f'Span {i+1}', 
                   ha='center', va='bottom', fontsize=10, fontweight='bold',
                   bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
        
        # Add support markers
        for i, pos in enumerate(support_positions_m):
            ax.axvline(x=pos, color='black', linestyle='-', linewidth=2, alpha=0.7)
            ax.text(pos, y_min - (y_max - y_min) * 0.1, f'Support {i+1}', 
                   ha='center', va='top', fontsize=9, fontweight='bold')


if __name__ == "__main__":
    # Example usage with SI units (N/m, m)
    from loads import UniformLoad
    from supports import Support
    
    # Create loads in N/m and positions in m
    loads = [UniformLoad(3480, 0, 4.5)]  # 3480 N/m uniform load from 0 to 4.5 m
    support_positions = [0, 1.5, 3.0, 4.5]  # Supports at 0, 1.5, 3.0, and 4.5 meters
    
    # Use the SI version of the deflection calculator
    deflection_calc = DeflectionCalculatorSI(
        loads=loads,
        support_positions=support_positions,
        e_modulus=210000,
        inertia=75.1
    )
    
    # Get maximum deflection
    max_deflection, max_pos = deflection_calc.get_max_deflection()
    print(f"Maximum deflection: {max_deflection:.6f} mm at position {max_pos:.1f} mm")
    
    # Get deflection at a specific position (in m)
    deflection_at_2m = deflection_calc.get_deflection_at_position(2.0)
    print(f"Deflection at 2.0 m: {deflection_at_2m:.6f} mm")
    
    # Plot results
    fig, (ax1, ax2) = deflection_calc.plot_all()
    plt.show() 