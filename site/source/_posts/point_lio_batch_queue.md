---
title: Point-LIO Batch测量队列问题记录
date: 2026-05-10
categories:
  - 笔记
tags:
  - 状态估计
  - Point-LIO
  - Robomaster
  - DEBUG
math: true
cover: cover.png
permalink: /notes/point_lio_batch_queue/
---

# Point-LIO Batch测量队列问题复盘

这篇短文记录一次 small_point_lio 的 Batch 更新问题排查。

## 1、原版 Point-LIO 的处理方式

原版 Point-LIO 并不是 IMU callback 一来就直接推进滤波器，然后等 LiDAR 点云包来了再处理。它的 callback 主要负责把 LiDAR 和 IMU 数据放入 buffer；真正的滤波处理发生在 `sync_packages(Measures)` 成功之后。

它大致做的是：

```text
等待一个 LiDAR scan 和覆盖该 scan 时间范围的 IMU 数据
-> 在这个 measurement package 内部按时间顺序处理
-> 用点云包起始时间 + 点内相对时间还原每个点的采样时刻
-> 状态预测到该点时间
-> 做点到面残差更新
```

也就是说，LiDAR topic 的发布频率虽然可能只有 50Hz 或 100Hz，但包内每个点仍然有自己的时间戳。Point-LIO 的“逐点更新”是在收到整包之后，沿着传感器时间线快速回放这一包内部的测量。

这带来两个结论：

- 原版 Point-LIO 的估计时间分辨率可以高于 LiDAR topic 频率。
- 但 LiDAR 修正后的位姿实际到达下游的延迟仍然受 LiDAR package 到达频率限制。

所以 Point-LIO 的高带宽并不等于控制器一定能低延迟收到均匀高频的 LiDAR-corrected odom。驱动打包和 ROS2 调度仍然是现实瓶颈。

## 2、small_point_lio 的现有实现差异

我手上的 small_point_lio 更偏 callback-driven：

```cpp
// LiDAR callback
small_point_lio->on_point_cloud_callback(pointcloud);
small_point_lio->handle_once();

// IMU callback
small_point_lio->on_imu_callback(imu_msg);
small_point_lio->handle_once();
```

这意味着 IMU callback 可能先推进 `time_current`。等低频 LiDAR package 到来时，包内早期点可能已经落后于当前滤波器时间。代码里对这种迟到点的处理是直接丢掉：

```cpp
if (point_lidar_frame.timestamp < time_current) {
    preprocess.point_deque.pop_front();
    continue;
}
```

这不是本文修复的重点，但它解释了为什么 LiDAR 驱动发布频率、package 延迟、ROS2 callback 调度会明显影响系统表现。把 LiDAR driver 调到更高发布频率，例如 200Hz，可以缩短单包时间跨度，从工程上缓解这个问题，但不是根治。

## 3、之前 Batch 版本的问题

Batch-LIWO 的核心视角可以这样理解：

```text
把一个短时间窗内的多个 LiDAR 点看成 batch_end_time 的一个复合测量。
```

原来单点更新是：

```text
predict 到 point 时间
构造 1 个点到面残差
做一次 measurement update
```

Batch 更新变成：

```text
predict 到 batch 末端时间
把 batch 内点去畸变到 batch 末端
构造 N 个点到面残差
做一次 measurement update
```

从 Kalman Filter 的角度看，流程仍然是 `predict -> update`。变化的是测量模型：

$$
z \in \mathbb{R}^1,\ H \in \mathbb{R}^{1 \times n}
$$

变成：

$$
z \in \mathbb{R}^N,\ H \in \mathbb{R}^{N \times n}
$$

因此 Batch 更新提高吞吐量的原因不是少做了协方差预测。原版 Point-LIO 的 LiDAR 点之间本来也主要只做状态预测，不在每个点之间传播过程协方差。Batch 真正减少的是 LiDAR measurement update 的高频重复开销，例如 Kalman 增益求解、状态注入、协方差修正和地图插入。

之前的实现只按点数切 Batch：

