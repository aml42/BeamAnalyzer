import numpy as np
from typing import Dict, List, Tuple

try:
    from .systembuilder import SystemBuilder
    from .systemsolver import SystemSolver
    from .loads import TriangularLoad, UniformLoad
    from .supports import Support
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from systembuilder import SystemBuilder
    from systemsolver import SystemSolver
    from loads import TriangularLoad, UniformLoad
    from supports import Support


class ReactionSolver:
    """
    Calculates support reactions for continuous beams with any number of supports.
    
    Uses the moments calculated by SystemSolver and applies equilibrium equations
    to each span to determine vertical support reactions.
    
    For single span systems (2 supports), uses simple statics with zero moments.
    """
    
    def __init__(self, system_builder: SystemBuilder, system_solver: SystemSolver):
        """
        Initialize the ReactionSolver.
        
        Args:
            system_builder: SystemBuilder instance containing loads and supports
            system_solver: SystemSolver instance with solved moments
        """
        self.system_builder = system_builder
        self.system_solver = system_solver
        self.support_positions = system_builder.support_positions
        self.loads = system_builder.loads
        self.is_single_span = system_builder.is_single_span
        
        # Get solved moments from SystemSolver
        self.support_moments = system_solver.solve_moments()
        
    def _get_span_info(self, span_index: int) -> Tuple[float, float, float]:
        """
        Get span information including length and end positions.
        
        Args:
            span_index: Index of the span (0-based)
            
        Returns:
            Tuple of (span_start, span_end, span_length)
        """
        span_start = self.support_positions[span_index]
        span_end = self.support_positions[span_index + 1]
        span_length = span_end - span_start
        return span_start, span_end, span_length
    
    def _get_loads_on_span(self, span_start: float, span_end: float) -> List:
        """
        Get all loads that affect a specific span.
        
        Args:
            span_start: Start position of the span
            span_end: End position of the span
            
        Returns:
            List of loads that overlap with the span
        """
        span_loads = []
        
        for load in self.loads:
            # Check if load overlaps with span
            if (load.start < span_end and load.end > span_start):
                span_loads.append(load)
                
        return span_loads
    
    def _calculate_total_load_on_span(self, span_start: float, span_end: float) -> float:
        """
        Calculate the total downward load on a span.
        
        Args:
            span_start: Start position of the span
            span_end: End position of the span
            
        Returns:
            Total load magnitude on the span
        """
        total_load = 0.0
        span_loads = self._get_loads_on_span(span_start, span_end)
        
        for load in span_loads:
            # Calculate the overlap between load and span
            overlap_start = max(load.start, span_start)
            overlap_end = min(load.end, span_end)
            
            if overlap_start < overlap_end:  # There is an overlap
                if isinstance(load, UniformLoad):
                    overlap_length = overlap_end - overlap_start
                    total_load += load.magnitude * overlap_length
                    
                elif isinstance(load, TriangularLoad):
                    # For triangular loads, we need to integrate over the overlap
                    overlap_length = overlap_end - overlap_start
                    
                    # Calculate load magnitudes at overlap boundaries
                    if load.magnitude_start < load.magnitude_end:
                        # Increasing triangular load
                        mag_at_start = load.magnitude_end * (overlap_start - load.start) / (load.end - load.start)
                        mag_at_end = load.magnitude_end * (overlap_end - load.start) / (load.end - load.start)
                    else:
                        # Decreasing triangular load
                        mag_at_start = load.magnitude_start * (load.end - overlap_start) / (load.end - load.start)
                        mag_at_end = load.magnitude_start * (load.end - overlap_end) / (load.end - load.start)
                    
                    # Area of trapezoid
                    total_load += 0.5 * (mag_at_start + mag_at_end) * overlap_length
                    
        return total_load
    
    def _calculate_moment_from_loads_about_point(self, span_start: float, span_end: float, 
                                                about_point: float) -> float:
        """
        Calculate the moment about a point due to all loads on a span.
        
        Args:
            span_start: Start position of the span
            span_end: End position of the span
            about_point: Point about which to take moments
            
        Returns:
            Total moment about the point (positive clockwise)
        """
        total_moment = 0.0
        span_loads = self._get_loads_on_span(span_start, span_end)
        
        for load in span_loads:
            # Calculate the overlap between load and span
            overlap_start = max(load.start, span_start)
            overlap_end = min(load.end, span_end)
            
            if overlap_start < overlap_end:  # There is an overlap
                if isinstance(load, UniformLoad):
                    overlap_length = overlap_end - overlap_start
                    load_magnitude = load.magnitude * overlap_length
                    # Centroid of uniform load is at the middle
                    centroid = (overlap_start + overlap_end) / 2
                    moment_arm = centroid - about_point
                    total_moment += load_magnitude * moment_arm
                    
                elif isinstance(load, TriangularLoad):
                    overlap_length = overlap_end - overlap_start
                    
                    if load.magnitude_start < load.magnitude_end:
                        # Increasing triangular load
                        mag_at_start = load.magnitude_end * (overlap_start - load.start) / (load.end - load.start)
                        mag_at_end = load.magnitude_end * (overlap_end - load.start) / (load.end - load.start)
                    else:
                        # Decreasing triangular load  
                        mag_at_start = load.magnitude_start * (load.end - overlap_start) / (load.end - load.start)
                        mag_at_end = load.magnitude_start * (load.end - overlap_end) / (load.end - load.start)
                    
                    # For a trapezoidal load, the centroid calculation is more complex
                    if abs(mag_at_start - mag_at_end) < 1e-10:  # Essentially uniform
                        load_magnitude = mag_at_start * overlap_length
                        centroid = (overlap_start + overlap_end) / 2
                    else:
                        # Trapezoidal load centroid
                        load_magnitude = 0.5 * (mag_at_start + mag_at_end) * overlap_length
                        # Centroid of trapezoid from overlap_start
                        if mag_at_end != mag_at_start:
                            centroid_from_start = overlap_length * (2 * mag_at_end + mag_at_start) / (3 * (mag_at_end + mag_at_start))
                        else:
                            centroid_from_start = overlap_length / 2
                        centroid = overlap_start + centroid_from_start
                    
                    moment_arm = centroid - about_point
                    total_moment += load_magnitude * moment_arm
                    
        return total_moment
    
    def calculate_support_reactions(self) -> Dict[float, float]:
        """
        Calculate all support reactions using equilibrium equations.
        
        For single span systems, uses simple statics with zero moments.
        
        Returns:
            Dictionary mapping support position to reaction force
        """
        if self.is_single_span:
            # For single span, use simple statics
            return self._calculate_single_span_reactions()
        
        num_spans = len(self.support_positions) - 1
        reactions = {}
        
        # Initialize all reactions to zero
        for pos in self.support_positions:
            reactions[pos] = 0.0
        
        # Calculate reactions for each span
        for span_idx in range(num_spans):
            span_start, span_end, span_length = self._get_span_info(span_idx)
            
            # Get moments at span ends
            moment_at_start = self.support_moments[span_start]
            moment_at_end = self.support_moments[span_end]
            
            # Calculate total load on span
            total_load = self._calculate_total_load_on_span(span_start, span_end)
            
            # Calculate moment about end support to find reaction at start support
            moment_about_end = self._calculate_moment_from_loads_about_point(
                span_start, span_end, span_end)
            
            # Equilibrium of moments about end support:
            # R_start * span_length + moment_at_start - moment_at_end = moment_about_end
            # R_start = (moment_about_end - moment_at_start + moment_at_end) / span_length
            if span_length > 0:
                reaction_at_start = (-moment_about_end - moment_at_start + moment_at_end) / span_length
            else:
                reaction_at_start = 0.0
            
            # Calculate reaction at end support using vertical equilibrium
            # R_start + R_end = total_load
            reaction_at_end = total_load - reaction_at_start
            
            # Add contributions to total reactions (for internal supports, 
            # reactions from adjacent spans will be summed)
            reactions[span_start] += reaction_at_start
            reactions[span_end] += reaction_at_end
        
        # Convert numpy floats to regular floats for cleaner output
        for pos in reactions:
            reactions[pos] = float(reactions[pos])
            
        return reactions
    
    def _calculate_single_span_reactions(self) -> Dict[float, float]:
        """
        Calculate reactions for a single span system using simple statics.
        
        Returns:
            Dictionary mapping support position to reaction force
        """
        if len(self.support_positions) != 2:
            raise ValueError("Single span reactions can only be calculated for 2 supports")
        
        span_start, span_end = self.support_positions[0], self.support_positions[1]
        span_length = span_end - span_start
        
        # Calculate total load on the span
        total_load = self._calculate_total_load_on_span(span_start, span_end)
        
        # Calculate moment about right support to find left reaction
        moment_about_right = self._calculate_moment_from_loads_about_point(
            span_start, span_end, span_end)
        
        # For simply supported beam with zero moments:
        # R_left * span_length = moment_about_right
        # The moment_about_right is positive when the load creates a clockwise moment
        # The left reaction should create a counterclockwise moment to balance it
        if span_length > 0:
            reaction_left = -moment_about_right / span_length
        else:
            reaction_left = 0.0
        
        # Calculate right reaction using vertical equilibrium
        reaction_right = total_load - reaction_left
        
        reactions = {
            span_start: float(reaction_left),
            span_end: float(reaction_right)
        }
        
        return reactions
    
    def get_reaction_details(self) -> Dict:
        """
        Get detailed information about reaction calculations for debugging.
        
        Returns:
            Dictionary containing detailed calculation information
        """
        if self.is_single_span:
            return self._get_single_span_reaction_details()
        
        num_spans = len(self.support_positions) - 1
        details = {
            'span_details': [],
            'total_reactions': self.calculate_support_reactions(),
            'support_moments': self.support_moments,
            'is_single_span': False
        }
        
        for span_idx in range(num_spans):
            span_start, span_end, span_length = self._get_span_info(span_idx)
            
            span_info = {
                'span_index': span_idx,
                'span_start': span_start,
                'span_end': span_end,
                'span_length': span_length,
                'total_load': self._calculate_total_load_on_span(span_start, span_end),
                'moment_about_end': self._calculate_moment_from_loads_about_point(
                    span_start, span_end, span_end),
                'moment_at_start': self.support_moments[span_start],
                'moment_at_end': self.support_moments[span_end],
                'loads_on_span': self._get_loads_on_span(span_start, span_end)
            }
            
            details['span_details'].append(span_info)
            
        return details
    
    def _get_single_span_reaction_details(self) -> Dict:
        """
        Get detailed information about single span reaction calculations.
        
        Returns:
            Dictionary containing detailed calculation information
        """
        span_start, span_end = self.support_positions[0], self.support_positions[1]
        span_length = span_end - span_start
        
        details = {
            'span_details': [{
                'span_index': 0,
                'span_start': span_start,
                'span_end': span_end,
                'span_length': span_length,
                'total_load': self._calculate_total_load_on_span(span_start, span_end),
                'moment_about_end': self._calculate_moment_from_loads_about_point(
                    span_start, span_end, span_end),
                'moment_at_start': 0.0,  # Simply supported
                'moment_at_end': 0.0,    # Simply supported
                'loads_on_span': self._get_loads_on_span(span_start, span_end)
            }],
            'total_reactions': self.calculate_support_reactions(),
            'support_moments': self.support_moments,
            'is_single_span': True
        }
        
        return details


