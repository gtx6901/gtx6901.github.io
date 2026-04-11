---
title: MaCA 强化学习从零到工程实践指南
date: 2026-04-11
categories:
  - 笔记
tags:
  - 强化学习
math: true
permalink: /notes/MaCA_RL/
---
# MaCA 强化学习从零到工程实践指南

> !AI GENERATED!

这份文档是给当前项目量身定做的 RL 主学习文档。   

>[项目地址](https://github.com/gtx6901/MaCA-project)


它的目标不是只告诉你“命令怎么敲”，而是帮助你建立一条连贯的理解链：

1. 你现在到底在解决什么控制问题。
2. 为什么这个问题会自然走到强化学习。
3. 为什么这类问题里 `DQN` 容易吃力，而 `PPO / APPO + LSTM` 更合理。
4. 这套工程里的每个 RL 组件在数学上是什么、在直觉上是什么、在代码里又落在哪里。
5. 你以后看到日志、checkpoint、reward 曲线时，脑子里应该怎么解释。

如果你是第一次系统接触 RL，不建议从中间挑一章硬啃。最好的方式是顺序读。

---

## 0. 先说一句最重要的话

你现在做的不是“学一个算法名字”，而是在学一套完整的方法论：

- 如何把一个复杂的动态决策问题形式化；
- 如何设计可学习的观测、动作、奖励；
- 如何选择合适的函数逼近器；
- 如何在有限算力和不完美环境里做稳定训练；
- 如何从日志和失败中反推系统问题。

从这个角度看，强化学习不是某个公式，而是一门“控制 + 统计 + 优化 + 软件工程”的综合课。

---

## 1. 这个项目到底在做什么

先把问题说人话。

你现在有一个空战仿真环境 `MaCA`。

在当前这条训练路线里：

- 红方有 `10` 架战斗机；
- 蓝方是固定规则对手，例如 `fix_rule`；
- 你每一步都要给红方每架飞机一个离散动作；
- 环境推进一步后，会返回新的观测、奖励，以及这一局是否结束。

你希望学出的不是“单步看起来聪明”的动作，而是能在整局博弈里取得更高长期收益的策略。

如果用自动化里更熟悉的话说：

- 这不是一个固定参考轨迹跟踪问题；
- 也不是一个已知模型下的最优控制问题；
- 而是一个“模型复杂、观测不全、对手在动、目标多阶段耦合”的闭环决策问题。

这也是为什么它很像控制，又不完全等于传统控制。

---

## 2. 先复习你已经学过的东西

这一步很重要。很多 RL 名词看起来陌生，但骨架并不陌生。

### 2.1 状态、输入、输出、反馈

在自动控制里，你已经习惯了：

- 系统有内部状态；
- 控制器根据输出或观测做决策；
- 输入会影响状态演化；
- 最终形成闭环。

RL 里只是把这件事推广成：

- 系统状态不一定能完全观测；
- 系统动力学不一定显式已知；
- 控制目标不一定是单个稳态误差，而可能是长期累积收益。

所以从控制视角看，RL 就是在做：

- 观测驱动的闭环策略优化。

### 2.2 代价函数和最优控制

你可能在最优控制或 MPC 里见过类似目标：

\[
J = \sum_{t=0}^{T} \ell(x_t, u_t)
\]

意思是：我们不只看当前一步，而是看整个时间区间的累计代价。

RL 的目标形式非常像，只不过通常写成“累计奖励最大化”而不是“累计代价最小化”：

\[
J = \mathbb{E}\left[\sum_{t=0}^{T} r_t\right]
\]

如果把奖励改成负代价，本质是一回事。

### 2.3 梯度下降和参数优化

你已经知道神经网络训练本质是：

- 定义一个损失函数；
- 对参数求梯度；
- 用梯度下降或 Adam 之类的优化器更新参数。

RL 里仍然是这套机器。

区别在于：

- 监督学习的标签通常是现成的；
- RL 的“标签”来自和环境交互出来的数据，而且这个标签本身还依赖你当前的策略。

这会让 RL 比普通监督学习更不稳定。

### 2.4 概率和期望

RL 几乎所有公式里都离不开两个词：

- 随机变量；
- 期望。

因为：

- 策略可能是随机的；
- 环境转移可能带随机性；
- 对手也会造成不确定性；
- 我们最终优化的是“平均意义下的长期表现”。

所以你看到

\[
\mathbb{E}[\cdot]
\]

不要紧张，它只是“平均来看”。

### 2.5 偏差和方差

后面你会反复看到一个经典张力：

- 偏差小，方差大；
- 方差小，偏差大。

这在控制、估计、统计里都常见。

RL 里的很多技巧，比如：

- baseline；
- TD；
- GAE；
- V-trace；

本质上都在做偏差-方差折中。

---

## 3. 什么是强化学习

最朴素地说：

- 观察当前情况；
- 采取动作；
- 环境给出反馈；
- 根据长期结果，逐渐调整策略。

它和监督学习最不同的一点是：

- 监督学习有现成标准答案；
- RL 没有“老师直接告诉你正确动作”，只有结果反馈。

所以 RL 解决的是：

- “怎么试错，并从试错中学到长期更优的决策规则”。

---

## 4. 用数学语言把 RL 形式化

### 4.1 MDP：马尔可夫决策过程

最标准的形式化对象是 MDP。

一个 MDP 通常包含：

- 状态 \(s_t\)
- 动作 \(a_t\)
- 状态转移 \(P(s_{t+1}\mid s_t, a_t)\)
- 即时奖励 \(r_t\)
- 折扣因子 \(\gamma\)

马尔可夫性的意思是：

- 在理想建模里，未来只由当前状态和当前动作决定；
- 不需要额外关心更久远的历史。

这是一个建模假设，不是世界的真理。

### 4.2 POMDP：部分可观测 MDP

你这个项目更接近 POMDP，而不是标准 MDP。

因为实际策略看不到完整状态，只能看到观测 \(o_t\)：

\[
o_t \sim \mathcal{O}(s_t)
\]

也就是说：

- 世界里有真实战场状态；
- 但每架飞机只能看到局部图像、少量向量信息和合法动作 mask；
- 所以策略输入不是 \(s_t\)，而是 \(o_t\)。

这件事后面会直接决定：

- 为什么需要 `LSTM`；
- 为什么单步 DQN 很容易不够；
- 为什么“记忆”在空战里特别重要。

### 4.3 Trajectory：轨迹

一局游戏的数据可以写成轨迹：

\[
\tau = (o_0, a_0, r_0, o_1, a_1, r_1, \dots)
\]

训练其实就是不断采样这样的轨迹，然后根据轨迹更新参数。

### 4.4 Return：回报

某一时刻开始的折扣累计回报定义为：

\[
G_t = r_t + \gamma r_{t+1} + \gamma^2 r_{t+2} + \cdots
\]

它的含义非常重要：

- 当前动作好不好，不只看这一拍；
- 而看它会不会把你带到长期更有利的局面。

这正是“信用分配”问题的来源。

---

## 5. 这个项目中的核心 RL 概念

把抽象名词和当前工程一一对应起来。

### 5.1 Agent

在物理层面：

- 红方有 10 架飞机；
- 每架飞机都在做决策。

在参数层面：

- 这 10 架飞机共享一个策略网络；
- 不是 10 套彼此独立的参数。

这叫“共享策略”。

这样做的好处是：

- 参数量更小；
- 数据利用率更高；
- 单卡更容易带得动；
- 飞机之间可以共享战术结构。

### 5.2 Environment

环境就是 `MaCA` 仿真器。

在当前工程里又分成几层：

1. 原始 `MaCA` 环境；
2. 并行多智能体包装；
3. `Sample Factory` 需要的适配接口。

也就是说，你训练时用到的“环境”其实是包装后的版本，而不是原始接口直接裸连。

### 5.3 Observation

当前训练中的单飞机观测主要包括：

- `obs`：形状约为 `(5, 100, 100)` 的图像张量；
- `measurements`：长度为 `6` 的归一化向量；
- `action_mask`：长度为 `336` 的合法动作 mask；
- `is_alive`：该飞机是否存活。

这四部分分别承担不同角色：

- 图像负责局部空间结构；
- 向量负责关键摘要信息；
- mask 负责动作合法性；
- alive 负责区分死机和活机。

### 5.4 Action

动作空间总数：

\[
ACTION\_NUM = 16 \times 21 = 336
\]

其中：

- `16` 是航向选择；
- `21` 是攻击索引。

攻击索引里又包括：

- `0`：不打；
- `1..10`：长程打第 `1..10` 个目标；
- `11..20`：短程打第 `1..10` 个目标。

所以每个动作本质上是：

- 机动方向；
- 攻击决策。

而雷达扫描 / 干扰支持动作目前由工程中固定策略提供，见 `fighter_action_utils.py`。

### 5.5 Reward

当前奖励来自两层：

1. 环境单步局部奖励；
2. 整局胜负奖励。

当前关键 reward 见 `configuration/reward.py`：

| 事件 | 原始值 |
| --- | ---: |
| 击毁敌机 | `420` |
| 击毁己机 | `-300` |
| 合法开火 | `0` |
| 非法开火 | `-8` |
| 每步存活 | `-1` |
| 普通赢局 | `1200` |
| 完全胜利 | `8000` |
| 普通失败 | `-1000` |
| 平局 | `-500` |

训练时又会经过：

- `reward_scale = 0.005`
- `reward_clip = 30.0`

例如：

- 普通赢局缩放后是 `6`
- 完全胜利缩放后是 `40`，再被裁剪到 `30`
- 一次击毁敌机缩放后是 `2.1`

这套量级设计的核心思想是：

- 让“赢局”仍然是明显重要的长期信号；
- 同时保留击中 / 被击毁这种局部信号；
- 避免某个 shaping 奖励主导一切。

### 5.6 Episode

一局最长默认 `1000` 步。

结束条件包括：

- 某一方被打穿；
- 或达到 `max_step`。

在代码里，`maca_max_step` 现在默认也是 `1000`。

---

## 6. 强化学习优化的真正目标是什么

理论上，我们想求的是一套策略参数 \(\theta\)，使得长期期望回报最大：

\[
J(\theta) = \mathbb{E}_{\tau \sim \pi_\theta}\left[\sum_{t=0}^{T}\gamma^t r_t\right]
\]

注意这里有三个层次：

1. 轨迹 \(\tau\) 是由当前策略采样出来的；
2. 每条轨迹的回报不同；
3. 我们优化的是很多轨迹的平均表现。

这意味着 RL 的难点不是只在于“算梯度”，而在于：

- 你的训练数据分布会随着策略本身变化；
- 也就是说，学习对象和采样分布是耦合的。

这也是为什么 RL 比普通监督学习更难稳。

---

## 7. Value、Q、Advantage 到底是什么

这几个概念看起来像一堆缩写，但它们在逻辑上很统一。

### 7.1 状态价值函数

状态价值函数定义为：

\[
V^\pi(s) = \mathbb{E}_\pi[G_t \mid s_t=s]
\]

意思是：

- 如果我现在在状态 \(s\)；
- 后面都按策略 \(\pi\) 走；
- 平均来看还能拿到多少长期回报。

在 POMDP 里，更准确说策略输入是观测或历史，但直觉一样。

### 7.2 动作价值函数

\[
Q^\pi(s,a) = \mathbb{E}_\pi[G_t \mid s_t=s, a_t=a]
\]

意思是：

- 当前先强制选动作 \(a\)；
- 然后再按策略 \(\pi\) 往后走；
- 长期回报期望是多少。

### 7.3 Advantage

\[
A^\pi(s,a) = Q^\pi(s,a) - V^\pi(s)
\]

它衡量的不是“这个动作绝对有多好”，而是：

- 它比这个状态下的平均动作好多少。

这非常重要。

因为在策略梯度里，我们更关心：

- 哪个动作相对更值得增大概率；
- 哪个动作相对更应该减小概率。

如果某个动作的 advantage 为正，说明它比平均水平好；
如果为负，说明它比平均水平差。

---

## 8. Bellman 方程：为什么 RL 总在递推

Bellman 方程的核心思想其实很直观：

- 长期价值 = 当前奖励 + 下一步剩余价值。

对状态价值函数来说：

\[
V^\pi(s) = \mathbb{E}_{a\sim\pi, s'\sim P}\left[r(s,a) + \gamma V^\pi(s')\right]
\]

