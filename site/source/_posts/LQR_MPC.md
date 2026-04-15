---
title: 最优控制：LQR与MPC
date: 2026-4-15
categories:
  - 笔记
tags:
  - 最优控制
  - LQR
  - MPC
  - Robomaster
math: true
cover: cover.jpg
permalink: /notes/LQR_MPC/
---
# 从 LQR 到 MPC，再到 NMPC
### ——从最优控制到现代机器人控制方法

---

## 一、引言

对于现代的很多控制系统，我们已经不再满足于系统能否安全正常运行，而更关心它们的运行是否高效，以及是否达到了 **效率和能耗的最优**。由此，我们引入了最优控制理论。最优控制不仅关心如何使系统保持稳定，更关心如何在保持稳定的同时，使得系统的某些性能指标达到最优。  

在最优控制理论的发展过程中，针对线性系统与二次型性能指标的优化问题，诞生了一种最具代表性且具有解析解的经典方法——**线性二次型调节器（Linear Quadratic Regulator, LQR）**。LQR不仅为最优控制提供了严谨的数学基础，也为后续模型预测控制(MPC)的发展奠定了理论基石。  

事实上，LQR与MPC之间存在着深刻的理论联系。LQR为线性系统提供了具有解析解的无限时域最优控制律，而MPC则通过滚动时域优化，将最优控制思想扩展至有限时域，并能够显式处理系统约束。  

在 **无约束条件下，当预测时域趋于无穷，且终端权重取为黎卡提方程的解时，MPC将退化为LQR**。因此，可以认为LQR是MPC在特定条件下的特例，而MPC则是LQR在约束条件和在线优化框架下的推广。这种关系构成了现代最优控制理论的重要桥梁，并为机器人与自动驾驶系统中的控制算法设计提供了统一的理论基础。

## 二、离散型线性二次系统（离散型 LQR）

### 0、问题定义

首先,让我们从最简单的例子出发，考虑一个离散型线性系统：

$$
x_{k+1} = A x_k + B u_k
$$

其中，$x_k \in \mathbb{R}^n$ 是状态，$u_k \in \mathbb{R}^m$ 是控制输入。

我们希望在保证系统稳定的同时，最小化如下二次型性能指标：

$$
J = \sum_{k=0}^{\infty} \left( x_k^T Q x_k + u_k^T R u_k \right)
$$

其中：

- $Q \succeq 0$：状态误差权重矩阵，通常设计为对角阵
- $R \succ 0$：控制输入权重矩阵，通常也设计为对角阵

这个目标函数很好理解：

- $x_k^TQx_k$ 惩罚“偏离目标”的程度
- $u_k^TRu_k$ 惩罚“控制动作过猛”而消耗过多能量

### 1、为什么最优控制律会是线性反馈

这个问题的关键在于：

- 系统是线性的
- 代价是二次型

在这种“线性 + 二次型”的结构下，最优值函数天然也会是二次型。设：

