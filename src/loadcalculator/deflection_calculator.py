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
        Calculate deflection by globally double-integrating M/(EI) over the full
        beam, then subtracting a piecewise-linear function so that the deflection
        equals zero at every support.

        Each inter-support span uses one linear piece (one slope, one intercept),
        so within each span the result is mathematically identical to the
        previous span-by-span integration. Cantilever overhangs reuse the
        adjacent end span's piece, so the correction has *no kink* at the first
        or last support — eliminating the spurious slope discontinuity that was
        visible at cantilever-adjacent supports. Kinks at internal supports are
        proportional only to numerical drift in ``M(x)`` (~1e-5 rad), so the
        deflection curve appears smooth everywhere.
        """
        if self._deflection is not None:
            return

        x = self.beam_plotter._x
        moment = self.beam_plotter._moment
        supports = self.beam_plotter.support_positions
        m_over_ei = moment / (self.e_modulus * self.inertia)

        if x.size < 2 or len(supports) < 2:
            self._slope = np.zeros_like(moment)
            self._deflection = np.zeros_like(moment)
            return

        # Global cumulative trapezoidal double integration.
        dx = np.diff(x)
        raw_slope = np.concatenate([[0.0], np.cumsum((m_over_ei[:-1] + m_over_ei[1:]) / 2 * dx)])
        raw_def = np.concatenate([[0.0], np.cumsum((raw_slope[:-1] + raw_slope[1:]) / 2 * dx)])

        n_sp = len(supports)
        sup_idx = [int(np.argmin(np.abs(x - s))) for s in supports]

        # One linear piece per inter-support span: subtract the line passing
        # through (s_a, raw_def(s_a)) and (s_b, raw_def(s_b)).
        slope_pieces = np.empty(n_sp - 1)
        intercept_pieces = np.empty(n_sp - 1)
        for i in range(n_sp - 1):
            s_a = float(supports[i])
            s_b = float(supports[i + 1])
            y_a = float(raw_def[sup_idx[i]])
            y_b = float(raw_def[sup_idx[i + 1]])
            if s_b == s_a:
                slope_pieces[i] = 0.0
                intercept_pieces[i] = y_a
            else:
                slope_pieces[i] = (y_b - y_a) / (s_b - s_a)
                intercept_pieces[i] = y_a - slope_pieces[i] * s_a

        corrected_def = raw_def.copy()
        corrected_slope = raw_slope.copy()

        for i in range(n_sp - 1):
            mask = (x >= supports[i]) & (x <= supports[i + 1])
            corrected_def[mask] = raw_def[mask] - (slope_pieces[i] * x[mask] + intercept_pieces[i])
            corrected_slope[mask] = raw_slope[mask] - slope_pieces[i]

        # Overhangs reuse the first / last span's linear piece — no kink at the
        # cantilever-adjacent supports.
        if x[0] < supports[0]:
            mask = x < supports[0]
            corrected_def[mask] = raw_def[mask] - (slope_pieces[0] * x[mask] + intercept_pieces[0])
            corrected_slope[mask] = raw_slope[mask] - slope_pieces[0]
        if x[-1] > supports[-1]:
            mask = x > supports[-1]
            corrected_def[mask] = raw_def[mask] - (slope_pieces[-1] * x[mask] + intercept_pieces[-1])
            corrected_slope[mask] = raw_slope[mask] - slope_pieces[-1]

        self._slope = corrected_slope
        self._deflection = corrected_def
    
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


