import numpy as np
from typing import Dict, List, Tuple

try:
    from .systembuilder import SystemBuilder
    from .loads import TriangularLoad, UniformLoad
    from .supports import Support
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from systembuilder import SystemBuilder
    from loads import TriangularLoad, UniformLoad
    from supports import Support


class SystemSolver:
    """
    Solves the three-moment equation system for continuous beams.
    
    Based on the three-moment equation:
    M1*L1 + 2*M2*(L1 + L2) + M3*L2 + (6*A1*a1)/L1 + (6*A2*b2)/L2 = 0
    
    Where:
    - M1, M2, M3 are moments at supports
    - L1, L2 are span lengths
    - A1*a1, A2*b2 are load components from left and right spans
    
    For single span systems (2 supports), all moments are zero (simply supported).

    The moments are returned in Nm.
    """
    
    def __init__(self, system_builder: SystemBuilder):
        """
        Initialize the SystemSolver with a SystemBuilder instance.
        
        Args:
            system_builder: SystemBuilder instance containing loads and supports
        """
        self.system_builder = system_builder
        self.support_positions = system_builder.support_positions
        self.subsystems = system_builder._create_subsystems()
        self.subsystem_components = system_builder.calculate_subsystem_components()
        self.is_single_span = system_builder.is_single_span
        
        # Number of internal supports (excluding end supports)
        self.num_internal_supports = len(self.support_positions) - 2
        self.num_equations = len(self.subsystems)
        
    def _get_span_length(self, span_tuple: Tuple[float, float]) -> float:
        """Get the length of a span given its start and end positions."""
        return span_tuple[1] - span_tuple[0]
    
    def _build_coefficient_matrix(self) -> np.ndarray:
        """
        Build the coefficient matrix for the three-moment equations.
        
        Returns:
            Coefficient matrix where each row represents one subsystem equation
        """
        if self.is_single_span:
            # For single span, return empty matrix as there are no equations to solve
            return np.array([]).reshape(0, 0)
            
        # Initialize coefficient matrix
        coeff_matrix = np.zeros((self.num_equations, self.num_internal_supports))
        
        for i, subsystem in enumerate(self.subsystems):
            left_span, right_span = subsystem
            L1 = self._get_span_length(left_span)
            L2 = self._get_span_length(right_span)
            
            # Find which internal supports correspond to this subsystem
            # The subsystem connects three supports: start of left span, middle, end of right span
            left_support_pos = left_span[0]
            middle_support_pos = left_span[1]  # = right_span[0]
            right_support_pos = right_span[1]
            
            # Find indices of these supports in the internal supports list
            # Internal supports are all supports except the first and last
            internal_support_positions = self.support_positions[1:-1]
            
            # Find the index of the middle support (this is always an internal support)
            middle_support_idx = internal_support_positions.index(middle_support_pos)
            
            # Set coefficient for middle support: 2*(L1 + L2)
            coeff_matrix[i, middle_support_idx] = 2 * (L1 + L2)
            
            # If left support is internal, add its coefficient: L1
            if left_support_pos in internal_support_positions:
                left_support_idx = internal_support_positions.index(left_support_pos)
                coeff_matrix[i, left_support_idx] = L1
            
            # If right support is internal, add its coefficient: L2
            if right_support_pos in internal_support_positions:
                right_support_idx = internal_support_positions.index(right_support_pos)
                coeff_matrix[i, right_support_idx] = L2
                
        return coeff_matrix
    
    def _build_load_vector(self) -> np.ndarray:
        """
        Build the load vector (right-hand side) for the equation system.
        
        Returns:
            Load vector containing the negative sum of load components for each subsystem
        """
        if self.is_single_span:
            # For single span, return empty vector as there are no equations to solve
            return np.array([])
            
        load_vector = np.zeros(self.num_equations)
        
        for i, subsystem in enumerate(self.subsystems):
            components = self.subsystem_components[subsystem]
            # The load components are negative in the equation (moved to right side)
            load_vector[i] = -(components['left_component'] + components['right_component'])
            
        return load_vector
    
    def solve_moments(self) -> Dict[float, float]:
        """
        Solve the three-moment equation system to find internal support moments.
        
        For single span systems, all moments are zero (simply supported).
        
        Returns:
            Dictionary mapping support position to moment value
        """
        if self.is_single_span:
            # For single span, all moments are zero (simply supported)
            result = {}
            for pos in self.support_positions:
                result[pos] = 0.0
            return result
        
        # Build the equation system: A * M = b
        coeff_matrix = self._build_coefficient_matrix()
        load_vector = self._build_load_vector()
        
        # Solve the linear system
        try:
            moment_values = np.linalg.solve(coeff_matrix, load_vector)
        except np.linalg.LinAlgError as e:
            raise ValueError(f"Could not solve the moment equation system: {e}")
        
        # Create result dictionary mapping support positions to moments
        internal_support_positions = self.support_positions[1:-1]
        result = {}
        
        # End supports always have zero moment (simply supported)
        result[self.support_positions[0]] = 0.0
        result[self.support_positions[-1]] = 0.0
        
        # Internal supports have calculated moments
        for i, support_pos in enumerate(internal_support_positions):
            result[support_pos] = moment_values[i]
            
        return result
    
    def get_equation_system_info(self) -> Dict:
        """
        Get detailed information about the equation system for debugging/analysis.
        
        Returns:
            Dictionary containing coefficient matrix, load vector, and subsystem info
        """
        if self.is_single_span:
            return {
                'coefficient_matrix': np.array([]).reshape(0, 0),
                'load_vector': np.array([]),
                'subsystems': self.subsystems,
                'support_positions': self.support_positions,
                'internal_support_positions': [],
                'subsystem_components': self.subsystem_components,
                'is_single_span': True
            }
        
        coeff_matrix = self._build_coefficient_matrix()
        load_vector = self._build_load_vector()
        
        return {
            'coefficient_matrix': coeff_matrix,
            'load_vector': load_vector,
            'subsystems': self.subsystems,
            'support_positions': self.support_positions,
            'internal_support_positions': self.support_positions[1:-1],
            'subsystem_components': self.subsystem_components,
            'is_single_span': False
        }