$$
V(x_k) = x_k^T P x_k
$$
>注：为什么这里可以设 $V(x_k)=x_k^TPx_k$？
>
>可以用有限时域的 Bellman 递推做一个归纳证明。即：
>$$
>J = \sum_{k=0}^{N-1} \left( x_k^T Q x_k + u_k^T R u_k \right) + x_N^TSx_N
>$$
>其中$S \succeq 0$为末端代价权重矩阵，他通常也是对角阵。
>
>先令终端代价为：
>$$
>V_N(x)=x^TP_Nx
>$$
>
>假设第 $k+1$ 步值函数也是二次型：
>$$
>V_{k+1}(x)=x^TP_{k+1}x
>$$
>
>则根据Bellman方程，第 $k$ 步有：
>$$
>V_k(x)=\min_u\left(x^TQx+u^TRu+V_{k+1}(Ax+Bu)\right)
>$$
>$$
>=\min_u\left(x^TQx+u^TRu+(Ax+Bu)^TP_{k+1}(Ax+Bu)\right)
>$$
>
>把最后一项展开：
>$$
>(Ax+Bu)^TP_{k+1}(Ax+Bu)
>=(Ax)^TP_{k+1}Ax + 2(Ax)^TP_{k+1}Bu + (Bu)^TP_{k+1}Bu
>$$
>
>因此关于 $u$ 的部分可以整理成：
>$$
>J(u)=u^T\underbrace{\left(R+B^TP_{k+1}B\right)}_{M}u
>+2\underbrace{\left(B^TP_{k+1}Ax\right)^T}_{d(x)^T}u
>+\text{const}
>$$
>
>所以其 Hessian 为：
>$$
>\nabla_u^2J = 2\left(R+B^TP_{k+1}B\right)
>$$
>在 $R\succ0$ 且 $P_{k+1}\succeq0$ 时，$B^TP_{k+1}B\succeq0$，从而
>$$
>R+B^TP_{k+1}B \succ 0
>$$
>故 $J(u)$ 对 $u$ 严格凸，极小点唯一。
>
>令梯度为零：
>$$
>\nabla_uJ = 2\left(R+B^TP_{k+1}B\right)u + 2B^TP_{k+1}Ax = 0
>$$
>解得：
>$$
>u^*=-K_kx,
>\quad
>K_k=(R+B^TP_{k+1}B)^{-1}B^TP_{k+1}A
>$$
>
>把 $u^*$ 代回去，$V_k(x)$ 仍然是关于 $x$ 的二次型：
>$$
>V_k(x)=x^TP_kx
>$$
>其中 $P_k$ 满足 Riccati 递推。由此完成归纳。
>
>当时域趋于无穷并满足稳定性条件时，$P_k\to P$，因此无限时域可写成：
>$$
>V(x)=x^TPx
>$$

将其代入 Bellman 最优性方程：

$$
V(x_k) = \min_{u_k} \left( x_k^TQx_k + u_k^TRu_k + V(x_{k+1}) \right)
$$

又因为 $x_{k+1}=Ax_k+Bu_k$，整理得到：

$$
V(x_k)=\min_{u_k}\Big[x_k^TQx_k+u_k^TRu_k+(Ax_k+Bu_k)^TP(Ax_k+Bu_k)\Big]
$$

对 $u_k$ 求偏导并令其为零：

$$
2\left(R+B^TPB\right)u_k + 2B^TPAx_k = 0
$$

得到最优控制律：

$$
u_k^* = -Kx_k,
\quad
K = \left(R + B^T P B\right)^{-1} B^T P A
$$

这就是经典的 LQR 反馈形式。

### 2、离散代数Riccati方程（DARE）

把最优控制律再代回 Bellman 方程，可以得到 $P$ 需要满足：

$$
P = Q + A^TPA - A^TPB\left(R+B^TPB\right)^{-1}B^TPA
$$

这就是离散代数黎卡提方程（DARE）。

求解流程通常是：

1. 给定系统矩阵 $A,B$ 和权重 $Q,R$
2. 数值求解 DARE 得到 $P$
3. 计算反馈增益 $K$
4. 在线控制使用 $u_k=-Kx_k$

---

## 三、连续型线性二次系统（连续型 LQR）

离散型 LQR 常用于数字控制器实现，而连续型 LQR 更像理论“母版”。

### 1、系统模型与目标函数

考虑连续时间线性系统：

$$
\dot{x}(t) = A x(t) + B u(t)
$$

目标函数写为：

$$
J = \int_0^{\infty} \left(x^TQx + u^TRu\right)dt
$$

其中仍有 $Q\succeq0, R\succ0$。

### 2、从HJB 到 CARE

设最优值函数：

$$
V(x)=x^TPx
$$

其中 $P=P^T\succeq0$。这个设定背后的理由与离散情形一致：在线性系统 + 二次代价结构下，值函数对 Bellman/HJB 算子是二次型闭包。

先给出 HJB（Hamilton-Jacobi-Bellman）条件。对无限时域连续系统

$$
\dot{x}=f(x,u),\qquad \ell(x,u)=x^TQx+u^TRu
$$

最优值函数满足

$$
0 = \min_u \Big(\ell(x,u)+\nabla V(x)^T f(x,u)\Big)
$$

