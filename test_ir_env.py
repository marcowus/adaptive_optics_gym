
import gymnasium as gym
import numpy as np
import matplotlib.pyplot as plt
import IR_Moisture_RL.envs  # This registers the env

def test_environment():
    print("Testing IR Moisture AO Environment...")
    env = gym.make('IRAO-v0',
                   telescope_diameter=0.5,
                   num_actuators=64,
                   fried_parameter=0.15,
                   target_distance=100.0) # Far field

    obs, _ = env.reset()
    print("Initial Observation shape:", obs.shape)
    print("Action Space shape:", env.action_space.shape)

    # Random Action
    action = env.action_space.sample()
    obs, reward, terminated, truncated, info = env.step(action)

    print("Observation after step:", obs[:2]) # First 2 are signals
    print("Reward:", reward)
    print("Info:", info)

    # Visualize Target
    try:
        from hcipy import imshow_field
        plt.figure(figsize=(10, 5))

        plt.subplot(1, 2, 1)
        plt.title("Target Reflectivity")
        imshow_field(env.unwrapped.target.get_reflectivity(), cmap='gray')
        plt.colorbar()

        plt.subplot(1, 2, 2)
        plt.title("Target Moisture")
        imshow_field(env.unwrapped.target.get_moisture(), cmap='Blues')
        plt.colorbar()

        plt.tight_layout()
        plt.savefig('target_visualization.png')
        print("Target visualization saved to target_visualization.png")
    except Exception as e:
        print("Visualization failed:", e)

    env.close()
    print("Test Complete.")

if __name__ == "__main__":
    test_environment()