if __name__ == "__main__":
    # Example usage with single span
    print("=== Single Span Test ===")
    loads = [UniformLoad(10, 0, 20)]
    supports = [Support(0), Support(20)]
    
    builder = SystemBuilder(loads, supports)
    solver = SystemSolver(builder)
    reaction_solver = ReactionSolver(builder, solver)
    
    print("Support positions:", reaction_solver.support_positions)
    print("Is single span:", reaction_solver.is_single_span)
    print("Support moments:", reaction_solver.support_moments)
    
    reactions = reaction_solver.calculate_support_reactions()
    print("\nSupport reactions:")
    for pos, reaction in reactions.items():
        print(f"Support at {pos}: {reaction:.2f}")
    
    # Get detailed information
    details = reaction_solver.get_reaction_details()
    print("\nDetailed calculation info:")
    for span_detail in details['span_details']:
        print(f"Span {span_detail['span_index']}: {span_detail['span_start']} to {span_detail['span_end']}")
        print(f"  Total load: {span_detail['total_load']:.2f}")
        print(f"  Moment about end: {span_detail['moment_about_end']:.2f}")
    
    # Example usage with continuous beam
    print("\n=== Continuous Beam Test ===")
    loads = [UniformLoad(10, 0, 20)]
    supports = [Support(0), Support(10), Support(20)]
    
    builder = SystemBuilder(loads, supports)
    solver = SystemSolver(builder)
    reaction_solver = ReactionSolver(builder, solver)
    
    print("Support positions:", reaction_solver.support_positions)
    print("Is single span:", reaction_solver.is_single_span)
    print("Support moments:", reaction_solver.support_moments)
    
    reactions = reaction_solver.calculate_support_reactions()
    print("\nSupport reactions:")
    for pos, reaction in reactions.items():
        print(f"Support at {pos}: {reaction:.2f}")
    
    # Get detailed information
    details = reaction_solver.get_reaction_details()
    print("\nDetailed calculation info:")
    for span_detail in details['span_details']:
        print(f"Span {span_detail['span_index']}: {span_detail['span_start']} to {span_detail['span_end']}")
        print(f"  Total load: {span_detail['total_load']:.2f}")
        print(f"  Moment about end: {span_detail['moment_about_end']:.2f}") 