对动作价值函数来说：

\[
Q^\pi(s,a) = \mathbb{E}_{s'\sim P}\left[r(s,a) + \gamma \mathbb{E}_{a'\sim\pi}Q^\pi(s',a')\right]
\]

这件事的直观含义是：

- 你不需要每次都把整条未来完全展开到终局；
- 可以用“下一步的价值估计”来递推长期价值。

这就引出了 bootstrapping。

---

## 9. Monte Carlo、TD、Bootstrapping

### 9.1 Monte Carlo

最朴素的方法是：

- 把整局跑完；
- 用真实整局回报 \(G_t\) 当监督信号。

优点：

- 无偏；
- 直接。

缺点：

- 方差很大；
- 必须等一整局结束；
- 长时程任务学得慢。

### 9.2 Temporal Difference

TD 的思想是：

- 不等整局结束；
- 用“当前奖励 + 下一步价值估计”来更新当前价值估计。

例如最简单的 TD(0)：

\[
V(s_t) \leftarrow V(s_t) + \alpha\left(r_t + \gamma V(s_{t+1}) - V(s_t)\right)
\]

中间的误差项

\[
\delta_t = r_t + \gamma V(s_{t+1}) - V(s_t)
\]

叫做 TD error。

### 9.3 Bootstrapping

