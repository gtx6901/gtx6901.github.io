import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# ======== 1. 填入你在终端查到的字体绝对路径 ========
# 这里以 Ubuntu 常见的文泉驿微米黑或思源黑体为例，请替换成你实际的路径
font_path = '/usr/share/fonts/ttf/PingFangSC-Thin.ttf'  

# ======== 2. 强制 Matplotlib 加载该字体 ========
fm.fontManager.addfont(font_path)
font_prop = fm.FontProperties(fname=font_path)

# ======== 3. 设置为全局默认字体 ========
plt.rcParams['font.sans-serif'] = [font_prop.get_name()] 
plt.rcParams['axes.unicode_minus'] = False  # 正常显示负号
plt.rcParams['figure.dpi'] = 150            # 提高渲染清晰度

# ==========================================
# 图1：标准电机特性曲线 (替换 1.2 节)
# ==========================================
def plot_motor_characteristics():
    T = np.linspace(0, 10, 100)
    N = 10 - T  # 转速线性下降
    P = T * N   # 功率抛物线
    
    fig, ax1 = plt.subplots(figsize=(8, 5))
    ax2 = ax1.twinx()
    
    ax1.plot(T, N, 'b-', linewidth=2, label='转速 N (rpm)')
    ax2.plot(T, P, 'r-', linewidth=2, label='功率 P (W)')
    
    # 标注关键点
    ax1.scatter([0], [10], color='blue', s=50, zorder=5)
    ax1.annotate('空载点 (最高转速)', xy=(0, 10), xytext=(0.5, 9.5), arrowprops=dict(arrowstyle="->"))
    ax1.scatter([10], [0], color='blue', s=50, zorder=5)
    ax1.annotate('堵转点 (最大扭矩)', xy=(10, 0), xytext=(8, 1), arrowprops=dict(arrowstyle="->"))
    ax2.scatter([5], [25], color='red', s=50, zorder=5)
    ax2.annotate('最大功率点', xy=(5, 25), xytext=(5.5, 24), arrowprops=dict(arrowstyle="->"))
    
    ax1.set_xlabel('扭矩 T (N·m)', fontsize=12)
    ax1.set_ylabel('转速 N (rpm)', color='b', fontsize=12)
    ax2.set_ylabel('功率 P (W)', color='r', fontsize=12)
    plt.title('直流无刷电机标准特性曲线', fontsize=14)
    ax1.grid(True, linestyle='--', alpha=0.6)
    fig.legend(loc="upper center", bbox_to_anchor=(0.5, 0.85), ncol=2)
    plt.show()

# ==========================================
# 图2：GM6020 包络线限制图 (替换 2.4 节)
# ==========================================
def plot_gm6020_envelope():
    speed = np.linspace(0, 320, 320)
    # 恒扭矩区 (0~132rpm)，最大扭矩1.2
    # 恒功率区 (132~320rpm)，功率132*1.2约158近似衰减
    torque = np.where(speed <= 132, 1.2, 1.2 * 132 / speed)
    
    plt.figure(figsize=(8, 5))
    plt.fill_between(speed, torque, color='skyblue', alpha=0.3)
    plt.plot(speed, torque, 'b-', linewidth=2)
    
    plt.axvline(x=132, color='r', linestyle='--', alpha=0.7)
    plt.axvline(x=213, color='g', linestyle='-.', linewidth=2)
    
    plt.text(60, 0.6, '恒扭矩区\n(受限于电流)', ha='center', fontsize=12)
    plt.text(220, 0.6, '恒功率区\n(受限于电压)', ha='center', fontsize=12)
    plt.annotate('你的工况: 213rpm\n(扭矩已被削减)', xy=(213, 0.74), xytext=(230, 0.9),
                 arrowprops=dict(facecolor='black', shrink=0.05), fontsize=11, color='green')
    
    plt.xlabel('转速 N (rpm)', fontsize=12)
    plt.ylabel('最大允许扭矩 T (N·m)', fontsize=12)
    plt.title('BLDC 软硬件双重限制包络线', fontsize=14)
    plt.xlim(0, 350)
    plt.ylim(0, 1.5)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.show()

# ==========================================
# 图3：理想与退化阶跃响应对比 (替换 4.2 & 4.3 节)
# ==========================================
def plot_step_response():
    t = np.linspace(0, 0.1, 500)
    target = 10  # 目标电流10A
    
    # 0 rpm: 指数收敛 (充沛电压)
    tau_fast = 0.005
    i_fast = target * (1 - np.exp(-t / tau_fast))
    
    # 213 rpm: 饱和恒定斜率爬升 (电压受限8V)
    # 假设 L=1mH, di/dt = 8/0.001 = 8000 A/s
    slope = 8000
    i_slow = slope * t
    i_slow = np.clip(i_slow, 0, target)  # 达到目标后限幅
    
    plt.figure(figsize=(8, 5))
    plt.plot(t, np.full_like(t, target), 'k--', label='目标电流 (Target)')
    plt.plot(t, i_fast, 'g-', linewidth=2.5, label='0 rpm 响应 (未饱和，指数收敛)')
    plt.plot(t, i_slow, 'r-', linewidth=2.5, label='213 rpm 响应 (电压饱和，斜率受限)')
    
    plt.xlabel('时间 t (s)', fontsize=12)
    plt.ylabel('电流 I (A)', fontsize=12)
    plt.title('不同初始转速下的电流阶跃响应对比', fontsize=14)
    plt.legend(fontsize=11)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.show()

# ==========================================
# 图4：相平面轨迹 (替换 6.1 & 6.2 节)
# ==========================================
def plot_phase_plane():
    i = np.linspace(0, 10, 100)
    # 线性系统轨迹: 假设一阶系统 di/dt = -a(i - target)
    di_dt_linear = 5 * (10 - i)
    # 饱和系统轨迹: di/dt 恒定上限
    di_dt_sat = np.full_like(i, 20)
    # 实际轨迹为两者取小
    di_dt_actual = np.minimum(di_dt_linear, di_dt_sat)
    
    plt.figure(figsize=(8, 5))
    plt.plot(i, di_dt_linear, 'g--', linewidth=2, label='理想线性系统轨迹')
    plt.plot(i, di_dt_sat, 'r-', linewidth=2, label='硬件执行器限幅边界 (di/dt上限)')
    plt.plot(i, di_dt_actual, 'b-', linewidth=3, label='实际系统截断轨迹')
    
    plt.scatter([0], [20], color='blue', s=50, zorder=5)
    plt.annotate('初始点被饱和边界截断', xy=(0, 20), xytext=(1, 30), arrowprops=dict(arrowstyle="->"))
    
    plt.scatter([10], [0], color='black', s=50, zorder=5)
    plt.text(9.5, 3, '平衡点', fontsize=12)
    
    plt.xlabel('状态变量 1: 电流 i', fontsize=12)
    plt.ylabel('状态变量 2: 电流变化率 di/dt', fontsize=12)
    plt.title('带执行器限幅的相平面分析', fontsize=14)
    plt.legend(fontsize=11)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.ylim(0, 55)
    plt.show()

# 依次执行绘图
plot_motor_characteristics()
plot_gm6020_envelope()
plot_step_response()
plot_phase_plane()