if __name__ == "__main__":
    # Example usage with single span
    print("=== Single Span Test ===")
    loads = [UniformLoad(10, 0, 20)]
    supports = [Support(0), Support(20)]
    
    builder = SystemBuilder(loads, supports)
    solver = SystemSolver(builder)
    
    print("Support positions:", solver.support_positions)
    print("Is single span:", solver.is_single_span)
    print("Subsystems:", solver.subsystems)
    print("Subsystem components:", solver.subsystem_components)
    
    info = solver.get_equation_system_info()
    print("\nCoefficient matrix shape:", info['coefficient_matrix'].shape)
    print("Load vector shape:", info['load_vector'].shape)
    
    moments = solver.solve_moments()
    print(moments)
    print("\nSolved moments:")
    for pos, moment in moments.items():
        print(f"Support at {pos}: {moment:.2f}")
    
    # Example usage with continuous beam
    print("\n=== Continuous Beam Test ===")
    loads = [UniformLoad(10, 0, 20)]
    supports = [Support(0), Support(10), Support(20)]
    
    builder = SystemBuilder(loads, supports)
    solver = SystemSolver(builder)
    
    print("Support positions:", solver.support_positions)
    print("Is single span:", solver.is_single_span)
    print("Subsystems:", solver.subsystems)
    print("Subsystem components:", solver.subsystem_components)
    
    info = solver.get_equation_system_info()
    print("\nCoefficient matrix:")
    print(info['coefficient_matrix'])
    print("\nLoad vector:")
    print(info['load_vector'])
    
    moments = solver.solve_moments()
    print("\nSolved moments:")
    for pos, moment in moments.items():
        print(f"Support at {pos}: {moment:.2f}") 