这条式子可以理解为：在最优策略下，"瞬时代价" + "未来最优代价变化率" 的和达到最小并等于 0。

把中括号内定义为哈密顿函数（Hamiltonian）：

$$
\mathcal{H}(x,u,\nabla V)=\ell(x,u)+\nabla V(x)^Tf(x,u)
$$

它的物理意义是“当前这一瞬间的总成本密度”，包含两部分：

- $\ell(x,u)$：眼前付出的控制与状态代价
- $\nabla V^Tf$：状态沿动力学演化时，剩余最优代价的变化率

对于 LQR，$f(x,u)=Ax+Bu$，且

$$
\nabla V(x)=2Px
$$

所以

$$
\nabla V^Tf = 2x^TP(Ax+Bu)
$$

等价写法是把这部分记成

$$
\dot{V}=x^T(A^TP+PA)x+2x^TPBu
$$

因此 HJB 可写为：

$$
0 = \min_u \left(x^TQx + u^TRu + x^T(A^TP+PA)x+2x^TPBu\right)
$$

对 $u$ 求偏导并令其为零：

$$
\frac{\partial \mathcal{H}}{\partial u}=2Ru+2B^TPx=0
$$

得到最优控制律：

$$
u^* = -R^{-1}B^TPx = -Kx
$$

代回 HJB：

$$
0=x^T\Big(Q+A^TP+PA-PBR^{-1}B^TP\Big)x
$$

由于该式对任意 $x$ 都成立，括号内矩阵必须为零，于是得到连续代数黎卡提方程（CARE）：

$$
A^TP + PA - PBR^{-1}B^TP + Q = 0
$$

于是连续 LQR 增益为：

$$
K = R^{-1}B^TP
$$

CARE 的作用可以理解为：它是“把最优控制问题变成矩阵方程”的桥梁。只要解出稳定化解 $P$，就能立刻得到最优反馈增益 $K$。因此连续 LQR 的工程流程通常是：先解 CARE，再上线性状态反馈 $u=-Kx$。

### 3、离散与连续的关系

实际控制器常以采样周期 $\Delta t$ 运行。将连续系统离散化可得：

$$
A_d=e^{A\Delta t},
\quad
B_d=\int_0^{\Delta t}e^{A\tau}B\,d\tau
$$

然后直接在离散域做 LQR 设计，这也是机器人控制里最常见的流程。

---

## 四、模型预测控制（MPC）

### 0、先说清楚：MPC 到底在做什么

MPC（Model Predictive Control）不是一条固定控制公式，而是一种“在线滚动优化”方法：

1. 用模型预测未来 $N$ 步状态
2. 在所有可行控制序列中找最优
3. 只执行第一步控制
4. 下一采样时刻重新优化

这 4 步不断循环，就是 MPC 的核心。


### 1、从线性离散系统开始

系统模型：

$$
x_{k+1}=Ax_k+Bu_k
$$

常用的跟踪型代价函数：

$$
J = \sum_{i=0}^{N-1}\left[(x_i-x_{ref})^TQ(x_i-x_{ref}) + u_i^TRu_i\right] + (x_N-x_{ref})^TP(x_N-x_{ref})
$$

解释：

- $Q$ 大：更在乎跟踪误差
- $R$ 大：更在乎控制平滑
- $P$：保证预测末端别“散”掉

### 2、把未来状态一步一步展开

从当前状态 $x_0$ 出发：

$$
x_1 = Ax_0 + Bu_0
$$

$$
x_2 = A^2x_0 + ABu_0 + Bu_1
$$

$$
x_3 = A^3x_0 + A^2Bu_0 + ABu_1 + Bu_2
$$

归纳可得：

$$
x_i = A^ix_0 + \sum_{j=0}^{i-1}A^{i-1-j}Bu_j
$$

这一步是线性 MPC 推导的核心：未来状态被显式写成“当前状态 + 控制序列”的函数。

### 3、堆叠写成矩阵形式

定义：

$$
X = \begin{bmatrix}x_1\\x_2\\\vdots\\x_N\end{bmatrix},
\quad
U = \begin{bmatrix}u_0\\u_1\\\vdots\\u_{N-1}\end{bmatrix}
$$

