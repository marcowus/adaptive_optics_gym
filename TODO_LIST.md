# 基于自适应光学的红外水分测量系统研究待办事项 (TODO List)

## 1. 理论基础与光学系统设计 (Phase 1: Theoretical Basis & Optical Design)

- [ ] **波长选择 (Wavelength Selection)**
  - [ ] 确定红外水分吸收峰值波长（例如 1.45 µm 或 1.94 µm）。
  - [ ] 选择参考波长（非吸收波段，用于归一化消除反射率差异）。
  - [ ] **任务:** 调研不同物质的水分吸收光谱特性。

- [ ] **光路设计 (Optical Path Design)**
  - [ ] **发射端 (Transmitter):** 定义红外光源（宽带或双波长激光），经由变形镜 (DM) 整形/聚焦。
  - [ ] **目标端 (Target):** 建模目标的反射特性（漫反射 vs 镜面反射）与吸收特性（Beer-Lambert 定律）。
  - [ ] **接收端 (Receiver):** 定义收集光路（单点探测器 vs 焦平面阵列），计算回波功率预算。
  - [ ] **大气传输 (Atmospheric Propagation):** 考虑双程传输（发射+接收）受湍流的影响。

- [ ] **测量原理建模 (Measurement Principle)**
  - [ ] 推导双波长差分吸收测量公式：
    $$ R = \frac{I(\lambda_{ref})}{I(\lambda_{abs})} \propto e^{\alpha(\lambda) \cdot C_{water} \cdot L} $$
  - [ ] 分析湍流引起的闪烁（Scintillation）对光强测量的影响，以及 AO 校正如何提高信噪比 (SNR)。

## 2. 仿真环境升级 (Phase 2: Simulation Environment Upgrade)

- [ ] **多波长传播模拟 (Multi-wavelength Propagation)**
  - [ ] 修改 `AO_env.py` 以支持同时或交替模拟 $\lambda_{ref}$ 和 $\lambda_{abs}$ 的传播。
  - [ ] 确保大气湍流产生的相位畸变 $D_{\phi}(\lambda)$ 随波长正确缩放（色散效应通常可忽略，但衍射效应不同）。

- [ ] **目标反射模型 (Target Reflection Model)**
  - [ ] 新建 `Target` 类，包含空间反射率分布 $\rho(x, y)$ 和水分分布 $W(x, y)$。
  - [ ] 实现光束与目标的相互作用：$U_{refl} = U_{inc} \cdot \rho(x, y) \cdot e^{-\alpha W(x, y)}$。

- [ ] **接收光路模拟 (Receiver Path Simulation)**
  - [ ] 实现从目标反射回接收孔径的传播过程（可能是漫反射导致相干性丧失，需考虑统计光学模型或简化为点源阵列）。
  - [ ] 模拟探测器噪声（热噪声、散粒噪声）。

## 3. 控制算法开发 (Phase 3: Control Algorithm Development)

- [ ] **状态空间定义 (State Space Definition)**
  - [ ] 输入：双波长回波强度、波前传感器数据（如有）、历史控制序列。
  - [ ] 目标：不仅仅是最大化光强，而是最大化 **信噪比 (SNR)** 或 **测量稳定性**。

- [ ] **奖励函数设计 (Reward Function Design)**
  - [ ] 设计新的奖励函数 $r_t$：
    - 选项 A：最大化回波功率 $P_{return}$（提高 SNR）。
    - 选项 B：最小化测量误差 $Error = |C_{measured} - C_{true}|$。
    - 选项 C：保持光斑在目标特定区域的稳定性（抗抖动）。

- [ ] **强化学习训练 (RL Training)**
  - [ ] 训练 PPO/SAC Agent 控制 DM，使得光束能克服湍流，准确聚焦在目标上，或在目标表面进行扫描。
  - [ ] 探究“主动照明”策略：Agent 是否能学会根据回波信号调整光束形状以避开强吸收/强散射区域？

## 4. 实验验证与硬件考量 (Phase 4: Validation & Experiment Design)

- [ ] **仿真验证 (Simulation Validation)**
  - [ ] 对比开环（无 AO）与闭环（有 AO）条件下的水分测量精度。
  - [ ] 分析不同湍流强度 ($D/r_0$) 对测量误差的影响。

- [ ] **硬件选型 (Hardware Selection)**
  - [ ] **光源:** 可调谐红外激光器或宽带光源 + 滤光片。
  - [ ] **变形镜 (DM):** 连续镜面或分段镜面，需覆盖红外波段镀膜。
  - [ ] **探测器:** InGaAs 或 PbS 探测器（针对 NIR/SWIR 波段）。

- [ ] **实验平台搭建 (Experimental Setup)**
  - [ ] 搭建缩比实验系统，使用相位屏模拟湍流，使用湿润样品（如纸张、土壤）作为目标。

## 5. 预期成果 (Expected Outcomes)

1.  一套支持 **主动照明与光谱测量** 的 AO-RL 仿真环境。
2.  验证 AO 技术在 **非成像传感 (Non-imaging Sensing)** 领域的应用潜力。
3.  发表关于“自适应光学增强的红外差分吸收水分测量”的研究论文。
