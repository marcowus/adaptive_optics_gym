
import numpy as np
from hcipy import Field

class Target:
    """
    Simulates a target object with spatially varying reflectivity and moisture content.
    """
    def __init__(self, grid, moisture_base=0.1, reflectivity_base=0.2, reflectivity_var=0.05, moisture_var=0.05):
        """
        Initialize the Target.

        Args:
            grid (hcipy.Grid): The spatial grid on which the target properties are defined.
            moisture_base (float): Base moisture content (fraction).
            reflectivity_base (float): Base reflectivity (fraction).
            reflectivity_var (float): Standard deviation of reflectivity noise.
            moisture_var (float): Standard deviation of moisture noise.
        """
        self.grid = grid

        # Initialize reflectivity map with some random variation (e.g., speckle or surface texture)
        self.reflectivity_map = Field(reflectivity_base + np.random.normal(0, reflectivity_var, grid.size), grid)
        self.reflectivity_map = np.clip(self.reflectivity_map, 0.05, 0.95) # Ensure valid reflectivity

        # Initialize moisture map with some random variation
        self.moisture_map = Field(moisture_base + np.random.normal(0, moisture_var, grid.size), grid)
        self.moisture_map = np.clip(self.moisture_map, 0.0, 1.0) # Ensure valid moisture fraction [0, 1]

    def get_reflectivity(self):
        """Returns the reflectivity map."""
        return self.reflectivity_map

    def get_moisture(self):
        """Returns the moisture map."""
        return self.moisture_map

    def update_moisture(self, delta_moisture):
        """
        Update the moisture map (e.g., drying process).

        Args:
            delta_moisture (float or Field): Change in moisture content.
        """
        self.moisture_map += delta_moisture
        self.moisture_map = np.clip(self.moisture_map, 0.0, 1.0)
