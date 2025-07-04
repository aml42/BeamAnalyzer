import numpy as np
from scipy.integrate import quad
import math as m


class LoadFunctions:
    '''
    Private base class for load functions.
    '''

    def _load_function_left_span(self, x, L: float) -> float:
        load = self.load_function(x)
        return (load*(x)/L * (L**2 -x**2))

    def _load_function_right_span(self, x, L: float) -> float:
        load = self.load_function(x)
        return (load*(L-x)/L * (L**2 -(L-x)**2))
    
    def _load_function_left_span_with_offset(self, x, L: float, span_start: float) -> float:
        """
        Load function for left span with proper coordinate handling.
        
        Args:
            x: Relative position within span (0 to L)
            L: Span length
            span_start: Absolute position of span start
        """
        absolute_x = x + span_start  # Convert relative x to absolute coordinate
        load = self.load_function(absolute_x)  # Evaluate load at absolute position
        return (load*(x)/L * (L**2 -x**2))  # Use relative x in the formula

    def _load_function_right_span_with_offset(self, x, L: float, span_start: float) -> float:
        """
        Load function for right span with proper coordinate handling.
        
        Args:
            x: Relative position within span (0 to L)
            L: Span length
            span_start: Absolute position of span start
        """
        absolute_x = x + span_start  # Convert relative x to absolute coordinate
        load = self.load_function(absolute_x)  # Evaluate load at absolute position
        return (load*(L-x)/L * (L**2 -(L-x)**2))  # Use relative x in the formula

    def load_components_left_span(self, span: float, start_overlap: float, end_overlap: float) -> float:
        result_left = quad(self._load_function_left_span, start_overlap, end_overlap, args=(span))[0]
        return result_left
    
    def load_components_right_span(self, span: float, start_overlap: float, end_overlap: float) -> float:
        result_right = quad(self._load_function_right_span, start_overlap, end_overlap, args=(span))[0]
        return result_right
    
    def load_components_left_span_with_offset(self, span: float, start_overlap: float, end_overlap: float, span_start: float) -> float:
        """
        Calculate load components for left span with proper coordinate handling.
        
        Args:
            span: Length of the span
            start_overlap: Start of overlap (relative to span start)
            end_overlap: End of overlap (relative to span start)
            span_start: Absolute position of span start (for load evaluation)
        """
        result_left = quad(self._load_function_left_span_with_offset, start_overlap, end_overlap, args=(span, span_start))[0]
        return result_left
    
    def load_components_right_span_with_offset(self, span: float, start_overlap: float, end_overlap: float, span_start: float) -> float:
        """
        Calculate load components for right span with proper coordinate handling.
        
        Args:
            span: Length of the span
            start_overlap: Start of overlap (relative to span start)
            end_overlap: End of overlap (relative to span start)
            span_start: Absolute position of span start (for load evaluation)
        """
        result_right = quad(self._load_function_right_span_with_offset, start_overlap, end_overlap, args=(span, span_start))[0]
        return result_right
    
    def __repr__(self):
        if hasattr(self, 'magnitude'):
            return f"{self.__class__.__name__}(magnitude={self.magnitude}, start={self.start}, end={self.end})"
        elif hasattr(self, 'magnitude_start') and hasattr(self, 'magnitude_end'):
            return f"{self.__class__.__name__}(magnitude_start={self.magnitude_start}, magnitude_end={self.magnitude_end}, start={self.start}, end={self.end})"
        else:
            return f"{self.__class__.__name__}(start={self.start}, end={self.end})"
    
    def __tuple__(self):
        return (self.type, self.magnitude, self.start, self.end)

class TriangularLoad(LoadFunctions):
    def __init__(self, magnitude_start: float, magnitude_end: float, start: float, end: float):
        self.magnitude_start = magnitude_start
        self.magnitude_end = magnitude_end
        self.start = start
        self.end = end
        self.range = (start, end)
        self.type = "triangular"

    def load_function(self, x):
        if self.magnitude_start < self.magnitude_end:
            return 1/(self.end-self.start) * self.magnitude_end*(x-self.start)
        else:
            return 1/(self.end-self.start) * self.magnitude_start*(self.end-x)

class UniformLoad(LoadFunctions):
    '''
    Args:
        magnitude: float
        start: float
        end: float
    '''
    def __init__(self, magnitude: float, start: float, end: float):
        self.magnitude = magnitude
        self.start = start
        self.end = end
        self.range = (start, end)
        self.type = "uniform"

    def load_function(self, x):
        return self.magnitude


# class PunctualLoad:
#     def __init__(self, magnitude: float, position: float, effective_width: float = None):
#         if not effective_width:
#             self.magnitude = magnitude
#         else:
#             self.magnitude = magnitude / effective_width
#         self.position = position

#     def load_components_left_span(self,span: float):
#         return (self.magnitude*(self.position)/span * (span**2 -self.position**2))
    
#     def load_components_right_span(self,span: float):
#         return (self.magnitude*(span-self.position)/span * (span**2 -(span-self.position)**2))