所谓 bootstrapping，就是：

- 用自己的估计去更新自己的估计。

它会引入偏差，但能大幅降低方差。

直观上：

- Monte Carlo 更“老实”，但噪声大；
- TD 更“务实”，但依赖估计质量。

强化学习里很多方法本质上都是在这两者之间找平衡。

---

## 10. DQN 在做什么

你之前项目里走过 DQN 路线，所以必须真正理解它，而不是只知道“它不适合”。

### 10.1 Q-learning 的核心

Q-learning 想学一个最优动作价值函数 \(Q^*(s,a)\)。

Bellman 最优方程写成：

\[
Q^*(s,a) = \mathbb{E}\left[r + \gamma \max_{a'}Q^*(s', a')\right]
\]

这意味着：

- 当前动作价值 = 当前奖励 + 下一状态最优动作价值。

### 10.2 DQN

DQN 用神经网络近似 \(Q(s,a)\)，更新目标近似为：

\[
y = r + \gamma \max_{a'} Q_{\text{target}}(s',a')
\]

然后最小化：

\[
\mathcal{L} = \left(Q_{\text{eval}}(s,a) - y\right)^2
\]

为稳定训练，DQN 常见工程技巧包括：

- replay buffer；
- target network；
- Double DQN；
- Dueling；
- reward clip；
- action mask。

这些你在本项目旧路线里都碰到过。

### 10.3 DQN 为什么在这个项目里吃力

不是说 DQN 完全不能学，而是当前问题结构对它很不友好。

原因有五个。

#### 原因 1：多智能体 + 对手非平稳

当对手在动，或者己方多个 agent 同时影响局面时：

- “同一个观测 + 动作”对应的长期后果更不稳定；
- Q 函数更难学稳。

#### 原因 2：部分可观测

单步观测看不见全局状态时：

- 单步 Q 值缺少关键上下文；
- 很多动作好坏要结合过去几步历史才能解释。

#### 原因 3：动作空间大而稀疏

这里每架飞机动作有 `336` 种。

在 DQN 里：

- 你要为每个动作都估一个 Q 值；
- 很多动作大部分时间非法或无意义；
- 这会让估计浪费容量，也让 argmax 更不稳定。

#### 原因 4：长时程信用分配

空战链条通常是：

- 机动；
- 探测；
- 锁定；
- 进入射程；
- 开火；
- 命中；
- 赢局。

从前面动作到最后结果，中间可能隔很多步。

#### 原因 5：课程迁移不一定成立

`fix_rule_no_att` 学到的“生存”和“得分”能力，不一定能迁移到真实对抗。

因为一旦对手会攻击，策略分布已经变了。

---

## 11. 为什么转向 Policy Gradient

### 11.1 最本质的区别

DQN 的思路是：

- 先学“每个动作值多少钱”；
- 再选值最大的动作。

Policy Gradient 的思路是：

- 直接学“什么动作概率更大”。

也就是：

- value-based：学价值，再间接出策略；
- policy-based：直接学策略。

### 11.2 REINFORCE 的直觉

如果某条轨迹最后回报很好，那就应该：

- 增大这条轨迹中那些动作出现的概率。

如果回报很差，那就应该：

- 减小这些动作的概率。

这件事可写成经典策略梯度形式：

\[
\nabla_\theta J(\theta)
=
\mathbb{E}\left[
\sum_t \nabla_\theta \log \pi_\theta(a_t \mid o_t) \, G_t
\right]
\]

它的意思是：

- 某个动作如果带来了高回报；
- 就把它的 log-prob 往上推。

### 11.3 为什么要减 baseline

如果直接用 \(G_t\)，方差通常很大。

所以常见做法是减去一个 baseline \(b_t\)：

\[
\nabla_\theta J(\theta)
=
\mathbb{E}\left[
\sum_t \nabla_\theta \log \pi_\theta(a_t \mid o_t) \, (G_t - b_t)
\right]
\]

如果 baseline 选为价值函数 \(V(o_t)\)，就得到 advantage：

\[
A_t \approx G_t - V(o_t)
\]

这样会更稳。

---

## 12. Actor-Critic：为什么同时要策略和价值网络

Actor-Critic 可以理解为：

- Actor 负责“做动作”；
- Critic 负责“评价动作好不好”。

在共享 backbone 的实现里，通常是：

- 前面共享一个编码器；
- 后面分出 policy head 和 value head。

当前工程里实际上也是这个思路，只不过由 `Sample Factory` 的 actor-critic 框架承载。

这样做的好处：

- Actor 得到 Critic 的低方差训练信号；
- Critic 通过 bootstrap 估计长期价值；
- 整体比纯 REINFORCE 更稳。

---

## 13. PPO：当前训练的核心算法

这部分必须吃透，因为你现在正式训练用的就是 PPO 家族。

### 13.1 为什么不能更新太猛

策略梯度一个天然风险是：

- 一次更新把策略改得太大；
- 采样分布和训练分布迅速错位；
- 性能会突然崩。

PPO 的核心就是：

- 允许更新；
- 但不让每次更新跨太大步。

### 13.2 概率比值

定义新旧策略比值：

\[
r_t(\theta)=\frac{\pi_\theta(a_t \mid o_t)}{\pi_{\theta_{\text{old}}}(a_t \mid o_t)}
\]

如果：

- \(r_t > 1\)，说明新策略更偏爱这个动作；
- \(r_t < 1\)，说明新策略更不偏爱这个动作。

### 13.3 PPO 的 clipped objective

PPO 的关键目标函数是：

\[
L^{CLIP}(\theta) =
\mathbb{E}\left[
\min\left(
r_t(\theta) A_t,\;
\text{clip}(r_t(\theta), 1-\epsilon, 1+\epsilon) A_t
\right)
\right]
\]

直观解释：

- 当更新还在合理范围内，就正常鼓励；
- 一旦概率改动过大，就把收益截住；
- 防止策略暴冲。

这就是 PPO 稳定性的核心来源。

### 13.4 PPO 的总损失

实际训练时通常不只这一项，还包括：

- policy loss；
- value loss；
- entropy bonus。

总目标常写成：

\[
\mathcal{L}
=
\mathcal{L}_{policy}
 c_v \mathcal{L}_{value}
 c_e \mathcal{L}_{entropy}
\]

其中：

- value loss 帮 critic 学得准；
- entropy 帮策略别太快塌成完全确定性。

---

## 14. GAE：为什么要估 Advantage

GAE 全称是 Generalized Advantage Estimation。

它的目的非常实际：

- 给 actor 一个质量不错、方差又别太大的 advantage 估计。

先定义 TD residual：

\[
\delta_t = r_t + \gamma V(o_{t+1}) - V(o_t)
\]

GAE 把很多步 TD residual 衰减累加：

\[
A_t^{GAE(\gamma,\lambda)}
=
\delta_t + \gamma \lambda \delta_{t+1}
+ (\gamma \lambda)^2 \delta_{t+2} + \cdots
\]

其中 \(\lambda\) 控制：

- 更像 TD；
- 还是更像 Monte Carlo。

直觉上：

- \(\lambda\) 小一点，方差小、偏差大；
- \(\lambda\) 大一点，偏差小、方差大。

当前默认里：

- `gamma = 0.995`
- `gae_lambda = 0.95`（由 Sample Factory 默认提供）

这是一组比较常见的长时程任务配置。

---

## 15. APPO 和 V-trace：为什么你现在不是纯 PPO

当前工程训练命令里用的是：

- `--algo=APPO`
- `--with_vtrace=True`

这意味着你实际跑的是异步 PPO 风格训练。

### 15.1 APPO 的动机

为了提高吞吐，通常会：

- 多个 actor 并行采样；
- learner 单独更新参数；
- 两边异步工作。

这样采样更快，但带来一个问题：

- actor 采样时用的是稍旧版本策略；
- learner 更新时策略已经变了。

这叫 off-policy 偏移或 policy lag。

### 15.2 V-trace 在干什么

V-trace 是一种重要性采样修正方法。

你不用背完整推导，先记住一句：

- 它在异步采样下，用来缓和“数据来自旧策略”带来的偏差。

### 15.3 `max_policy_lag`

当前默认：

- `max_policy_lag = 15`

这表示：

- 太旧的数据会被过滤掉，不参与训练。

这是最近一轮实际训练经验得出的重要调整：

- 之前设得更大时，虽然日志里平均 lag 没总打到上限；
- 但 learner 积压严重时，旧样本风险会明显变大；
- 所以现在把它收紧。

---

## 16. 为什么这个项目必须重视部分可观测

这个问题不是“可观测有点差”，而是“本质上部分可观测”。

原因包括：

- 只能看到局部战场信息；
- 目标可能刚刚消失在当前观测里；
- 导弹、锁定、接敌窗口都有明显时序性；
- 当前一步的最优动作往往依赖过去几步历史。

这意味着：

- 单帧卷积不够；
- 必须给模型某种记忆。

所以当前正式基线使用：

- `use_rnn=True`
- `rnn_type=lstm`
- `hidden_size=256`

LSTM 的作用不是“让网络更高级”，而是让它在隐状态里记住：

- 刚才看到过谁；
- 最近几步自己是怎么机动的；
- 目标是否刚进入射程；
- 当前交战窗口大概有没有形成。

---

## 17. 为什么是共享策略而不是每机一套网络

你完全可以想象给每架飞机一套独立网络，但当前工程没有这么做。

原因很现实。

### 17.1 参数量

10 套独立策略意味着：

- 显存占用更大；
- 训练样本更稀；
- 更容易出现某些 agent 学得快、某些学得慢。

### 17.2 对称性

同类战斗机在很多规则上是对称的。

共享策略意味着：

- “会打仗的规则”可以在不同飞机之间复用；
- 学到的是角色通用行为，而不是单机特化行为。

### 17.3 工程稳定性

单卡 `RTX 4060 8GB` 下，共享策略更稳妥。

所以当前路线属于：

- 参数共享；
- 执行时多 agent 并行；
- 但不是 centralized critic 那种更重的结构。

---

## 18. 为什么动作 mask 在这个项目里特别重要

### 18.1 问题根源

动作空间有 `336` 个，但很多时刻真正合法的动作只有很少一部分。

例如：

- 没有目标；
- 目标不在射程；
- 没有对应导弹；
- 飞机已死亡。

如果不做 mask，会怎样？

- 策略会把很多概率浪费在根本不可能执行的动作上；
- 训练容量被无效动作吞掉；
- log-prob、entropy 也会被这些坏动作污染。

### 18.2 当前工程怎么做

当前项目里动作 mask 有两层。

第一层，环境侧生成合法动作：

- 文件：`fighter_action_utils.py`
- 核心函数：`build_valid_action_masks`

它根据：

- 剩余长程导弹数量；
- 剩余短程导弹数量；
- 当前目标距离；
- 当前目标 id；

生成一个长度为 `336` 的二值 mask。

第二层，策略侧真正使用这个 mask：

- 文件：`scripts/train_sf_maca.py`
- 方法：在 `Sample Factory` 的 actor-critic forward 里，把非法动作 logits 设成极小值 `-1e9`

也就是：

\[
\text{logits}_{masked} =
\begin{cases}
\text{logits}, & \text{合法}\\
-10^9, & \text{非法}
\end{cases}
\]

这样 softmax 之后，非法动作概率几乎为零。

### 18.3 为什么还保留环境侧 fallback

尽管策略层已经 mask 了，环境侧仍然保留一个安全修正：

- 如果收到非法动作，不让环境崩；
- 优先退化成同航向 no-op 攻击；
- 再不行就选一个合法动作。

这是工程上的双保险。

---

## 19. 奖励设计：为什么这是最容易学偏的地方

强化学习里最常见的问题不是“模型太弱”，而是“目标信号给歪了”。

### 19.1 奖励不是事实，而是训练接口

奖励不是世界真理。

它只是你告诉 agent：

- 什么值得追求；
- 什么值得避免。

如果这个接口设计得不好，模型会去钻空子。

这叫 reward hacking。

### 19.2 当前这套奖励为什么比之前更合理

我们已经做过一轮重要修正：

- `reward_strike_act_valid = 100` 改成了 `0`
- `reward_draw = -1500` 改成了 `-500`

为什么？

因为之前：

- 合法开火本身就拿很大正奖励；
- 可能鼓励“只要能打就乱打”；
- 反而削弱了赢局这个真正目标。

现在更合理的逻辑是：

- 是否开火由“命中 / 打空 / 输赢后果”来决定；
- 不额外奖励“只是执行了一个合法开火动作”。

### 19.3 reward scale 和 clip 的耦合

当前默认：

- `reward_scale = 0.005`
- `reward_clip = 30.0`

这组参数必须一起看。

如果 scale 太大，而 clip 太小，会发生什么？

- `win` 和 `totally_win` 都可能被裁到同一个上限；
- critic 看不出两者差异；
- 终局目标层级变差。

所以现在这组值是刻意配合过的。

---

## 20. 当前项目为什么不再以 DQN 为主线

一句话总结：

- 不是 DQN 完全错；
- 而是这类问题对 policy-gradient 路线更自然。

更完整的说法是：

这个项目同时具有：

- 多智能体；
- 部分可观测；
- 大离散动作空间；
- 长时程信用分配；
- 非平稳对手；
- 明显动作合法性约束。

这些特点叠加在一起后，value-based 路线的训练稳定性压力会非常大。

因此当前主线切换到：

- `Sample Factory`
- `APPO / PPO`
- `LSTM`
- 共享策略
- policy-level action masking

---

## 21. 这套工程里的代码结构应该怎么理解

下面按“数据流”而不是“目录树”来理解。

### 21.1 原始环境层

`MaCA` 原始环境本体仍然负责：

- 推演战场；
- 接收红蓝动作；
- 返回原始观测和 reward。

### 21.2 并行多智能体包装层

文件：`marl_env/maca_parallel_env.py`

它做的事情：

- 只暴露红方战斗机作为学习 agent；
- 把观测整理成每个 agent 一个 dict；
- 为每个 agent 构造 reward、termination、truncation、info；
- 生成 action mask；
- 对死掉的飞机保留固定槽位，而不是直接删掉。

这里的设计非常重要，因为很多 RL 框架都希望：

- 本局开始时 agent 数固定；
- 中途不要乱变。

### 21.3 Sample Factory 适配层

文件：`marl_env/sample_factory_env.py`

它把上一层包装成 `Sample Factory 1.x` 需要的 API。

这里主要做了：

- 把 `screen` 调整成 `CHW`；
- 把 `info` 归一化成 `measurements`；
- 暴露 `action_mask`；
- 暴露 `is_alive`；
- 统计 `invalid_action_frac`、`true_reward`、`win_flag` 等日志指标。

### 21.4 自定义编码器

文件：`marl_env/sample_factory_model.py`

当前编码器是：

- CNN 编码 `obs`
- MLP 编码 `measurements + is_alive`
- 两者拼接后进入后续 actor-critic

这是一个典型的“多模态轻量编码器”设计。

### 21.5 环境注册和默认参数

文件：`marl_env/sample_factory_registration.py`

这里定义了当前正式基线默认值，例如：

- `hidden_size = 256`
- `rollout = 32`
- `recurrence = 32`
- `batch_size = 512`
- `num_workers = 4`
- `learning_rate = 2e-5`
- `reward_scale = 0.005`
- `reward_clip = 30.0`
- `ppo_epochs = 4`
- `max_policy_lag = 15`
- `exploration_loss_coeff = 0.01`

### 21.6 训练入口

文件：`scripts/train_sf_maca.py`

这里做了三类工作：

1. 调 `Sample Factory` 官方训练入口；
2. 加兼容性补丁；
3. 加本项目需要的策略级动作 mask 补丁。

兼容性补丁包括：

- checkpoint 临时文件名保存兼容；
- 单轨迹 batch 的 squeeze 问题修复；
- action mask 注入。

### 21.7 启动脚本

文件：

- `scripts/run_sf_maca_gpu_smoke.sh`
- `scripts/run_sf_maca_4060_baseline.sh`

前者用来证明：

- 环境能起；
- 模型能前向；
- learner 能更新；
- checkpoint 能保存。

后者才是正式长训基线。

### 21.8 评估脚本

文件：`scripts/eval_sf_maca.py`

它负责：

- 加载已有 experiment；
- 加载最新 checkpoint；
- 跑固定局数评估；
- 输出 `win_rate`、`round_reward_mean`、`true_reward_mean`、`invalid_action_frac_mean`。

这比只盯训练 reward 曲线靠谱得多。

---

## 22. 一条完整训练数据流到底怎么走

把整套流程串起来。

### 第 1 步：actor 采样

环境当前给出：

- `obs`
- `measurements`
- `action_mask`
- `is_alive`

### 第 2 步：策略前向

编码器把观测变成特征。

然后 actor-critic 输出：

- value 估计；
- action logits。

接着把 `action_mask` 作用到 logits 上。

### 第 3 步：动作采样并执行

策略从 masked distribution 中采样动作。

环境再做一次安全兜底修正，最后推进仿真。

### 第 4 步：收集轨迹

actor worker 不断把：

- 观测；
- 动作；
- log-prob；
- value；
- reward；
- done；

等信息写入轨迹 buffer。

### 第 5 步：learner 更新

learner 收到一批 rollout 后：

- 计算 advantage；
- 计算 value target；
- 做 PPO / APPO 更新；
- 广播新参数给 policy worker。

### 第 6 步：周期性保存和评估

训练中会定期：

- 保存 checkpoint；
- 记录 summary；
- 后续可以用评估脚本做 fixed-opponent evaluation。

---

## 23. 当前正式基线超参数应该怎么理解

下面不是“神秘魔法数字”，而是你应该能用语言解释的东西。

### 23.1 `num_workers = 4`

为什么不是越大越好？

因为更多 worker 意味着：

- 更高采样吞吐；
- 但也可能让 learner 来不及吃数据。

最近一轮实验已经出现 learner 积压严重，所以现在从 `6` 下调到 `4`。

### 23.2 `rollout = 32`

rollout 太短的问题是：

- 时序上下文太碎；
- 长时程信用分配更弱。

rollout 太长的问题是：

- buffer 更大；
- learner 压力更高；
- 单次更新更慢。

`32` 是当前在单卡上的折中。

### 23.3 `recurrence = 32`

既然用了 `LSTM`，就必须关心 BPTT 长度。

这里设成和 rollout 一样，意味着：

- 反向传播能穿过整个 rollout。

### 23.4 `batch_size = 512`

批量太小：

- 梯度噪声大；
- 更新不稳。

批量太大：

- 显存和吞吐压力上去；
- learner 更容易成为瓶颈。

### 23.5 `ppo_epochs = 4`

PPO 不是一批样本只用一次。

如果 epoch 太少：

- 样本利用率低。

如果太多：

- 容易对旧样本过拟合；
- 也会增加 policy lag 风险。

当前 `4` 是比较经典的起点。

### 23.6 `learning_rate = 2e-5`

最近一轮从 `5e-5` 降到 `2e-5`，是因为：

- 已经学到一些有价值的策略；
- 此时更怕大步更新把好区域冲掉。

### 23.7 `gamma = 0.995`

这体现出任务是长时程决策。

如果 \(\gamma\) 太小，就会更短视。

### 23.8 `exploration_loss_coeff = 0.01`

这是熵正则项权重。

太小会怎样？

- 策略太快变得接近确定性；
- 早早停止探索。

### 23.9 `max_policy_lag = 15`

这是异步训练里非常关键的稳定性参数。

它的目标不是“越小越好”，而是：

- 尽量少吃太旧的数据；
- 但又不要把样本扔得太多。

### 23.10 `reward_scale = 0.005` 和 `reward_clip = 30`

这两者必须联动理解，前面已经解释过。

---

## 24. 当前模型结构应该怎么理解

### 24.1 CNN 部分

`sample_factory_model.py` 里当前图像编码是三层卷积：

- `5 -> 16`
- `16 -> 32`
- `32 -> 48`

每层都做 stride 下采样。

直觉上：

- 前层提局部纹理；
- 中层提更高层局部结构；
- 后层压缩成更适合决策的特征图。

### 24.2 Measurement MLP

长度为 `6` 的向量不能直接丢掉，因为它包含了高度决策相关的信息，例如：

- 导弹剩余；
- 目标距离；
- 目标 id；

所以单独用两层 MLP 编码，再和图像特征拼接。

### 24.3 为什么没有做得更大

不是因为更大一定没用，而是因为：

- 当前目标先是建立稳定 baseline；
- 算力是 `4060 8GB`；
- 工程上先要稳定可迭代。

---

## 25. 训练日志应该怎么看

这是最容易从“看热闹”变成“看门道”的地方。

### 25.1 第一层：系统有没有正常起

先看：

- env 是否初始化成功；
- learner 是否初始化成功；
- policy worker 是否初始化成功；
- checkpoint 是否能保存。

如果这里都没过，别讨论算法效果。

### 25.2 第二层：是不是在用 GPU

不要被单独一行 `Queried available GPUs: 0` 吓到。

真正要看的是 learner / policy worker 里有没有：

- `Set environment var CUDA_VISIBLE_DEVICES to '0'`
- `Visible devices: 1`
- `GPU learner timing: ...`

这几行才说明实际训练进程看到了 GPU。

### 25.3 第三层：learner 是不是瓶颈

如果日志反复出现：

- `Learner ... accumulated too much experience`

说明：

- actor 采样太快；
- learner 来不及更新；
- policy lag 风险会上升。

这时应该优先考虑：

- 降 `num_workers`；
- 降学习复杂度；
- 或重新平衡批量与网络大小。

### 25.4 第四层：任务表现是不是在变好

常见可看指标：

- `Avg episode reward`
- evaluation 的 `win_rate`
- `round_reward_mean`
- `true_reward_mean`
- `invalid_action_frac_mean`

不要只看单点峰值，要看：

- 滑动平均；
- 最佳窗口；
- 最后阶段；
- checkpoint 对应的表现。

---

## 26. 为什么训练 reward 不等于真实战斗能力

这点一定要反复提醒自己。

原因有三类。

### 26.1 奖励不是胜率

训练 reward 是很多局部项的合成。

它可能上升，但：

- 只是更会存活；
- 或更会刷局部奖励；
- 但不一定更会赢。

### 26.2 训练对手固定，会有过拟合

如果一直只打 `fix_rule`：

- 策略可能学到的是“针对这个规则对手的特化行为”；
- 不一定具有更强泛化。

### 26.3 PPO 曲线本来就有波动

RL 不是监督学习那种平滑下降曲线。

你会经常看到：

- 上涨；
- 回撤；
- 再恢复；
- 再波动。

关键不是“有没有波动”，而是：

- 长期趋势；
- 最佳窗口；
- 评估是否实质变好。

---

## 27. Resume、Fresh Start、Done 文件、Env Step 上限

这部分是最近工程里非常实际、也非常容易踩坑的知识。

### 27.1 什么时候是 resume

`Sample Factory` 用 experiment 名字识别实验目录。

也就是说：

- `EXP_NAME` 相同，才会加载原 experiment；
- 名字不同，就一定新开目录从头训。

### 27.2 什么时候是 fresh start

下面这些情况适合 fresh start：

- 改了模型结构；
- 改了观测结构；
- 改了动作定义；
- 想做严格对照实验。

### 27.3 `done` 文件的作用

当实验达到训练目标后，目录里会留下 `done` 文件。

如果不删它，再次启动同名 experiment 时会直接退出，并提示：

- `Training already finished! Remove "done" file to continue training`

### 27.4 `train_for_env_steps` 的坑

恢复训练时，`Sample Factory` 会加载旧 checkpoint 中记录的 `env_steps`。

如果旧 checkpoint 已经是：

- `50000899`

但你新的命令还是：

- `--train_for_env_steps=50000000`

那它一恢复就已经达到上限，自然会马上结束。

所以续训时一定要保证：

\[
\text{新的 train\_for\_env\_steps} > \text{当前 checkpoint 的 env\_steps}
\]

这是最近一次真实踩坑总结出来的工程经验。

---

## 28. 为什么必须做独立评估

当前工程已经有：

- 训练脚本：`scripts/train_sf_maca.py`
- 评估脚本：`scripts/eval_sf_maca.py`

评估的重要性在于：

- 训练 reward 曲线只是训练时的在线统计；
- checkpoint 谁更好，必须用固定条件重新测。

建议每次长训后都做：

```bash
python scripts/eval_sf_maca.py \
  --experiment=<experiment_name> \
  --train_dir=train_dir/sample_factory \
  --device=cpu \
  --episodes=50 \
  --maca_opponent=fix_rule \
  --maca_max_step=1000
```

重点看：

- `win_rate`
- `round_reward_mean`
- `true_reward_mean`
- `invalid_action_frac_mean`

其中：

- `win_rate` 最接近最终目标；
- `invalid_action_frac_mean` 能帮助判断 mask 是否真的在约束策略；
- `true_reward_mean` 比局部平均更接近整局效果。

---

## 29. 当前技术路线的真正逻辑

把整个项目压缩成一条主线。

### 第 1 步：先把环境整理成现代 RL 框架能吃的形式

也就是：

- 固定 agent 集；
- dict obs；
- per-agent reward；
- action mask；
- inactive agent handling。

### 第 2 步：先证明系统工程链路通

也就是 smoke：

- 能初始化；
- 能前向；
- 能更新；
- 能保存 checkpoint。

### 第 3 步：建立一个可持续跑的 baseline

这就是当前：

- `Sample Factory`
- `APPO`
- `LSTM`
- 共享策略
- `fix_rule`

### 第 4 步：建立评估闭环

也就是：

- 不是只盯 reward；
- 而是固定 checkpoint、固定对手、固定局数来比较。

### 第 5 步：再谈更复杂增强

例如：

- opponent pool；
- self-play；
- 更强 critic；
- centralized training；
- curriculum；
- reward 微调。

如果 baseline 都不稳，这些高级技巧通常只会把问题复杂化。

---

## 30. 一些常见误解

### 误解 1：能跑起来就等于模型方向对了

不对。

系统工程打通，只代表：

- 没有 shape 错；
- 没有 multiprocessing 错；
- 没有 CUDA 错；
- 不代表策略真的在学对东西。

### 误解 2：reward 上升就一定更会赢

不对。

它可能只是更会：

- 存活；
- 拖时间；
- 利用 shaping。

### 误解 3：参数越大越强

不对。

更大的网络和更大的 batch 往往也意味着：

- 更慢；
- 更难稳定；
- 更容易让 learner 成为瓶颈。

### 误解 4：动作 mask 做了环境兜底就够了

不对。

环境兜底只能防止崩，
不能直接让策略学到“哪些动作根本不该考虑”。

所以当前项目已经把 mask 接到了 policy logits。

### 误解 5：resume 就只是继续跑命令

不对。

续训至少要同时检查：

- `EXP_NAME` 是否一致；
- `done` 文件是否删除；
- `train_for_env_steps` 是否大于当前 checkpoint 的 env step。

---

## 31. 建议你的学习顺序

如果你准备认真学，不要乱跳。

### 第一遍：建立全局图景

只看这些章节：

- 第 1 章到第 7 章；
- 第 16 章到第 18 章；
- 第 21 章到第 23 章；
- 第 29 章。

目标是回答：

- RL 在这个项目里到底是什么；
- 当前系统到底怎么流动。

### 第二遍：啃核心数学

重点看：

- 第 8 章到第 15 章。

目标是回答：

- value、advantage、GAE、PPO、V-trace 分别是什么；
- 为什么要这样设计。

### 第三遍：对照代码

边看边打开这些文件：

- `marl_env/maca_parallel_env.py`
- `marl_env/sample_factory_env.py`
- `marl_env/sample_factory_model.py`
- `marl_env/sample_factory_registration.py`
- `scripts/train_sf_maca.py`
- `scripts/eval_sf_maca.py`
- `fighter_action_utils.py`
- `configuration/reward.py`

### 第四遍：训练和评估实操

去跑：

- smoke；
- baseline；
- evaluation；
- resume。

然后再回来看第 25、27、28 章，你会理解得更深。

---

## 32. 一份最小可执行的认知清单

如果你现在只想抓住最关键的东西，先记住下面这些。

1. 这个项目本质上是一个多智能体、部分可观测、长时程、大离散动作空间的决策问题。
2. 共享策略 + `LSTM` 是当前算力条件下最现实的第一版结构。
3. 当前主算法不是 DQN，而是 `APPO/PPO`。
4. `advantage` 是“动作比平均水平好多少”。
5. PPO 的核心是“更新，但不要一次改太猛”。
6. `action_mask` 在这个项目里不是可选优化，而是核心必要条件。
7. reward 设计决定了“模型到底在学什么”。
8. 日志里 learner bottleneck 和 policy lag 比单个 reward 峰值更值得警惕。
9. checkpoint 保留策略和固定评估循环是必须的，不是锦上添花。
10. 续训能不能接上，不只看 experiment 名，还要看 `done` 和 `train_for_env_steps`。

---

## 33. 一句话总结整条路线

当前这套工程不是“随便拿 PPO 套上去”，而是：

- 先把 `MaCA` 变成一个标准化、可并行、可 mask、可记录统计的多智能体环境；
- 再用更适合长时程部分可观测任务的 `APPO + LSTM + 共享策略` 去训练；
- 同时用 reward 设计、action masking、checkpoint 管理、固定评估和日志诊断，把它做成一个可持续迭代的 RL 工程。

如果你真正读懂这份文档，再去看代码和日志，你会发现：

- 那些看起来零散的 patch；
- 那些看起来琐碎的参数；
- 那些看起来麻烦的工程步骤；

其实都在服务同一件事：

- 让一个复杂的动态对抗决策问题，变成一个可以稳定学习、可以解释失败、可以逐步改进的系统。
