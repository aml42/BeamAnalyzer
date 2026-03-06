import numpy as np
import matplotlib.pyplot as plt


from .plotter import BeamPlotter
from .units import DeflectionUnit


class DeflectionCalculator:
    """
    Calculates beam deflection based on bending moment results.

    Uses double integration of the moment diagram to compute deflection.
    The deflection is calculated using the relationship: d²y/dx² = M/(EI)
    where M is the bending moment, E is the elastic modulus, and I is the moment of inertia.

    All inputs and outputs use pure SI units.

    Parameters
    ----------
    beam_plotter : BeamPlotter
        The BeamPlotter instance that contains the solved system and moment data.
    e_modulus : float, default 2.1e11
        Elastic modulus in Pa (default is typical for steel).
    inertia : float, default 1e-8
        Moment of inertia in m⁴.
    num_points : int, default 2000
        Number of evaluation points for deflection calculation.
    """
    
    def __init__(
        self,
        beam_plotter: BeamPlotter,
        e_modulus: float = 2.1e9,
        inertia: float = 1e-8,
        num_points: int = 2000
    ) -> None:
        self.beam_plotter = beam_plotter
        self.e_modulus = e_modulus  # Pa
        self.inertia = inertia  # m⁴
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
        m_over_ei = moment / (self.e_modulus * self.inertia)
        
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
    
    def get_max_deflection(self) -> tuple[float, float]:
        """
        Get the maximum deflection and its location.
        
        Returns
        -------
        tuple
            (max_deflection_m, x_position_m)
        """
        deflection = self.deflection
        x = self.x_coordinates
        
        # Find maximum absolute deflection
        max_idx = np.argmax(np.abs(deflection))
        max_deflection = deflection[max_idx]
        x_position = x[max_idx]
        
        return max_deflection, x_position
    
    def plot_deflection(self, ax: plt.Axes | None = None, unit: DeflectionUnit = DeflectionUnit.m, **kwargs) -> plt.Axes:
        """
        Plot the deflection diagram.

        Parameters
        ----------
        ax : plt.Axes, optional
            Matplotlib axes to plot on. If None, creates a new figure.
        unit : DeflectionUnit, default DeflectionUnit.m
            Y-axis unit.
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

        ax.plot(x, deflection * unit.scale, **default_kwargs)
        ax.set_xlabel('Position [m]')
        ax.set_ylabel(f'Deflection [{unit.label}]')
        ax.set_title('Beam Deflection Diagram')
        ax.grid(True, alpha=0.3)
        ax.legend()

        # Add span background
        self.beam_plotter._add_span_background(ax)

        return ax
    
    def plot_slope(self, ax: plt.Axes | None = None, **kwargs) -> plt.Axes:
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
        ax.set_xlabel('Position [m]')
        ax.set_ylabel('Slope [rad]')
        ax.set_title('Beam Slope Diagram')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # Add span background
        self.beam_plotter._add_span_background(ax)
        
        return ax
    
    def plot_all(self, figsize=(12, 8)) -> tuple[plt.Figure, tuple[plt.Axes, plt.Axes]]:
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
            Position along the beam in m.

        Returns
        -------
        float
            Deflection at the specified position in m.
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
            Position along the beam in m.

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


