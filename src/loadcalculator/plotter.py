import numpy as np
import matplotlib.pyplot as plt
from typing import Optional, Tuple

try:
    from .systembuilder import SystemBuilder
    from .systemsolver import SystemSolver
    from .reactionsolver import ReactionSolver
    from .loads import UniformLoad, TriangularLoad
except ImportError:
    # Support direct execution when the package import fails
    from systembuilder import SystemBuilder
    from systemsolver import SystemSolver
    from reactionsolver import ReactionSolver
    from loads import UniformLoad, TriangularLoad


class BeamPlotter:
    """Utility class that plots shear-force and bending-moment diagrams for a
    continuous beam assembled with *SystemBuilder*, solved with *SystemSolver*
    and *ReactionSolver*.

    Parameters
    ----------
    system_builder : SystemBuilder
        The already-configured SystemBuilder instance that holds loads and
        support information.
    system_solver : SystemSolver | None, default None
        If *None*, a new SystemSolver will be instantiated with *system_builder*.
    reaction_solver : ReactionSolver | None, default None
        If *None*, a new ReactionSolver will be instantiated with the
        *system_builder* and the (possibly newly-created) *system_solver*.
    num_points : int, default 1000
        Number of evaluation points that will be used along the beam when the
        internal shear and bending-moment fields are computed.  A higher number
        increases accuracy at the expense of speed.
    """

    def __init__(
        self,
        system_builder: SystemBuilder,
        system_solver: Optional[SystemSolver] = None,
        reaction_solver: Optional[ReactionSolver] = None,
        num_points: int = 2000,
    ) -> None:
        self.builder = system_builder
        self.solver = system_solver or SystemSolver(system_builder)
        self.reaction_solver = reaction_solver or ReactionSolver(system_builder, self.solver)
        self.num_points = max(100, num_points)  # guard against tiny numbers

        # Cache solved quantities so we do the heavy lifting only once
        self._moments = self.solver.solve_moments()
        self._reactions = self.reaction_solver.calculate_support_reactions()

        # Space discretisation
        self._x: np.ndarray | None = None
        self._w: np.ndarray | None = None
        self._shear: np.ndarray | None = None
        self._moment: np.ndarray | None = None

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    @property
    def support_positions(self) -> Tuple[float, ...]:
        return self.builder.support_positions

    @property
    def moments_at_supports(self):
        """Return a dict {support_position: bending_moment}."""
        return self._moments

    @property
    def reactions(self):
        """Return a dict {support_position: reaction_force}.  Positive means
        upward (conventional sign used throughout the module).
        """
        return self._reactions

    # ------------------------------------------------------------------
    # Numerical field evaluation
    # ------------------------------------------------------------------

    def _distributed_load(self, x: float) -> float:
        """Return total distributed load intensity *w(x)* at coordinate *x*.

        The convention is *positive downwards* because the original *Load*
        objects represent gravitation loads.  Internally, shear is computed
        assuming *positive upward* forces, hence the minus sign when the load
        is later integrated.
        """
        w_val = 0.0
        for ld in self.builder.loads:
            if ld.start <= x <= ld.end:
                w_val += ld.load_function(x)
        return w_val

    def _ensure_fields(self):
        if self._shear is not None and self._moment is not None:
            return  # Already computed

        x0 = self.support_positions[0]
        xL = self.support_positions[-1]
        self._x = np.linspace(x0, xL, self.num_points)

        # Vectorised distributed load
        v_load_func = np.vectorize(self._distributed_load)
        self._w = v_load_func(self._x)

        dx = self._x[1] - self._x[0]

        # ------------------------------------------------------------------
        # Shear force V(x): integrate (-w) and add point reactions
        # Conventional sign: upward positive
        # ------------------------------------------------------------------

        # Start with distributed load contribution
        # Shear from distributed load alone: V_w(x) = -∫ w dx
        cumulative_w = np.cumsum(self._w) * dx
        shear = -cumulative_w  # start with negative because w is downward

        # Add reactions (point loads) as step functions.  For every support
        # situated at position a, the shear will jump by +R (upward) for all
        # sections **to the right** of the support.
        for pos, reaction in self._reactions.items():
            shear += reaction * (self._x >= pos)

        self._shear = shear
        print(len(self._shear))

        # ------------------------------------------------------------------
        # Bending moment M(x): integrate shear V(x)
        # We integrate span-by-span to honour the already-solved support moments
        # as boundary conditions, thereby eliminating numerical drift.
        # ------------------------------------------------------------------

        moment = np.zeros_like(self._shear)
        span_indices = list(range(len(self.support_positions) - 1))

        for idx in span_indices:
            a = self.support_positions[idx]
            b = self.support_positions[idx + 1]

            # indices belonging to current span
            span_mask = (self._x >= a) & (self._x <= b)
            span_x = self._x[span_mask]
            span_shear = self._shear[span_mask]

            # Starting moment at left support (provided by SystemSolver)
            M0 = self._moments.get(a, 0.0)
            M_end_expected = self._moments.get(b, 0.0)

            # Cumulative integrate via trapezoidal rule inside the span
            if span_x.size > 1:
                dxi = np.diff(span_x)
                # cumulative trapezoidal integration
                dMi = (span_shear[:-1] + span_shear[1:]) / 2 * dxi
                span_moment = np.concatenate([[M0], np.cumsum(dMi) + M0])
            else:
                span_moment = np.array([M0])

            # Apply linear correction so that moment at right support matches
            # the value obtained from the analytical SystemSolver.
            if span_moment.size > 1:
                correction = M_end_expected - span_moment[-1]
                # Linear ramp 0 -> correction across the span length
                ramp = np.linspace(0.0, correction, span_moment.size)
                span_moment += ramp

            moment[span_mask] = span_moment

        self._moment = moment
        print(len(self._moment))
    # ------------------------------------------------------------------
    # Internal helper for span shading
    # ------------------------------------------------------------------

    def _add_span_background(
        self,
        ax: "plt.Axes",
        colors: Tuple[str, str] = ("lightblue", "lightgreen"),  # Updated colors
        alpha: float = 0.2,
    ) -> None:
        """Tint the background of *ax* to highlight individual spans.

        The function draws a semi‐transparent rectangle for every span
        (between consecutive supports) using two alternating colours from the
        *colors* tuple.  It is idempotent: calling it multiple times on the
        same ``Axes`` will not duplicate the rectangles.
        """
        if getattr(ax, "_spans_shaded", False):
            return  # already shaded

        for idx in range(len(self.support_positions) - 1):
            a = self.support_positions[idx]
            b = self.support_positions[idx + 1]
            color = colors[idx % len(colors)]
            ax.axvspan(a, b, facecolor=color, alpha=alpha, zorder=-1)

        ax._spans_shaded = True  # type: ignore[attr-defined]
    
    def _add_span_labels(self, ax: "plt.Axes") -> None:
        """Add span labels to the plot at the top with proper padding.
        
        Parameters
        ----------
        ax : plt.Axes
            The axes to add the span labels to.
        """
        for idx in range(len(self.support_positions) - 1):
            a = self.support_positions[idx]
            b = self.support_positions[idx + 1]
            
            # Add span label at the top with padding
            span_center = (a + b) / 2
            y_min, y_max = ax.get_ylim()
            ax.text(span_center, y_max - (y_max - y_min) * 0.15, f'Span {idx+1}', 
                   ha='center', va='bottom', fontsize=10, fontweight='bold',
                   bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))

    def _add_support_labels(self, ax: "plt.Axes") -> None:
        """Add support labels to the plot.
        
        Parameters
        ----------
        ax : plt.Axes
            The axes to add the support labels to.
        """
        if len(self.support_positions) < 1:
            return
            
        # Get the y-axis limits
        y_min, y_max = ax.get_ylim()
        
        # Add support markers and labels
        for i, pos in enumerate(self.support_positions):
            ax.axvline(x=pos, color='black', linestyle='-', linewidth=2, alpha=0.7)
            ax.text(pos, y_min - (y_max - y_min) * 0.1, f'Support {i+1}', 
                   ha='center', va='top', fontsize=9, fontweight='bold')

    # ------------------------------------------------------------------
    # Plotting interface
    # ------------------------------------------------------------------

    def plot_shear(self, ax: Optional[plt.Axes] = None, **kwargs) -> plt.Axes:
        """Plot the shear-force diagram and return the Matplotlib ``Axes``."""
        self._ensure_fields()
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 6))
        
        # Default styling
        default_kwargs = {
            'color': 'blue',
            'linewidth': 2,
            'label': 'Shear Force'
        }
        default_kwargs.update(kwargs)
        
        self._add_span_background(ax)
        ax.plot(self._x, self._shear, **default_kwargs)
        ax.set_title("Shear Force Diagram")
        ax.set_xlabel("Position [m]")
        ax.set_ylabel("Shear V(x) [N]")
        ax.axhline(0, color="black", linewidth=0.8, alpha=0.3)
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # Add span and support labels after plot is drawn
        self._add_span_labels(ax)
        self._add_support_labels(ax)
        
        return ax

    def plot_moment(self, ax: Optional[plt.Axes] = None, **kwargs) -> plt.Axes:
        """Plot the bending-moment diagram and return the Matplotlib ``Axes``."""
        self._ensure_fields()
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 6))
        
        # Default styling
        default_kwargs = {
            'color': 'green',
            'linewidth': 2,
            'label': 'Bending Moment'
        }
        default_kwargs.update(kwargs)
        
        self._add_span_background(ax)
        ax.plot(self._x, self._moment, **default_kwargs)
        ax.set_title("Bending Moment Diagram")
        ax.set_xlabel("Position [m]")
        ax.set_ylabel("Moment M(x) [N·m]")
        ax.axhline(0, color="black", linewidth=0.8, alpha=0.3)
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # Add span and support labels after plot is drawn
        self._add_span_labels(ax)
        self._add_support_labels(ax)
        
        return ax

    def plot_all(self, figsize=(10, 6)) -> Tuple[plt.Figure, Tuple[plt.Axes, plt.Axes]]:
        """Convenience wrapper that plots shear and moment diagrams stacked
        vertically and returns the Matplotlib ``Figure`` together with both
        axes.
        """
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, sharex=True)
        self.plot_shear(ax1)
        self.plot_moment(ax2)
        plt.tight_layout()
        return fig, (ax1, ax2)


# ---------------------------------------------------------------------------
# Self-test / quick demo when executed as script
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Example identical to mechanics/basic_mechanics/example_usage.py
    ld = [
        TriangularLoad(0, 1400,1, 10),
    ]
    from loadcalculator.supports import Support
    sp = [Support(0), Support(3), Support(4), Support(12)]
    
    builder = SystemBuilder(ld, sp)
    plotter = BeamPlotter(builder)
    moments = plotter._ensure_fields()
    print(moments)
    plotter.plot_all()
    plt.show() 