则有：

$$
X = \mathcal{A}x_0 + \mathcal{B}U
$$

其中：

$$
\mathcal{A}=
\begin{bmatrix}
A\\A^2\\\vdots\\A^N
\end{bmatrix}
$$

$$
\mathcal{B}=
\begin{bmatrix}
B & 0 & \cdots & 0 \\
AB & B & \cdots & 0 \\
\vdots & \vdots & \ddots & \vdots \\
A^{N-1}B & A^{N-2}B & \cdots & B
\end{bmatrix}
$$

$\mathcal{B}$ 是下三角块矩阵，直观含义是“越早的控制会影响越远的未来”。

### 4、写成标准二次规划（QP）

定义参考堆叠向量和块对角权重：

$$
X_{ref} = \begin{bmatrix}x_{ref,1}\\x_{ref,2}\\\vdots\\x_{ref,N}\end{bmatrix}
$$

$$
\bar{Q}=\mathrm{diag}(Q,Q,\dots,Q,P),
\quad
\bar{R}=\mathrm{diag}(R,R,\dots,R)
$$

总代价：

$$
J = (X-X_{ref})^T\bar{Q}(X-X_{ref}) + U^T\bar{R}U
$$

代入 $X=\mathcal{A}x_0+\mathcal{B}U$，可整理为：

$$
J(U)=\frac{1}{2}U^THU + g^TU + c
$$

其中：

$$
H = 2(\mathcal{B}^T\bar{Q}\mathcal{B}+\bar{R})
$$

$$
g = 2\mathcal{B}^T\bar{Q}(\mathcal{A}x_0-X_{ref})
$$

$c$ 与 $U$ 无关，可以在优化时忽略。

于是线性 MPC 在线求解问题成为：

$$
\min_U \frac{1}{2}U^THU + g^TU
$$

若再加入约束：

$$
x_{min}\le x_k \le x_{max},
\quad
u_{min}\le u_k \le u_{max}
$$

堆叠后可统一写成：

$$
GU \le h + Ex_0
$$

这就是标准二次规划（QP）问题。每个采样周期求一次 QP，执行第一项 $u_0^*$，再滚动到下一时刻。

### 5、一个最小直观例子

考虑离散时间线性系统：

$$
x_{k+1} = A x_k + B u_k
$$

其中：

$$
A =
\begin{bmatrix}
1 & \Delta t \\
0 & 1
\end{bmatrix}, \quad
B =
\begin{bmatrix}
\frac{1}{2}\Delta t^2 \\
\Delta t
\end{bmatrix}
$$

状态向量与控制输入分别为：

$$
x_k =
\begin{bmatrix}
p_k \\
v_k
\end{bmatrix}, \quad
u_k = a_k
$$

其中 $p_k$ 表示位置，$v_k$ 表示速度，$a_k$ 表示加速度。

设预测时域为 $N=3$，参考状态为 $x_{\text{ref}}$。

**可以自行练习,求：**

1. 写出 $x_1, x_2, x_3$；
2. 构造预测模型 $X = \mathcal{A}x_0 + \mathcal{B}U$
3. 写出MPC的二次型优化目标函数。


---

## 五、非线性模型预测控制（NMPC）

### 0、为什么线性 MPC 会走向 NMPC

现在开始最关键的问题：为什么线性 MPC 会变成 NMPC？

答案很简单：因为真实系统往往不是线性的。

线性 MPC 建立在：

$$
x_{k+1}=Ax_k+Bu_k
$$

但很多机器人不是这样。以差速底盘（独轮车模型）为例：
$$
\dot p_x=v\cos\theta,\quad \dot p_y=v\sin\theta,\quad \dot\theta=\omega
$$

离散化后：

$$
p_{x,k+1}=p_{x,k}+\Delta t\,v_k\cos\theta_k
$$
$$
p_{y,k+1}=p_{y,k}+\Delta t\,v_k\sin\theta_k
$$
$$
\theta_{k+1}=\theta_k+\Delta t\,\omega_k
$$

显然它不是 $Ax_k+Bu_k$，因此更一般地写成：

$$
x_{k+1}=f(x_k,u_k)
$$