```cpp
batch_point_count >= batch_point_size
|| batch_point_count >= batch_max_points
|| preprocess.point_deque.empty()
```

正常情况下这没有明显问题。比如降采样后 70k pts/s，`batch_point_size = 100`，一个 Batch 大约是：

```text
100 / 70000 = 1.43ms
```

这是一个合理的小时间窗。

真正的问题发生在边缘场景。

## 4、容易出问题的场景

假设 LiDAR topic 是 50Hz，即一个 package 约 20ms。正常点率下，一个 package 内有足够多的有效点，所以 100 点 Batch 仍然只覆盖约 1.43ms。

但是如果激光雷达视野被严重遮挡，例如近距离用手挡住窗口，大量点会被距离过滤：

```cpp
if (dist < parameters->min_distance_squared || dist > parameters->max_distance_squared) {
    continue;
}
```

这时一个 20ms package 内可能只剩很少有效点，例如 20 个。它们的时间戳可能分布在整个 package 内：

```text
T + 0.5ms, T + 2.0ms, ..., T + 19.2ms
```

旧实现因为凑不满 100 点，最后会被 `preprocess.point_deque.empty()` 触发提交：

```text
20 个点，被当成一个 Batch
Batch 时间跨度接近 20ms
```

这会破坏 Batch-LIWO 的关键假设。`h_point_batch()` 会取 batch 最后一个点的时间作为参考：

```cpp
double last_time = batch_points_timestamps.back();
```

然后用 batch 末端的一组速度和角速度把所有点补偿到末端：

```cpp
velocity_imu = ...;
angular_velocity_imu = ...;
```

如果最早的点距离末端接近 20ms，甚至更多，那么恒速、恒角速度近似会明显变差。此时系统得到的是一个“点数很少、几何约束弱、时间跨度却很长”的复合测量。它比正常 Point-LIO 逐点处理更容易退化。

所以问题不是 Batch 理论本身，而是实现没有保证：

```text
一个 Batch 必须是短时间窗内的复合测量。
```

## 5、这次的解决方案

这次修复采用“时间 + 点数”双约束。

新增参数：

```yaml
batch_max_duration: 0.002
```

含义是一个 Batch 最大只能覆盖 2ms。收集新点时，如果当前点会让已有 Batch 超过时间窗口，就先提交旧 Batch，再用当前点开启新 Batch：

```cpp
if (!batch_points_buffer.empty() && parameters.batch_max_duration > 0.0 &&
    point_lidar_frame.timestamp - batch_points_buffer.front().timestamp >= parameters.batch_max_duration) {
    flush_batch_points();
}
```

原来的点数触发仍然保留：

```cpp
batch_point_count >= parameters.batch_point_size
|| batch_point_count >= parameters.batch_max_points
|| preprocess.point_deque.empty()
```

这样正常点率下仍然主要按 100 点切 Batch；遮挡低点率时则退化成短时间窗小 Batch。小 Batch 仍走 Batch update，因为 $N=1$ 时它本来就是单点复合测量，语义上接近 Point-LIO。

## 6、修复后的效果预期

在正常场景：

```text
70k pts/s, batch_point_size = 100
=> 约 1.43ms 一个 Batch
```

系统仍然走高吞吐 Batch 更新。

在遮挡或低有效点率场景：

```text
LiDAR package 20ms
有效点只剩 20 个
batch_max_duration = 2ms
```

旧实现可能形成一个 20ms Batch；新实现会切成多个小 Batch，每个 Batch 时间跨度不超过 2ms。这样不会把长时间跨度内的稀疏点硬合成一个复合观测。

这不是完整修复所有同步问题。callback-driven 架构、迟到 LiDAR 点丢弃、LiDAR driver 打包延迟依然存在。但这次修复针对的是 Batch 模式的主要矛盾：

> Batch 更新必须保持短时间窗复合测量的语义；当有效点率下降时，应退化为小 Batch，而不是变成长时间窗 Batch。

这个修复使 Batch 模式在边缘遮挡场景下更接近 Point-LIO 的原理，也避免了因为实现细节导致的额外退化。
