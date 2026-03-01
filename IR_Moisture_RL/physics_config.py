# IR Moisture RL Physics Configuration

# Wavelengths in micrometers
WAVELENGTH_REF = 1.3  # Reference wavelength (low water absorption)
WAVELENGTH_ABS = 1.45 # Absorption wavelength (high water absorption)

# Absorption Coefficients for Water (cm^-1)
# Note: These are approximate values. Need to be verified with literature.
ALPHA_WATER_REF = 0.5   # Absorption at reference wavelength
ALPHA_WATER_ABS = 25.0  # Absorption at absorption wavelength

# Reflectivity Parameters (Typical values)
REFLECTIVITY_BASE = 0.2 # Base reflectivity of the target material (e.g., paper/soil)
REFLECTIVITY_VARIATION = 0.05 # Variation in reflectivity due to surface roughness/inhomogeneity

# Moisture Content Parameters (Typical range)
MOISTURE_MIN = 0.0 # Dry (0%)
MOISTURE_MAX = 0.5 # Saturated (50%)
