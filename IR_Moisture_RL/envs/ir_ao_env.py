
import gymnasium as gym
from gymnasium import spaces
import numpy as np
import matplotlib.pyplot as plt
from hcipy import *
from IR_Moisture_RL.physics_config import *
from IR_Moisture_RL.envs.target import Target

class IRAOEnv(gym.Env):
    """
    Gym Environment for IR Moisture Measurement using Adaptive Optics.

    This environment simulates:
    1.  A dual-wavelength IR source (Reference and Absorption wavelengths).
    2.  Atmospheric turbulence (phase screen).
    3.  A Deformable Mirror (DM) for wavefront correction/shaping.
    4.  Propagation to a Target object.
    5.  Interaction with the Target (Reflectivity and Moisture absorption).
    6.  Measurement of the reflected signal.
    """
    metadata = {'render.modes': ['human']}

    def __init__(self,
                 telescope_diameter=0.5,
                 wavelength_ref=WAVELENGTH_REF * 1e-6,
                 wavelength_abs=WAVELENGTH_ABS * 1e-6,
                 num_actuators=64, # Number of actuators for the DM
                 fried_parameter=0.15,
                 velocity=0.0,
                 target_distance=10.0, # Distance to target
                 grid_size=256,
                 fov=1e-3 # Field of View at target (radians?) or physical size
                 ):
        super(IRAOEnv, self).__init__()

        self.telescope_diameter = telescope_diameter
        self.wavelength_ref = wavelength_ref
        self.wavelength_abs = wavelength_abs
        self.num_actuators = num_actuators
        self.fried_parameter = fried_parameter
        self.velocity = velocity
        self.target_distance = target_distance
        self.grid_size = grid_size

        # --- Optical Setup ---
        # 1. Pupil Plane (Source & DM)
        self.pupil_grid = make_pupil_grid(grid_size, telescope_diameter)
        self.aperture = make_circular_aperture(telescope_diameter)(self.pupil_grid)

        # 2. Deformable Mirror
        # Create influence functions (Gaussian or similar)
        # Using a simple Zernike or Influence function basis
        self.num_modes = num_actuators
        # Example: Zernike modes for simplicity in this initial version, or a regular actuator grid
        # Let's use Zernike for now as it's easier to setup without specific actuator geometry
        # self.dm_modes = make_zernike_basis(num_actuators, telescope_diameter, self.pupil_grid, starting_mode=2)
        # Using influence functions (actuators) as requested in typical AO
        # make_gaussian_influence_functions takes number of actuators across the diameter
        num_actuators_linear = int(np.sqrt(num_actuators))
        actuator_spacing = telescope_diameter / num_actuators_linear
        self.dm_modes = make_gaussian_influence_functions(self.pupil_grid, num_actuators_linear, actuator_spacing)
        self.num_modes = self.dm_modes.num_modes # Update actual number of modes
        self.dm = DeformableMirror(self.dm_modes)

        # 3. Atmosphere
        # Creating a multi-layer atmosphere or single layer
        # Cn^2 profile calculation for r0
        cn_squared = Cn_squared_from_fried_parameter(fried_parameter, 500e-9) # Fried param defined at 500nm typically
        self.atmosphere = InfiniteAtmosphericLayer(self.pupil_grid, cn_squared, 10.0, [velocity, 0])

        # 4. Propagator (Pupil -> Target)
        # Focal grid at the target
        # Calculate focal grid size based on diffraction limit
        f_number = target_distance / telescope_diameter
        spatial_resolution = wavelength_ref * f_number
        self.focal_grid = make_focal_grid(q=4, num_airy=10, spatial_resolution=spatial_resolution) # Adjust as needed

        self.propagator_ref = FraunhoferPropagator(self.pupil_grid, self.focal_grid, focal_length=target_distance)
        self.propagator_abs = FraunhoferPropagator(self.pupil_grid, self.focal_grid, focal_length=target_distance)
        # Note: Fraunhofer is for far-field. Fresnel might be better for near target, but for "remote sensing" Fraunhofer is often OK or use FresnelPropagator if needed.
        # Let's stick to Fraunhofer for simplicity of implementation in gym for now.

        # 5. Target
        self.target = Target(self.focal_grid)

        # --- Gym Spaces ---
        # Action: DM actuator commands
        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(self.num_modes,), dtype=np.float32)

        # Observation:
        # For now, let's assume we observe the Reflected Intensity Signal (2 values: Ref, Abs)
        # and maybe the current DM shape? Or if we have a WFS, the WFS slopes.
        # The prompt implies "sensor detection" -> "control measurement".
        # Let's assume we get the Integrated Intensity at the detector for both wavelengths.
        # And potentially a low-res image if we have a focal plane array.
        # Let's define observation as: [Signal_Ref, Signal_Abs] + [DM_Actuators]
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(2 + self.num_modes,), dtype=np.float32)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.dm.flatten()
        self.atmosphere.reset()
        # Randomize target slightly?
        self.target = Target(self.focal_grid)

        return self._get_obs(), {}

    def step(self, action):
        # Apply action to DM
        self.dm.actuators = action

        # Evolve atmosphere
        self.atmosphere.t += 0.001 # delta_t

        # --- Propagate Reference Beam ---
        wf_ref = Wavefront(self.aperture, self.wavelength_ref)
        wf_ref = self.atmosphere(wf_ref)
        wf_ref = self.dm(wf_ref)
        wf_ref_target = self.propagator_ref(wf_ref)

        # --- Propagate Absorption Beam ---
        wf_abs = Wavefront(self.aperture, self.wavelength_abs)
        wf_abs = self.atmosphere(wf_abs) # Note: Atmosphere phase scales with wavelength automatically in hcipy if using same layer?
        # Actually hcipy InfiniteAtmosphericLayer.phase_for(wavelength) handles dispersion if called explicitly,
        # but calling layer(wf) automatically uses wf.wavelength.
        wf_abs = self.dm(wf_abs)
        wf_abs_target = self.propagator_abs(wf_abs)

        # --- Interaction with Target ---
        # Calculate Intensity at Target
        I_ref_target = wf_ref_target.power
        I_abs_target = wf_abs_target.power

        # Apply Reflection and Absorption
        # Reflected Power = Incident * Reflectivity * exp(-alpha * moisture * path_length)
        # Path length L -> interaction depth. Let's assume effective path length factor 'L_eff'
        L_eff = 0.1 # cm, hypothetical interaction depth

        # Absorption factor
        attenuation_ref = np.exp(-ALPHA_WATER_REF * self.target.get_moisture() * L_eff)
        attenuation_abs = np.exp(-ALPHA_WATER_ABS * self.target.get_moisture() * L_eff)

        # Reflected Intensity Map
        I_ref_reflected = I_ref_target * self.target.get_reflectivity() * attenuation_ref
        I_abs_reflected = I_abs_target * self.target.get_reflectivity() * attenuation_abs

        # --- Detection (Bucket Detector) ---
        # Integrate over the target area (assuming all reflected light is collected or a constant fraction)
        Signal_Ref = np.sum(I_ref_reflected)
        Signal_Abs = np.sum(I_abs_reflected)

        # --- Reward Calculation ---
        # Goal: Maximize Signal to Noise Ratio? Or Maximize Stability?
        # The prompt mentions "calculate the object's moisture content".
        # So the "Control" might be to maximize the signal strength (focus) to get a better reading.
        # Reward = Signal_Ref (Maximize return signal)
        # Or Reward = - |Measured_Moisture - True_Moisture| (if we knew truth, for training)

        # Let's calculate "Measured Moisture"
        # Ratio R = Signal_Ref / Signal_Abs
        # R ~ exp( (alpha_abs - alpha_ref) * C * L )
        # ln(R) ~ (alpha_abs - alpha_ref) * C * L
        # C ~ ln(R) / ( (alpha_abs - alpha_ref) * L )

        ratio = Signal_Ref / (Signal_Abs + 1e-9)
        measured_moisture_avg = np.log(ratio) / ((ALPHA_WATER_ABS - ALPHA_WATER_REF) * L_eff)

        # True moisture (weighted by intensity? Average over illuminated area?)
        # This is tricky because moisture varies spatially.
        # Let's use total signal intensity as the reward for now (Standard AO goal: Focus light).
        reward = float(Signal_Ref)

        terminated = False
        truncated = False
        info = {
            "signal_ref": float(Signal_Ref),
            "signal_abs": float(Signal_Abs),
            "measured_moisture": float(measured_moisture_avg),
            "ratio": float(ratio)
        }

        self.last_obs = np.concatenate(([Signal_Ref, Signal_Abs], self.dm.actuators)).astype(np.float32)
        return self.last_obs, reward, terminated, truncated, info

    def _get_obs(self):
        # For initial reset, we can just return zeros or do a simplified step
        # Let's return zeros for signals and current actuators
        return np.concatenate(([0.0, 0.0], self.dm.actuators)).astype(np.float32)

    def render(self):
        # Visualize the target and the beam
        pass
