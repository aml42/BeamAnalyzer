import numpy as np
import matplotlib.pyplot as plt

from .loads import UniformLoad, TriangularLoad
from .supports import Support
from .systembuilder import SystemBuilder
from .systemsolver import SystemSolver
from .reactionsolver import ReactionSolver
from .plotter import BeamPlotter
from .deflection_calculator import DeflectionCalculator
from .units import (
    ShearUnit, MomentUnit, DeflectionUnit,
    LengthUnit, ForcePerLengthUnit, PressureUnit, InertiaUnit,
)


class BeamAnalyzer:
    """
    Main interface for beam analysis that provides a unified way to analyze continuous beams.

    This class combines all the functionality of the basic_mechanics package into a single
    easy-to-use interface. Input and output units are independently configurable.

    Parameters
    ----------
    support_positions : list[float]
        Support positions along the beam axis.
    loads : list[UniformLoad | TriangularLoad]
        Load objects whose positions and magnitudes are in the units given by
        ``position_unit`` and ``load_unit``.
    inertia : float | None, default None
        Moment of inertia (in ``inertia_unit``). If None, deflection is skipped.
    e_modulus : float, default 2.1e11
        Elastic modulus (in ``e_modulus_unit``). Default is steel in Pa.
    num_points : int, default 2000
        Number of evaluation points for calculations and plotting.
    position_unit : LengthUnit, default LengthUnit.m
        Unit of ``support_positions`` and load start/end positions.
    load_unit : ForcePerLengthUnit, default ForcePerLengthUnit.N_per_m
        Unit of load magnitudes.
    e_modulus_unit : PressureUnit, default PressureUnit.Pa
        Unit of ``e_modulus``.
    inertia_unit : InertiaUnit, default InertiaUnit.m4
        Unit of ``inertia``.
    shear_unit : ShearUnit, default ShearUnit.N
        Unit for shear force output.
    moment_unit : MomentUnit, default MomentUnit.Nm
        Unit for moment output.
    deflection_unit : DeflectionUnit, default DeflectionUnit.m
        Unit for deflection output.
    """

    def __init__(
        self,
        support_positions: list[float],
        loads: list[UniformLoad | TriangularLoad],
        inertia: float | None = None,
        e_modulus: float = 2.1e11,
        num_points: int = 2000,
        position_unit: LengthUnit = LengthUnit.m,
        load_unit: ForcePerLengthUnit = ForcePerLengthUnit.N_per_m,
        e_modulus_unit: PressureUnit = PressureUnit.Pa,
        inertia_unit: InertiaUnit = InertiaUnit.m4,
        shear_unit: ShearUnit = ShearUnit.N,
        moment_unit: MomentUnit = MomentUnit.Nm,
        deflection_unit: DeflectionUnit = DeflectionUnit.m,
    ):
        # Validate inputs
        if len(support_positions) < 2:
            raise ValueError("At least 2 support positions are required")

        if not loads:
            raise ValueError("At least one load must be provided")

        # Convert inputs to SI
        pos_scale = position_unit.to_si
        load_scale = load_unit.to_si

        self.support_positions = [p * pos_scale for p in support_positions]
        self.loads = self._convert_loads(loads, pos_scale, load_scale)
        self.inertia = inertia * inertia_unit.to_si if inertia is not None else None
        self.e_modulus = e_modulus * e_modulus_unit.to_si
        self.num_points = num_points
        self.shear_unit = shear_unit
        self.moment_unit = moment_unit
        self.deflection_unit = deflection_unit
        
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
        
    @staticmethod
    def _convert_loads(loads, pos_scale: float, load_scale: float) -> list:
        """Return new load objects with positions and magnitudes converted to SI."""
        converted = []
        for load in loads:
            if isinstance(load, UniformLoad):
                converted.append(UniformLoad(
                    magnitude=load.magnitude * load_scale,
                    start=load.start * pos_scale,
                    end=load.end * pos_scale,
                ))
            elif isinstance(load, TriangularLoad):
                converted.append(TriangularLoad(
                    magnitude_start=load.magnitude_start * load_scale,
                    magnitude_end=load.magnitude_end * load_scale,
                    start=load.start * pos_scale,
                    end=load.end * pos_scale,
                ))
            else:
                raise ValueError(f"Unsupported load type: {type(load)}")
        return converted

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
                self._deflection_calculator = DeflectionCalculator(
                    self._beam_plotter,
                    self.e_modulus,
                    self.inertia,
                    self.num_points
                )
    
    def analyze(self) -> dict:
        """
        Perform complete beam analysis.
        
        Returns
        -------
        dict
            dictionary containing all analysis results:
            - 'reactions': dict mapping support positions to reaction forces
            - 'moments_at_supports': dict mapping support positions to moments
            - 'max_moments_per_span': list of dicts with max moment info for each span
            - 'max_shear_per_span': list of dicts with max shear info for each span
            - 'max_deflection_per_span': list of dicts with max deflection info for each span (if inertia provided)
        """
        self._initialize_components()
        
        # Get basic results
        reactions_si = self._reaction_solver.calculate_support_reactions()
        moments_si = self._system_solver.solve_moments()

        # Apply unit scaling
        reactions = {k: float(v) * self.shear_unit.scale for k, v in reactions_si.items()}
        moments_at_supports = {k: float(v) * self.moment_unit.scale for k, v in moments_si.items()}

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
    
    def _get_max_moments_per_span(self) -> list[dict]:
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
                'max_moment': float(max_moment) * self.moment_unit.scale,
                'max_moment_position': float(max_position)
            })
        
        return max_moments
    
    def _get_max_shear_per_span(self) -> list[dict]:
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
                'max_shear': float(max_shear_val) * self.shear_unit.scale,
                'max_shear_position': float(max_position)
            })
        
        return max_shear
    
    def _get_max_deflection_per_span(self) -> list[dict]:
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
                'max_deflection': float(max_deflection) * self.deflection_unit.scale,
                'max_deflection_position': float(max_position)
            })
        
        return max_deflections
    
    def get_shear_values(self) -> tuple[np.ndarray, np.ndarray]:
        """
        Get all shear force values over the beam span in the configured unit.

        Returns
        -------
        tuple[np.ndarray, np.ndarray]
            (x_coordinates, shear_values)
        """
        self._initialize_components()
        self._beam_plotter._ensure_fields()
        return self._beam_plotter._x, self._beam_plotter._shear * self.shear_unit.scale

    def get_moment_values(self) -> tuple[np.ndarray, np.ndarray]:
        """
        Get all moment values over the beam span in the configured unit.

        Returns
        -------
        tuple[np.ndarray, np.ndarray]
            (x_coordinates, moment_values)
        """
        self._initialize_components()
        self._beam_plotter._ensure_fields()
        return self._beam_plotter._x, self._beam_plotter._moment * self.moment_unit.scale

    def get_deflection_values(self) -> tuple[np.ndarray, np.ndarray]:
        """
        Get all deflection values over the beam span in the configured unit.

        Returns
        -------
        tuple[np.ndarray, np.ndarray]
            (x_coordinates, deflection_values)
        """
        if self.inertia is None:
            raise ValueError("Deflection values not available. Provide inertia parameter.")

        self._initialize_components()
        return self._deflection_calculator.x_coordinates, self._deflection_calculator.deflection * self.deflection_unit.scale
    
    def get_value_at_position(self, position: float) -> dict:
        """
        Get shear, moment, and deflection values at a specific position.

        Values are returned in the configured output units.

        Parameters
        ----------
        position : float
            Position along the beam axis in meters.

        Returns
        -------
        dict
            dictionary containing values at the specified position:
            - 'position': The input position
            - 'shear': Shear force at position (in configured shear_unit)
            - 'moment': Bending moment at position (in configured moment_unit)
            - 'deflection': Deflection at position (in configured deflection_unit, if inertia provided)
        """
        self._initialize_components()
        self._beam_plotter._ensure_fields()

        # Interpolate raw SI values and scale
        x_coords = self._beam_plotter._x
        shear_at_pos = float(np.interp(position, x_coords, self._beam_plotter._shear)) * self.shear_unit.scale
        moment_at_pos = float(np.interp(position, x_coords, self._beam_plotter._moment)) * self.moment_unit.scale

        result = {
            'position': position,
            'shear': shear_at_pos,
            'moment': moment_at_pos
        }

        # Add deflection if available
        if self.inertia is not None:
            x_def = self._deflection_calculator.x_coordinates
            defl = self._deflection_calculator.deflection
            deflection_at_pos = float(np.interp(position, x_def, defl)) * self.deflection_unit.scale
            result['deflection'] = deflection_at_pos

        return result
    
    def plot_shear_diagram(self, save_path: str | None = None, unit: ShearUnit | None = None, **kwargs) -> plt.Axes:
        """
        Plot the shear force diagram.

        Parameters
        ----------
        save_path : str | None, default None
            If provided, save the plot to this path.
        unit : ShearUnit | None, default None
            Y-axis unit. Defaults to the analyzer's ``shear_unit``.
        **kwargs
            Additional keyword arguments passed to the plotter.

        Returns
        -------
        plt.Axes
            The axes containing the plot.
        """
        self._initialize_components()
        ax = self._beam_plotter.plot_shear(unit=unit or self.shear_unit, **kwargs)

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')

        return ax
    
    def plot_moment_diagram(self, save_path: str | None = None, unit: MomentUnit | None = None, **kwargs) -> plt.Axes:
        """
        Plot the bending moment diagram.

        Parameters
        ----------
        save_path : str | None, default None
            If provided, save the plot to this path.
        unit : MomentUnit | None, default None
            Y-axis unit. Defaults to the analyzer's ``moment_unit``.
        **kwargs
            Additional keyword arguments passed to the plotter.

        Returns
        -------
        plt.Axes
            The axes containing the plot.
        """
        self._initialize_components()
        ax = self._beam_plotter.plot_moment(unit=unit or self.moment_unit, **kwargs)

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')

        return ax
    
    def plot_deflection_diagram(self, save_path: str | None = None, unit: DeflectionUnit | None = None, **kwargs) -> plt.Axes:
        """
        Plot the deflection diagram.

        Parameters
        ----------
        save_path : str | None, default None
            If provided, save the plot to this path.
        unit : DeflectionUnit | None, default None
            Y-axis unit. Defaults to the analyzer's ``deflection_unit``.
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
        ax = self._deflection_calculator.plot_deflection(unit=unit or self.deflection_unit, **kwargs)

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')

        return ax
    
    def plot_all_diagrams(
        self,
        save_path: str | None = None,
        figsize: tuple[int, int] = (15, 10),
        shear_unit: ShearUnit | None = None,
        moment_unit: MomentUnit | None = None,
        deflection_unit: DeflectionUnit | None = None,
    ) -> tuple[plt.Figure, tuple[plt.Axes, plt.Axes, plt.Axes]]:
        """
        Plot all diagrams (shear, moment, deflection) in a single figure.

        Parameters
        ----------
        save_path : str | None, default None
            If provided, save the plot to this path.
        figsize : tuple[int, int], default (15, 10)
            Figure size (width, height).
        shear_unit : ShearUnit | None, default None
            Y-axis unit for shear diagram. Defaults to the analyzer's ``shear_unit``.
        moment_unit : MomentUnit | None, default None
            Y-axis unit for moment diagram. Defaults to the analyzer's ``moment_unit``.
        deflection_unit : DeflectionUnit | None, default None
            Y-axis unit for deflection diagram. Defaults to the analyzer's ``deflection_unit``.

        Returns
        -------
        tuple[plt.Figure, tuple[plt.Axes, plt.Axes, plt.Axes]]
            Figure and axes containing all three plots.
        """
        self._initialize_components()
        su = shear_unit or self.shear_unit
        mu = moment_unit or self.moment_unit
        du = deflection_unit or self.deflection_unit

        if self.inertia is not None:
            fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=figsize)

            self._beam_plotter.plot_moment(ax=ax1, unit=mu)
            ax1.set_title('Bending Moment Diagram')

            self._beam_plotter.plot_shear(ax=ax2, unit=su)
            ax2.set_title('Shear Force Diagram')

            self._deflection_calculator.plot_deflection(ax=ax3, unit=du)
            ax3.set_title('Deflection Diagram')

            plt.tight_layout()

            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')

            return fig, (ax1, ax2, ax3)
        else:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(figsize[0], figsize[1] * 2/3))

            self._beam_plotter.plot_moment(ax=ax1, unit=mu)
            ax1.set_title('Bending Moment Diagram')

            self._beam_plotter.plot_shear(ax=ax2, unit=su)
            ax2.set_title('Shear Force Diagram')

            plt.tight_layout()

            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')

            return fig, (ax1, ax2)