这就是 NMPC 的起点。

### 1、NMPC 的标准优化问题

和线性 MPC 很像，只是模型变成非线性：

$$
\min_{\{x_k,u_k\}}J=
\sum_{k=0}^{N-1}\Big[(x_k-x_k^{ref})^TQ(x_k-x_k^{ref})+(u_k-u_k^{ref})^TR(u_k-u_k^{ref})\Big]
+(x_N-x_N^{ref})^TP(x_N-x_N^{ref})
$$

约束：

$$
x_{k+1}=f(x_k,u_k),\quad k=0,\dots,N-1
$$
$$
u_{min}\le u_k\le u_{max},\qquad x_{min}\le x_k\le x_{max}
$$
$$
h(x_k,u_k)\le0
$$

因此 NMPC 的标准形式是一个非线性规划（NLP）。

### 2、NMPC 和线性 MPC 最本质的区别

不是“多了个 N”，也不是“换了个求解器”，而是：

- 在线性 MPC 里，未来状态可显式消元：$X=\mathcal{A}x_0+\mathcal{B}U$
- 在 NMPC 里，一般不能写成这种线性显式形式

所以线性 MPC 通常是 QP，NMPC 通常是 NLP。

### 3、先用 Single Shooting 理解 NMPC

Single Shooting 是最直观的入门方式：

1. 把控制序列 $U=\{u_0,u_1,\dots,u_{N-1}\}$ 作为优化变量
2. 给定当前状态 $x_0$，按动力学递推：
$$
x_1=f(x_0,u_0),\;x_2=f(x_1,u_1),\;\dots,\;x_N=f(x_{N-1},u_{N-1})
$$
3. 于是状态成为控制序列的函数：
$$
x_k=\phi_k(x_0,u_0,\dots,u_{k-1})
$$
4. 代价函数变成 $J(U)$，对 $U$ 做数值优化

关键点在于：$J(U)$ 一般不再是二次函数，而是非线性函数。

### 4、差速底盘的 NMPC 求解（运动学模型）

#### 4.1 状态、控制与模型

状态：

$$
x_k=
\begin{bmatrix}
p_{x,k}\\
p_{y,k}\\
\theta_k
\end{bmatrix}
$$

控制：

$$
u_k=
\begin{bmatrix}
v_k\\
\omega_k
\end{bmatrix}
$$

离散模型：

$$
p_{x,k+1}=p_{x,k}+\Delta t\,v_k\cos\theta_k
$$
$$
p_{y,k+1}=p_{y,k}+\Delta t\,v_k\sin\theta_k
$$
$$
\theta_{k+1}=\theta_k+\Delta t\,\omega_k
$$

#### 4.2 代价函数设计

$$
J=
\sum_{k=0}^{N-1}\Big[(x_k-x_k^{ref})^TQ(x_k-x_k^{ref})+u_k^TRu_k\Big]
+(x_N-x_N^{ref})^TP(x_N-x_N^{ref})
$$

若需要更平滑控制，可加入：

$$
\sum_{k=0}^{N-2}(u_{k+1}-u_k)^TS(u_{k+1}-u_k)
$$

#### 4.3 约束设计

输入约束：

$$
v_{min}\le v_k\le v_{max},\qquad
\omega_{min}\le\omega_k\le\omega_{max}
$$

障碍约束（圆形障碍示例）：

$$
h_{obs}(x_k) =(r_{obs}+r_{safe})^2 - ( (p_{x,k}-p_x^{obs})^2+(p_{y,k}-p_y^{obs})^2 ) \le 0
$$

#### 4.4 NLP 转录（Single Shooting）

以控制序列 $U$ 为决策变量：

$$
\min_U J(U)
$$

subject to

$$
x_{k+1}=f(x_k,u_k),\quad x_0=\hat{x}(t)
$$

以及输入/障碍等约束。

#### 4.5 在线滚动求解流程

每个采样时刻执行：

1. 读取当前状态估计 $\hat{x}(t)$
2. 用上一时刻最优解平移作 warm-start
3. 用系统模型滚动预测状态轨迹
4. 计算总代价与约束
5. 用 SQP / IPOPT / ACADOS 迭代求解 NLP
6. 取第一步控制 $u_0^*$ 下发给底盘
7. 时域前移，进入下一轮优化

