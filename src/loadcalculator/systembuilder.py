from scipy.integrate import quad  # type: ignore

from .loads import TriangularLoad, UniformLoad
from .supports import Support



class SystemBuilder:
    def __init__(
        self,
        loads: list[UniformLoad | TriangularLoad],
        supports: list[Support],
        beam_left: float | None = None,
        beam_right: float | None = None,
    ):
        self.loads = loads

        if len(supports) < 2:
            raise ValueError("A system must have at least 2 supports")

        self.support_positions: tuple[float, ...] = tuple(sorted([support.position for support in supports]))
        self.is_single_span = len(supports) == 2

        # Beam physical extent (may exceed inter-support span when cantilevers exist).
        first_support = self.support_positions[0]
        last_support = self.support_positions[-1]
        self.beam_left = first_support if beam_left is None else min(beam_left, first_support)
        self.beam_right = last_support if beam_right is None else max(beam_right, last_support)
        self.has_left_overhang = self.beam_left < first_support
        self.has_right_overhang = self.beam_right > last_support
        self.has_overhang = self.has_left_overhang or self.has_right_overhang
        
    def compute_end_moments(self) -> tuple[float, float]:
        """Compute the bending moments at the end supports caused by overhang
        loads (cantilever statics). Returns ``(M_left_end, M_right_end)``.

        Sign convention matches the rest of the package: sagging is positive,
        so a downward load on a cantilever produces a *negative* (hogging)
        moment at the adjacent end support.

        Loads must already be pre-split at the end-support positions — i.e.
        each load lies fully inside one of: left overhang, main beam, right
        overhang. ``BeamAnalyzer`` performs this split before constructing
        the SystemBuilder.
        """
        a_left = self.support_positions[0]
        a_right = self.support_positions[-1]
        m_left = 0.0
        m_right = 0.0
        for load in self.loads:
            if load.end <= a_left:
                # entirely on left overhang
                integrand = lambda x, ld=load: ld.load_function(x) * (a_left - x)
                m_left += -quad(integrand, load.start, load.end)[0]
            elif load.start >= a_right:
                # entirely on right overhang
                integrand = lambda x, ld=load: ld.load_function(x) * (x - a_right)
                m_right += -quad(integrand, load.start, load.end)[0]
        return m_left, m_right

    def overhang_loads(self) -> tuple[list, list]:
        """Return ``(left_overhang_loads, right_overhang_loads)`` after split."""
        a_left = self.support_positions[0]
        a_right = self.support_positions[-1]
        left = [ld for ld in self.loads if ld.end <= a_left]
        right = [ld for ld in self.loads if ld.start >= a_right]
        return left, right

    def _create_subsystems(self):
        if self.is_single_span:
            # For single span, there are no subsystems (no internal supports)
            return tuple()
        
        simple_ranges = []
        for i in range(len(self.support_positions) - 1):
            current_range = (self.support_positions[i], self.support_positions[i+1])
            simple_ranges.append(current_range)
        
        paired_ranges = []
        for i in range(len(simple_ranges) - 1):
            current_pair = (simple_ranges[i], simple_ranges[i+1])
            paired_ranges.append(current_pair)

        return tuple(paired_ranges)
    
    def _get_overlapping_range(self, set1, set2):
        """
        Checks if the ranges of two sets of numbers overlap and returns the boundaries.

        The range of a set is determined by its minimum and maximum values.

        Args:
            set1: The first set of numbers.
            set2: The second set of numbers.

        Returns:
            A tuple representing the start and end of the overlapping range (start, end)
            if they overlap. Returns None if there is no overlap or if either set is empty.
        """
        if not set1 or not set2:
            return None  # Return None if either set is empty

        min1, max1 = min(set1), max(set1)
        min2, max2 = min(set2), max(set2)

        # Check for overlap
        if max1 > min2 and max2 > min1:
            # Calculate the overlapping boundaries
            overlap_start = max(min1, min2)
            overlap_end = min(max1, max2)

            return (overlap_start, overlap_end)
        else:
            return None
        
    def _get_subsystem_load_overlaps(self):
        if self.is_single_span:
            # For single span, return empty list as there are no subsystems
            return []
            
        overlaps = []
        # For each subsystem, check if it overlaps with any load
        for subsystem in self._create_subsystems():
            left_span, right_span = subsystem
            for load in self.loads:
                # Check overlap with left span
                left_overlap = self._get_overlapping_range(left_span, load.range)
                if left_overlap:
                    overlaps.append((subsystem, load, left_overlap, 'left'))
                
                # Check overlap with right span
                right_overlap = self._get_overlapping_range(right_span, load.range)
                if right_overlap:
                    overlaps.append((subsystem, load, right_overlap, 'right'))
        return overlaps

    def _calculate_load_components_for_subsystem(self, subsystem, load, overlap, span_position):
        """
        Calculate load components for a specific span in a subsystem.
        
        Args:
            subsystem: Tuple of two ranges representing the subsystem
            load: Load object with load_components_left_span and load_components_right_span methods
            overlap: Tuple representing the overlapping range (in absolute coordinates)
            span_position: 'left' or 'right' to indicate which span of the subsystem
            
        Returns:
            Load component value for the specified span
        """
        left_span, right_span = subsystem
        
        if span_position == 'left':
            span_start = left_span[0]
            span_length = left_span[1] - left_span[0]
            # Convert to span-relative coordinates for integration limits
            relative_start = overlap[0] - span_start
            relative_end = overlap[1] - span_start
            # Pass span_start so load function can convert back to absolute coordinates
            return load.load_components_left_span_with_offset(span_length, relative_start, relative_end, span_start)
        elif span_position == 'right':
            span_start = right_span[0]
            span_length = right_span[1] - right_span[0]
            # Convert to span-relative coordinates for integration limits
            relative_start = overlap[0] - span_start
            relative_end = overlap[1] - span_start
            # Pass span_start so load function can convert back to absolute coordinates
            return load.load_components_right_span_with_offset(span_length, relative_start, relative_end, span_start)
        else:
            raise ValueError("span_position must be 'left' or 'right'")

    def _get_subsystem_load_components_detailed(self):
        """
        Calculate detailed load components for each subsystem using the existing overlap detection.
        
        Returns:
            List of dictionaries, each containing:
            - subsystem: The subsystem tuple
            - left_span_overlaps: List of (load, overlap, component) for left span
            - right_span_overlaps: List of (load, overlap, component) for right span
        """
        if self.is_single_span:
            # For single span, return empty list as there are no subsystems
            return []
            
        # Get all overlaps using the existing method (now includes span position)
        all_overlaps = self._get_subsystem_load_overlaps()
        
        detailed_components = []
        
        for subsystem in self._create_subsystems():
            left_span_overlaps = []
            right_span_overlaps = []
            
            # Filter overlaps for this subsystem and group by span
            for overlap_data in all_overlaps:
                if len(overlap_data) == 4:  # New format: (subsystem, load, overlap, span_position)
                    overlap_subsystem, load, overlap, span_position = overlap_data
                    if overlap_subsystem == subsystem:
                        component = self._calculate_load_components_for_subsystem(
                            subsystem, load, overlap, span_position
                        )
                        if span_position == 'left':
                            left_span_overlaps.append((load, overlap, component))
                        elif span_position == 'right':
                            right_span_overlaps.append((load, overlap, component))
                            
            detailed_components.append({
                'subsystem': subsystem,
                'left_span_overlaps': left_span_overlaps,
                'right_span_overlaps': right_span_overlaps
            })
        
        return detailed_components

    def calculate_subsystem_components(self):
        """
        Calculate load components for all subsystems.
        
        Returns:
            Dictionary with subsystem as key and dict containing:
            - left_component: Sum of all left span load components
            - right_component: Sum of all right span load components  
            - total_component: Sum of left and right components
        """
        if self.is_single_span:
            # For single span, return empty dict as there are no subsystems
            return {}
            
        detailed_components = self._get_subsystem_load_components_detailed()
        result = {}
        
        for detail in detailed_components:
            subsystem = detail['subsystem']
            
            # Sum up left span components
            left_component = sum(overlap_data[2] for overlap_data in detail['left_span_overlaps'])
            
            # Sum up right span components
            right_component = sum(overlap_data[2] for overlap_data in detail['right_span_overlaps'])
            
            # Total component
            total_component = left_component + right_component
            
            result[subsystem] = {
                'left_component': left_component,
                'right_component': right_component,
                'total_component': total_component
            }
        
        return result

if __name__ == "__main__":
    # Test with single span
    builder = SystemBuilder([TriangularLoad(200, 0, 0, 20)], [Support(0), Support(20)])
    print("Single span test:", builder.is_single_span)
    print("Subsystems:", builder._create_subsystems())
    print("Components:", builder.calculate_subsystem_components())
    
    # Test with continuous beam
    builder = SystemBuilder([TriangularLoad(200, 0, 0, 20)], [Support(0), Support(10), Support(20)])
    print("\nContinuous beam test:", builder.is_single_span)
    print("Subsystems:", builder._create_subsystems())
    print("Components:", builder.calculate_subsystem_components())




