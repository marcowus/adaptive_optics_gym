from gymnasium.envs.registration import register

from IR_Moisture_RL.envs.ir_ao_env import IRAOEnv

register(
    id='IRAO-v0',
    entry_point='IR_Moisture_RL.envs.ir_ao_env:IRAOEnv',
)