这就是 NMPC 的 receding horizon 闭环。


### 5、为什么 NMPC 通常没有解析解

NMPC 最终面对的是

$$
\min_U J(U)
$$

但 $J(U)$ 由非线性递推 $x_{k+1}=f(x_k,u_k)$ 隐式定义，还叠加了非线性约束。通常没有闭式解，只能靠数值优化迭代求近似最优解。

### 6、线性化是连接线性 MPC 与 NMPC 的桥梁

对非线性系统在工作点 $(x^*,u^*)$ 附近做一阶泰勒展开：

$$
f(x,u)\approx
f(x^*,u^*)+
\left.\frac{\partial f}{\partial x}\right|_{x^*,u^*}(x-x^*)+
\left.\frac{\partial f}{\partial u}\right|_{x^*,u^*}(u-u^*)
$$

设 $\delta x=x-x^*,\delta u=u-u^*$，得到局部线性时变模型：

$$
\delta x_{k+1}\approx A_k\delta x_k+B_k\delta u_k
$$

其中

$$
A_k=\left.\frac{\partial f}{\partial x}\right|_{x^*,u^*},\qquad
B_k=\left.\frac{\partial f}{\partial u}\right|_{x^*,u^*}
$$

这也是很多快 NMPC 方法（Sequential QP / RTI）的核心思想：每个采样时刻在线性化，再解局部 QP。

## 六、LQR 与 MPC 的联系

现在，在完成对LQR和MPC的全面了解后，让我们回过头去观察两者的异同。

### 1. 统一的最优控制框架

LQR与MPC均源于线性系统的二次型性能指标优化问题。对于离散时间系统：

$$
x_{k+1} = A x_k + B u_k
$$

两者的目标函数分别为：

LQR（无限时域）：
$$
J = \sum_{k=0}^{\infty} \left( x_k^T Q x_k + u_k^T R u_k \right)
$$
MPC（有限时域）：
$$
J = \sum_{k=0}^{N-1} \left( x_k^T Q x_k + u_k^T R u_k \right) + x_N^T P x_N
$$

可以看出，MPC是对LQR无限时域问题的截断与近似。


### 2. 终端权重与黎卡提解

当终端权重矩阵取为离散代数黎卡提方程（DARE）的解时：
$$
P = P_{LQR}
$$
终端代价满足：
$$
x_N^T P x_N
$$
该项等价于系统从预测末端开始，在无限时域内由最优LQR控制器继续控制所产生的最小剩余代价（Cost-to-Go）。因此，终端项实际上是无限时域最优值函数的解析表达。

### 3. MPC 收敛于 LQR 的条件

在满足以下条件时，MPC与LQR等价：

1. 系统为线性且时不变；
2. 不存在输入与状态约束；
3. 终端权重取为黎卡提方程的解；
4. 预测时域趋于无穷；
5. 权重矩阵保持一致。

此时，MPC的最优控制律为：
$$
u_k = -K x_k
$$
其中，$K$为LQR反馈增益矩阵。因此，LQR = 无约束、无限时域的 MPC。


### 4. 控制策略的本质差异

| 对比维度 | LQR | MPC |
|----------|-----|-----|
| 优化时域 | 无限时域 | 有限时域 |
| 控制律形式 | 固定状态反馈 u = -Kx | 在线优化得到 |
| 增益矩阵 | 常数 | 时变 |
| 是否滚动优化 | 否 | 是 |
| 是否显式预测未来 | 隐式 | 显式 |
| 是否处理约束 | 否 | 是 |
| 求解方式 | 离线解析解 | 在线数值优化 |
| 计算复杂度 | 低 | 较高 |

---

## 参考文献
王天威、黄军魁，《控制之美 卷2：最优控制与模型预测控制》。  
J. B. Rawlings, D. Q. Mayne, and M. Diehl, *Model Predictive Control: Theory, Computation, and Design*.  
D. P. Bertsekas, *Dynamic Programming and Optimal Control*.
