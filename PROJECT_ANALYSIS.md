# 卫星通信自适应光学强化学习环境分析

## 1. 项目概述

本项目是一个用于卫星通信下行链路的自适应光学（Adaptive Optics, AO）强化学习环境。该项目利用 `HCIPy` 库构建物理光学仿真，通过强化学习算法（如 PPO, SAC, DDPG）控制变形镜（Deformable Mirror, DM），以校正大气湍流引起的波前畸变，从而提高单模光纤（Single-Mode Fiber, SMF）的耦合效率。

## 2. 数学原理

该项目的物理仿真基于波动光学（Wave Optics）和傅里叶光学（Fourier Optics）原理。

### 2.1 大气湍流模型 (Atmospheric Turbulence)

大气湍流引起折射率的随机起伏，导致通过大气的平面波前发生相位畸变。本项目采用 **Kolmogorov 湍流模型**。

在此模型中，相位结构函数 $D_{\phi}(\mathbf{r})$ 定义为：

$$
D_{\phi}(\mathbf{r}) = \langle |\phi(\mathbf{x} + \mathbf{r}) - \phi(\mathbf{x})|^2 \rangle = 6.88 \left( \frac{|\mathbf{r}|}{r_0} \right)^{5/3}
$$

其中：
*   $\mathbf{r}$ 是空间位置的差矢量。
*   $r_0$ 是 **Fried 参数**（Fried Parameter），表示大气相干长度。$r_0$ 越大，湍流越弱。
*   $\phi(\mathbf{x})$ 是位置 $\mathbf{x}$ 处的相位。

在大气层模型中，折射率结构常数 $C_n^2$ 与 Fried 参数的关系为（对于平面波）：

$$
r_0 = \left[ 0.423 k^2 \int_{path} C_n^2(z) dz \right]^{-3/5}
$$

其中 $k = 2\pi/\lambda$ 是波数。

代码中使用 `InfiniteAtmosphericLayer` 生成无限长相位屏，模拟风速 $v$ 下的动态湍流（冻结流假设，Frozen Flow Hypothesis）。

### 2.2 波前传播 (Wavefront Propagation)

光波在自由空间中的传播可以通过 **菲涅耳衍射** 或 **夫琅禾费衍射** 来描述。由于卫星通信属于远场传播，且聚焦过程涉及透镜，本项目主要利用傅里叶变换进行传播计算。

从瞳孔平面（Pupil Plane）到焦平面（Focal Plane）的场分布 $U_f(u, v)$ 与瞳孔函数 $U_p(x, y)$ 的关系为二维傅里叶变换：

$$
U_f(u, v) = \frac{1}{i\lambda f} e^{i\frac{k}{2f}(u^2+v^2)} \mathcal{F}\{U_p(x, y)\}_{f_x = \frac{u}{\lambda f}, f_y = \frac{v}{\lambda f}}
$$

在 `HCIPy` 中，`FraunhoferPropagator` 实现了这一传播过程。

### 2.3 变形镜模型 (Deformable Mirror)

变形镜用于产生共轭相位以抵消大气畸变。其相位修正量 $\phi_{DM}(x, y)$ 可以表示为基函数（Modes）的线性组合：

$$
\phi_{DM}(x, y) = \sum_{i=1}^{N} a_i Z_i(x, y)
$$

其中：
*   $a_i$ 是控制系数（动作 Action）。
*   $Z_i(x, y)$ 是基函数，可以是 **Zernike 多项式** 或 **致动器影响函数**（Influence Functions）。
*   $N$ 是模态数或致动器数量。

### 2.4 光纤耦合与斯特尔比 (Fiber Coupling & Strehl Ratio)

#### 光纤耦合效率
单模光纤的耦合效率 $\eta$ 定义为焦平面上的光场 $U_{field}$ 与光纤基模 $U_{fiber}$ 的重叠积分的模平方：

$$
\eta = \frac{\left| \iint U_{field}(u, v) U_{fiber}^*(u, v) du dv \right|^2}{\iint |U_{field}(u, v)|^2 du dv \iint |U_{fiber}(u, v)|^2 du dv}
$$

#### 斯特尔比 (Strehl Ratio)
斯特尔比是衡量光学系统成像质量的重要指标，定义为有像差时的点扩散函数（PSF）峰值强度与无像差（衍射极限）时 PSF 峰值强度的比值：

$$
S = \frac{\max(I_{aberrated})}{\max(I_{ideal})}
$$

## 3. 控制原理

该项目使用 **强化学习 (Reinforcement Learning, RL)** 来实现无波前传感器（Wavefront Sensorless）的自适应光学控制。

### 3.1 控制回路

控制回路如下：
1.  **环境 (Environment)**：光学系统，包括大气湍流、透镜、光纤等。
2.  **观测 (Observation)**：焦平面上的光强分布。
3.  **动作 (Action)**：施加在变形镜上的电压或系数。
4.  **奖励 (Reward)**：耦合效率或斯特尔比。

### 3.2 状态空间 (State Space)

状态 $s_t$ 由焦平面探测器（Photodetector）测量的光强分布组成。为了模拟实际传感器，使用了子采样（Subsampling）的像素阵列（例如 $2 \times 2$ 或 $5 \times 5$）：

$$
s_t = \text{Subsample}(|U_f(u, v)|^2)
$$

这对应于代码中的 `wf_wfs_after_foc_subsample.power`。

### 3.3 动作空间 (Action Space)

动作 $a_t$ 直接控制变形镜的致动器或 Zernike 模态系数：

$$
a_t \in [-1, 1]^N
$$

### 3.4 奖励函数 (Reward Function)

奖励 $r_t$ 旨在最大化光束质量。常用的奖励函数为斯特尔比：

$$
r_t = -(1 - S) \quad \text{或} \quad r_t = S
$$

或者是与单模光纤耦合效率相关的指标。

### 3.5 算法 (Algorithms)

项目支持多种 Model-Free RL 算法：
*   **PPO (Proximal Policy Optimization)**：基于策略梯度，适用于连续动作空间。
*   **SAC (Soft Actor-Critic)**：最大化熵的 Off-policy 算法，具有较好的探索性。
*   **DDPG (Deep Deterministic Policy Gradient)**：适用于连续控制的 Off-policy 算法。

## 4. 关于光电传感器与测量控制的探讨

**问题：** 这个光学结构是不是可以做一个光电传感器，从而我们可以控制测量？

**回答：** **是的，该光学结构本身就构成了一个闭环的光电传感与控制系统。**

详细分析如下：

1.  **光电传感器的角色**：
    在项目中，焦平面上的探测器（`obs_dim` 对应的像素阵列，如 $2 \times 2$ 或 $5 \times 5$ 像素）实际上就是一个 **光电传感器**。它将光信号（焦平面光强分布）转换为电信号（数值矩阵），作为控制系统的输入（State）。

2.  **控制测量的实现**：
    *   **测量对象**：系统的测量对象是光束的质量（即波前畸变的程度），通过焦平面光强分布来间接表征。
    *   **控制机制**：强化学习 Agent 充当控制器，根据光电传感器的读数，计算出变形镜（执行器）所需的控制信号。
    *   **闭环控制**：
        $$ \text{光电传感器 (State)} \xrightarrow{\text{RL Policy}} \text{变形镜 (Action)} \xrightarrow{\text{物理光学}} \text{光束校正} \rightarrow \text{新的传感器读数} $$

    这种结构被称为 **无波前传感器自适应光学 (Wavefront Sensorless AO, WSAO)**。传统的 AO 系统使用 Shack-Hartmann 等专用波前传感器直接测量相位，而本项目利用焦平面光强（光电传感器数据）直接进行优化控制。

3.  **应用推论**：
    *   **作为传感器**：该结构可以作为一个能够感知光束质量和大气湍流强度的“智能传感器”。
    *   **控制测量**：通过控制变形镜改变光路，我们可以主动地探测和补偿系统的像差。例如，通过施加特定的扰动（Dither），观察传感器的响应，可以反推波前相位信息（类似相位差异法 Phase Diversity）。
    *   **扩展应用**：这种架构不仅限于卫星通信，还可以应用于生物显微成像、激光加工等领域，通过光电反馈实时优化焦点质量。

**结论：**
该项目展示的不仅是一个仿真环境，更是一个典型的 **智能光电反馈控制系统** 原型。它证明了利用简单的光电传感器（低像素探测器）结合先进的控制算法（RL），可以实现对复杂光学像差的有效测量与校正。
