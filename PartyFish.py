import time
import os
import webbrowser
import warnings
import cv2
import numpy as np
from PIL import Image
import threading  # 用于在独立线程中运行脚本
import ctypes
from pynput import keyboard, mouse  # 用于监听键盘和鼠标事件，支持热键和鼠标侧键操作

# 初始化键盘和鼠标控制器
keyboard_controller = keyboard.Controller()
mouse_controller = mouse.Controller()
import datetime
import re
import queue  # 用于线程安全通信
import random  # 添加随机模块用于时间抖动
import getpass  # 用于获取电脑账号

# 尝试导入硬件信息相关库
try:
    import wmi
    WMI_AVAILABLE = True
except ImportError:
    WMI_AVAILABLE = False
    print("⚠️  [警告] 无法导入wmi，硬件信息获取可能受限")

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("⚠️  [警告] 无法导入psutil，硬件信息获取可能受限")

try:
    import winsound

    WINSOUND_AVAILABLE = True
except ImportError:
    WINSOUND_AVAILABLE = False
    print("⚠️  [警告] 无法导入winsound，部分音效可能不可用")

# 过滤libpng的iCCP警告（图片ICC配置文件问题）
warnings.filterwarnings("ignore", message=".*iCCP.*")
# 设置OpenCV不显示libpng警告
os.environ["OPENCV_IO_ENABLE_JASPER"] = "0"

import tkinter as tk  # 保留用于兼容性
from tkinter import ttk  # 保留用于兼容性
from tkinter import messagebox
import ttkbootstrap as ttkb
from ttkbootstrap.constants import *
import json  # 用于保存和加载参数
import mss


# =========================
# 卡密验证相关
# =========================
# 硬编码卡密
VALID_CARD_KEY = "免费软件倒卖全家死光光"

# 卡密信息保存键名
CARD_KEY_SAVE_KEY = "card_key"
HARDWARE_INFO_SAVE_KEY = "hardware_info"


def verify_card_key():
    """
    验证卡密，绑定硬件信息
    每次启动时调用，硬件信息不一致则需要重新输入卡密
    """
    # 先加载参数，获取保存的卡密和硬件信息
    load_parameters()
    
    # 获取当前硬件信息
    current_hardware = get_hardware_info()
    
    # 读取保存的卡密和硬件信息
    saved_card_key = None
    saved_hardware = None
    
    try:
        with open(PARAMETER_FILE, "r", encoding="utf-8") as f:
            params = json.load(f)
            saved_card_key = params.get(CARD_KEY_SAVE_KEY, None)
            saved_hardware = params.get(HARDWARE_INFO_SAVE_KEY, None)
    except Exception as e:
        print(f"⚠️  [警告] 读取卡密信息失败: {e}")
    
    # 检查是否需要重新输入卡密
    need_reinput = False
    if not saved_card_key:
        need_reinput = True
        print("🔑 [卡密] 首次启动，需要输入卡密")
    elif saved_hardware != current_hardware:
        need_reinput = True
        print("🔄 [卡密] 硬件信息已变更，需要重新输入卡密")
    
    # 需要重新输入卡密
    if need_reinput:
        # 导入必要的模块
        import tkinter as tk
        from tkinter import messagebox
        
        # 创建卡密输入窗口
        def create_card_key_window():
            """创建卡密输入窗口"""
            # 创建临时根窗口
            temp_root = tk.Tk()
            temp_root.withdraw()  # 隐藏主窗口
            
            # 创建卡密输入对话框
            card_key = tk.StringVar()
            result = [False]  # 使用列表存储结果，以便在内部函数中修改
            
            def on_submit():
                """提交卡密"""
                input_card_key = card_key_entry.get().strip()
                if input_card_key == VALID_CARD_KEY:
                    result[0] = True
                    temp_root.quit()  # 退出对话框
                else:
                    messagebox.showerror("错误", "卡密错误，请重新输入！")
            
            def on_cancel():
                """取消输入"""
                temp_root.quit()  # 退出对话框
                exit()  # 退出程序
            
            # 创建对话框
            dialog = tk.Toplevel(temp_root)
            dialog.title("🔑 卡密验证")
            dialog.geometry("400x200")
            dialog.minsize(350, 180)
            dialog.resizable(False, False)  # 不允许调整大小
            
            # 设置窗口居中
            dialog.update_idletasks()
            width = dialog.winfo_width()
            height = dialog.winfo_height()
            x = (dialog.winfo_screenwidth() // 2) - (width // 2)
            y = (dialog.winfo_screenheight() // 2) - (height // 2)
            dialog.geometry(f"{width}x{height}+{x}+{y}")
            
            # 设置窗口图标
            set_window_icon(dialog)
            
            # 创建对话框内容
            frame = tk.Frame(dialog, padx=20, pady=20)
            frame.pack(fill=tk.BOTH, expand=True)
            
            # 标题
            title_label = tk.Label(frame, text="请输入卡密", font=("Segoe UI", 14, "bold"))
            title_label.pack(pady=(0, 20))
            
            # 卡密输入框
            card_key_entry = tk.Entry(frame, textvariable=card_key, font=("Segoe UI", 12), width=30)
            card_key_entry.pack(pady=(0, 20))
            card_key_entry.focus_set()  # 设置焦点
            
            # 绑定回车键提交
            card_key_entry.bind("<Return>", lambda event: on_submit())
            
            # 按钮框架
            button_frame = tk.Frame(frame)
            button_frame.pack(fill=tk.X, pady=(0, 10))
            
            # 取消按钮
            cancel_btn = tk.Button(button_frame, text="取消", command=on_cancel, width=12)
            cancel_btn.pack(side=tk.LEFT, padx=(0, 10))
            
            # 确定按钮
            submit_btn = tk.Button(button_frame, text="确定", command=on_submit, width=12)
            submit_btn.pack(side=tk.RIGHT)
            
            # 禁用关闭按钮
            def on_close():
                exit()  # 退出程序
            
            dialog.protocol("WM_DELETE_WINDOW", on_close)
            
            # 运行对话框
            temp_root.mainloop()
            
            # 销毁临时窗口
            temp_root.destroy()
            
            return card_key.get().strip() if result[0] else None
        
        # 运行卡密输入对话框
        input_card_key = create_card_key_window()
        
        if input_card_key:
            # 保存卡密和硬件信息
            try:
                # 读取现有参数
                with open(PARAMETER_FILE, "r", encoding="utf-8") as f:
                    params = json.load(f)
            except Exception:
                params = {}
            
            # 更新卡密和硬件信息
            params[CARD_KEY_SAVE_KEY] = input_card_key
            params[HARDWARE_INFO_SAVE_KEY] = current_hardware
            
            # 保存更新后的参数
            with open(PARAMETER_FILE, "w", encoding="utf-8") as f:
                json.dump(params, f)
            
            print("✅ [卡密] 验证成功！")
            print("💾 [卡密] 卡密和硬件信息已保存")
        else:
            print("❌ [卡密] 卡密验证失败，程序退出")
            exit()
    else:
        # 验证通过
        print("✅ [卡密] 卡密验证通过")


# =========================
# 硬件信息获取
# =========================
def get_hardware_info():
    """
    获取硬件信息，包括CPU型号、CPU序列号、GPU型号和电脑账号
    返回格式化的硬件信息字符串
    """
    hardware_info = {}
    
    # 获取电脑账号
    try:
        hardware_info['username'] = getpass.getuser()
    except Exception as e:
        hardware_info['username'] = f"获取失败: {e}"
    
    # 获取CPU信息
    try:
        if WMI_AVAILABLE:
            w = wmi.WMI()
            for processor in w.Win32_Processor():
                hardware_info['cpu_model'] = processor.Name.strip()
                break
        else:
            hardware_info['cpu_model'] = "获取失败: wmi不可用"
    except Exception as e:
        hardware_info['cpu_model'] = f"获取失败: {e}"
    
    # 获取CPU序列号
    try:
        if WMI_AVAILABLE:
            w = wmi.WMI()
            for processor in w.Win32_Processor():
                hardware_info['cpu_serial'] = processor.ProcessorId.strip()
                break
        else:
            hardware_info['cpu_serial'] = "获取失败: wmi不可用"
    except Exception as e:
        hardware_info['cpu_serial'] = f"获取失败: {e}"
    
    # 获取内存信息
    try:
        if PSUTIL_AVAILABLE:
            total_memory = psutil.virtual_memory().total
            # 转换为GB
            total_memory_gb = round(total_memory / (1024 ** 3), 2)
            hardware_info['memory'] = f"{total_memory_gb} GB"
        else:
            hardware_info['memory'] = "获取失败: psutil不可用"
    except Exception as e:
        hardware_info['memory'] = f"获取失败: {e}"
    
    # 获取硬盘信息
    try:
        if WMI_AVAILABLE:
            w = wmi.WMI()
            disk_info = []
            for disk in w.Win32_DiskDrive():
                if disk.Model:
                    disk_info.append(disk.Model.strip())
            hardware_info['disk'] = ", ".join(disk_info) if disk_info else "未知"
        else:
            hardware_info['disk'] = "获取失败: wmi不可用"
    except Exception as e:
        hardware_info['disk'] = f"获取失败: {e}"
    
    # 获取网卡信息
    try:
        if PSUTIL_AVAILABLE:
            net_if_addrs = psutil.net_if_addrs()
            mac_addresses = []
            for interface_name, addresses in net_if_addrs.items():
                for address in addresses:
                    if address.family == psutil.AF_LINK:
                        mac_addresses.append(address.address)
            hardware_info['network'] = ", ".join(mac_addresses) if mac_addresses else "未知"
        else:
            hardware_info['network'] = "获取失败: psutil不可用"
    except Exception as e:
        hardware_info['network'] = f"获取失败: {e}"
    
    # 获取GPU信息
    try:
        if WMI_AVAILABLE:
            w = wmi.WMI()
            gpu_info = []
            for gpu in w.Win32_VideoController():
                if gpu.Name:
                    gpu_info.append(gpu.Name.strip())
            hardware_info['gpu_model'] = ", ".join(gpu_info) if gpu_info else "未知"
        else:
            hardware_info['gpu_model'] = "获取失败: wmi不可用"
    except Exception as e:
        hardware_info['gpu_model'] = f"获取失败: {e}"
    
    # 格式化硬件信息字符串，按照顺序：cpu|内存|硬盘|网卡|gpu型号
    # 保留username和cpu_serial作为前两个字段，保持与现有逻辑兼容
    hardware_str = f"{hardware_info['username']}|{hardware_info['cpu_model']}|{hardware_info['memory']}|{hardware_info['disk']}|{hardware_info['network']}|{hardware_info['gpu_model']}"
    return hardware_str


# =========================
# 简化版音效管理器
# =========================
class SimpleSoundManager:
    """简化版音效管理器，只使用winsound和控制台铃声"""

    def __init__(self):
        self.enabled = True
        self.can_use_winsound = False
        self._playing = False  # 防止重复播放
        self._lock = threading.Lock()  # 线程锁

        try:
            import winsound

            self.can_use_winsound = True
            print("🔊 [音效] 使用winsound播放音效")
        except ImportError:
            print("🔊 [音效] 使用控制台铃声")

    def _safe_beep(self, frequency, duration):
        """安全的蜂鸣函数"""
        if not self.enabled:
            return

        try:
            if self.can_use_winsound:
                import winsound

                winsound.Beep(frequency, duration)
            else:
                print("\a", end="", flush=True)
        except:
            # 音效失败时静默处理
            pass

    def play_start(self):
        """播放启动音效"""
        with self._lock:
            if not self.enabled or self._playing:
                return
            self._playing = True

        # 在独立线程中播放，避免阻塞
        def _play():
            try:
                self._safe_beep(1000, 200)
                time.sleep(0.05)
                self._safe_beep(1200, 150)
            finally:
                with self._lock:
                    self._playing = False

        threading.Thread(target=_play, daemon=True).start()

    def play_pause(self):
        """播放暂停音效"""
        with self._lock:
            if not self.enabled or self._playing:
                return
            self._playing = True

        def _play():
            try:
                self._safe_beep(600, 200)
                time.sleep(0.05)
                self._safe_beep(500, 150)
            finally:
                with self._lock:
                    self._playing = False

        threading.Thread(target=_play, daemon=True).start()

    def play_resume(self):
        """播放恢复音效"""
        with self._lock:
            if not self.enabled or self._playing:
                return
            self._playing = True

        def _play():
            try:
                self._safe_beep(800, 200)
                time.sleep(0.05)
                self._safe_beep(900, 150)
            finally:
                with self._lock:
                    self._playing = False

        threading.Thread(target=_play, daemon=True).start()


# 使用简化版
sound_manager = SimpleSoundManager()


# =========================
# 全局资源路径管理
# =========================
def get_icon_path():
    """获取logo.ico图标的路径，处理不同环境下的路径问题

    Returns:
        str: logo.ico图标的完整路径
    """
    import sys
    import os

    if hasattr(sys, "_MEIPASS"):
        # 打包后直接在MEIPASS下查找
        icon_path = os.path.join(sys._MEIPASS, "logo.ico")
    else:
        # 开发环境下直接使用当前目录
        icon_path = "logo.ico"

    return icon_path


def get_resources_path():
    """获取resources目录的路径，处理不同环境下的路径问题

    Returns:
        str: resources目录的完整路径
    """
    import sys
    import os

    if hasattr(sys, "_MEIPASS"):
        # 打包后resources目录在MEIPASS下
        resources_path = os.path.join(sys._MEIPASS, "resources")
    else:
        # 开发环境下直接使用当前目录下的resources
        resources_path = os.path.join(".", "resources")

    return resources_path


def set_window_icon(window):
    """设置窗口图标，同时支持窗口和任务栏

    Args:
        window: 要设置图标的窗口对象
    """
    try:
        import tkinter as tk

        # 获取图标路径
        icon_path = get_icon_path()

        # 尝试使用iconphoto方法设置图标（同时支持窗口和任务栏）
        try:
            icon = tk.PhotoImage(file=icon_path)
            window.iconphoto(True, icon)
        except Exception as e1:
            # 如果iconphoto失败，尝试回退到iconbitmap
            try:
                window.iconbitmap(icon_path)
            except Exception as e2:
                print(f"⚠️  [警告] 设置窗口图标失败: {e2}")
    except Exception as e:
        print(f"⚠️  [警告] 设置窗口图标时发生错误: {e}")


# =========================
# OCR引擎初始化（使用rapidocr，速度快）
# =========================
try:
    from rapidocr_onnxruntime import RapidOCR

    ocr_engine = RapidOCR()
    OCR_AVAILABLE = True
    print("✅ [OCR] RapidOCR 引擎加载成功")
except ImportError:
    OCR_AVAILABLE = False
    ocr_engine = None
    print("⚠️  [OCR] RapidOCR 未安装，钓鱼记录功能将不可用")

# =========================
# 鱼桶满检测设置
# =========================
FISH_BUCKET_FULL_TEXT = "鱼桶满了，无法钓鱼"
fish_bucket_full_detected = False
fish_bucket_sound_enabled = True  # 是否启用鱼桶满/没鱼饵警告!音效

# 鱼桶满/没鱼饵！检测模式
# mode1: 自动暂停
# mode2: 按下一次F键然后一直鼠标左键，但检测到键盘活动时自动停止
# mode3: 不会自动暂停，只会按下一次F键
bucket_detection_mode = "mode1"  # 默认模式

# 抛竿间隔检测相关设置
casting_timestamps = []  # 存储最近的抛竿时间戳
casting_interval_lock = threading.Lock()  # 保护抛竿时间戳的线程锁
CASTING_INTERVAL_THRESHOLD = 1.0  # 抛竿间隔阈值（秒）
REQUIRED_CONSECUTIVE_MATCHES = 4  # 需要连续匹配的次数
bucket_full_by_interval = False  # 标记是否通过间隔检测到鱼桶满/没鱼饵！

# 操作状态标志，用于协调抛杆和放生操作
is_casting = False  # 当前是否正在抛杆
is_releasing = False  # 当前是否正在放生
operation_lock = threading.Lock()  # 保护操作状态的线程锁


# =========================
# 调试信息管理函数
# =========================
def add_debug_info(info):
    """添加调试信息到队列和历史记录"""
    if not debug_mode:
        return

    # 添加到队列（用于实时通知）
    try:
        debug_info_queue.put_nowait(info)
    except queue.Full:
        try:
            debug_info_queue.get_nowait()
            debug_info_queue.put_nowait(info)
        except:
            pass

    # 添加到历史记录（用于保留历史信息）
    with debug_history_lock:
        debug_info_history.append(info)
        # 保持历史记录不超过200条
        if len(debug_info_history) > 200:
            debug_info_history.pop(0)  # 移除最旧的记录


# =========================
# 运行日志系统
# =========================
# 运行日志队列，用于存储所有控制台输出信息
log_queue = queue.Queue(maxsize=1000)
log_history = []  # 日志历史记录
log_history_max = 500  # 最大保存500条日志
log_history_lock = threading.Lock()  # 保护日志历史记录的线程锁

# 重定向标准输出到日志系统
import sys
import io


class LogRedirector:
    """重定向标准输出到日志系统"""

    def __init__(self, original_stream):
        self.original_stream = original_stream
        self.buffer = io.StringIO()

    def write(self, text):
        # 写入到原始流，只有当original_stream不为None时才写入
        if self.original_stream is not None:
            self.original_stream.write(text)
        # 如果文本不为空，添加到日志队列
        if text.strip():
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] {text.rstrip()}"

            # 添加到队列
            try:
                log_queue.put_nowait(log_entry)
            except queue.Full:
                # 队列满时移除最旧的条目
                try:
                    log_queue.get_nowait()
                    log_queue.put_nowait(log_entry)
                except:
                    pass

            # 添加到历史记录
            with log_history_lock:
                log_history.append(log_entry)
                # 保持历史记录不超过最大限制
                if len(log_history) > log_history_max:
                    log_history.pop(0)

        # 写入到缓冲区（如果需要）
        self.buffer.write(text)

    def flush(self):
        if self.original_stream is not None:
            self.original_stream.flush()
        self.buffer.flush()


# 重定向标准输出和标准错误
sys.stdout = LogRedirector(sys.stdout)
sys.stderr = LogRedirector(sys.stderr)

# =========================
# 线程锁 - 保护共享变量
# =========================
param_lock = threading.Lock()  # 参数读写锁

# =========================
# 钓鱼记录开关
# =========================
record_fish_enabled = True  # 默认启用钓鱼记录
legendary_screenshot_enabled = True  # 默认关闭传奇鱼自动截屏
first_capture_screenshot_enabled = True  # 默认启用首次捕获自动截屏

# =========================
# 放生功能设置
# =========================
release_fish_enabled = False  # 是否启用放生功能
release_standard_enabled = False  # 是否放生标准鱼
release_uncommon_enabled = False  # 是否放生非凡鱼
release_rare_enabled = False  # 是否放生稀有鱼
release_epic_enabled = False  # 是否放生史诗鱼
release_legendary_enabled = False  # 是否放生传奇鱼
release_phantom_rare_enabled = False  # 是否放生幻神稀有鱼

# =========================
# 字体大小设置
# =========================
font_size = 100  # 默认字体大小

input_entries = []  # 保存所有输入框引用，用于后续字体更新
combo_boxes = []  # 保存所有组合框引用，用于后续字体更新
fish_tree_ref = None  # 保存钓鱼记录Treeview引用，用于动态调整列宽

# =========================
# 调试功能设置
# =========================
debug_mode = True  # 调试模式开关，默认开启
debug_info_queue = queue.Queue(maxsize=200)  # 调试信息队列，用于线程间通信
debug_info_history = []  # 调试信息历史记录，最多保存200条
debug_history_lock = threading.Lock()  # 保护调试历史记录的线程锁
debug_window = None  # 调试窗口引用
debug_auto_refresh = True  # 是否自动刷新调试信息

# =========================
# 时间抖动配置
# =========================
JITTER_RANGE = 0  # 时间抖动范围 ±0%
# 保存上次操作的时间戳
last_operation_time = None
last_operation_type = None


def add_jitter(base_time):
    """为给定的基础时间添加随机抖动

    Args:
        base_time: 基础时间（秒）

    Returns:
        float: 添加抖动后的时间（秒）
    """
    if base_time <= 0:
        return base_time

    # 计算抖动范围（±JITTER_RANGE%）
    jitter_factor = random.uniform(1 - JITTER_RANGE / 100, 1 + JITTER_RANGE / 100)
    jittered_time = base_time * jitter_factor

    # 确保时间不为负数且保持精度
    return max(0.01, round(jittered_time, 3))


def print_timing_info(operation_type, base_time, actual_time, previous_interval=None):
    """打印时间抖动信息

    Args:
        operation_type: 操作类型字符串
        base_time: 基础时间（秒）
        actual_time: 实际执行时间（秒）
        previous_interval: 与上次操作的时间间隔（秒）
    """
    global last_operation_time, last_operation_type

    current_time = time.time()

    # 计算与基础时间的偏差百分比
    deviation = ((actual_time - base_time) / base_time) * 100 if base_time > 0 else 0
    deviation_str = f"{deviation:+.1f}%"

    # 直接使用偏差字符串，不添加颜色
    deviation_display = deviation_str

    # 计算与上次操作的时间间隔
    interval_info = ""
    if last_operation_time is not None:
        interval = current_time - last_operation_time
        expected_interval = base_time if last_operation_type == operation_type else None

        if expected_interval is not None and expected_interval > 0:
            interval_deviation = (
                (interval - expected_interval) / expected_interval
            ) * 100
            interval_str = f"{interval:.3f}s ({interval_deviation:+.1f}%)"

            # 直接使用间隔字符串，不添加颜色
            interval_info = f" | 间隔: {interval_str}"

    # 更新最后操作信息
    last_operation_time = current_time
    last_operation_type = operation_type

    # 打印信息
    print(
        f"⏱️  [时间] {operation_type}: 基础={base_time:.3f}s, 实际={actual_time:.3f}s ({deviation_display}){interval_info}"
    )


# =========================
# 参数文件路径
# =========================
PARAMETER_FILE = "./parameters.json"

# =========================
# 配置管理
# =========================
# 配置只管理5个核心钓鱼参数：t, leftclickdown, leftclickup, times, paogantime
# 其他参数保持全局设置，不受配置切换影响

# 配置数量限制
MAX_CONFIGS = 4

# 当前配置索引（0-3）
current_config_index = 0

# 配置名称
config_names = ["配置1", "配置2", "配置3", "配置4"]

# 配置参数，保存5个核心钓鱼参数
config_params = [
    # 配置1
    {"t": 0.9, "leftclickdown": 1, "leftclickup": 0.7, "times": 25, "paogantime": 2},
    # 配置2
    {
        "t": 0.5,
        "leftclickdown": 0.9,
        "leftclickup": 0.5,
        "times": 25,
        "paogantime": 3,
    },
    # 配置3
    {
        "t": 0.2,
        "leftclickdown": 0.4,
        "leftclickup": 0.2,
        "times": 25,
        "paogantime": 0.1,
    },
    # 配置4
    {
        "t": 0.2,
        "leftclickdown": 1.5,
        "leftclickup": 1.0,
        "times": 25,
        "paogantime": 0.1,
    },
]


# =========================
# 初始化字体样式
# =========================
def init_font_styles(style, font_size_percent):
    """初始化所有字体样式

    Args:
        style: ttkbootstrap.Style对象
        font_size_percent: 字体大小百分比（50-200）
    """
    # 缩放因子
    scale_factor = font_size_percent / 100.0

    # 基础字体设置
    base_font = "Segoe UI"

    # 定义不同控件的字体大小
    font_sizes = {
        "Title": int(14 * scale_factor),  # 标题字体大小
        "Subtitle": int(8 * scale_factor),  # 副标题字体大小
        "Label": int(9 * scale_factor),  # 普通标签字体大小
        "Entry": int(9 * scale_factor),  # 输入框字体大小
        "Button": int(9 * scale_factor),  # 按钮字体大小
        "Treeview": int(9 * scale_factor),  # 树视图字体大小
        "Combobox": int(9 * scale_factor),  # 组合框字体大小
        "Small": int(7 * scale_factor),  # 小号字体大小
        "Stats": int(10 * scale_factor),  # 统计信息字体大小
        "StatsTotal": int(11 * scale_factor),  # 总计统计字体大小
        "LogText": int(8 * scale_factor),  # 日志文本字体大小
    }

    # 确保字体大小在合理范围内
    for key in font_sizes:
        font_sizes[key] = max(5, min(30, font_sizes[key]))

    # 更新各种控件的字体样式
    try:
        # 1. 更新标签样式
        label_font = (base_font, font_sizes["Label"])
        label_styles = ["TLabel", "TLabelframe.Label", "Status.TLabel", "Stats.TLabel"]
        for style_name in label_styles:
            style.configure(style_name, font=label_font)

        # 2. 更新输入框样式
        entry_font = (base_font, font_sizes["Entry"])
        entry_styles = ["TEntry", "Entry"]
        for style_name in entry_styles:
            style.configure(style_name, font=entry_font)

        # 3. 更新组合框样式（包括下拉列表）
        combobox_font = (base_font, font_sizes["Combobox"])
        combobox_styles = [
            "TCombobox",
            "Combobox",
            "TCombobox.Listbox",
            "Combobox.Listbox",
        ]
        for style_name in combobox_styles:
            style.configure(style_name, font=combobox_font)

        # 4. 更新复选框样式
        style.configure("TCheckbutton", font=label_font)

        # 5. 更新树视图样式
        treeview_font = (base_font, font_sizes["Treeview"])
        treeview_rowheight = int(font_sizes["Treeview"] * 2.2)
        treeview_styles = [
            ("Treeview", treeview_font, treeview_rowheight),
            ("CustomTreeview.Treeview", treeview_font, treeview_rowheight),
        ]
        for style_name, font, rowheight in treeview_styles:
            style.configure(style_name, font=font, rowheight=rowheight)
            style.configure(
                f"{style_name}.Heading", font=(base_font, font_sizes["Label"], "bold")
            )

        # 6. 更新滑块样式
        scale_styles = ["Horizontal.TScale", "Vertical.TScale"]
        for style_name in scale_styles:
            style.configure(style_name, font=label_font)

        # 7. 更新单选按钮样式
        radiobutton_styles = {
            "TRadiobutton": label_font,
            "Toolbutton.TRadiobutton": label_font,
            "InfoOutline.TRadiobutton": label_font,
            "SuccessOutline.TRadiobutton": label_font,
            "DangerOutline.TRadiobutton": label_font,
            "InfoOutline.Toolbutton.TRadiobutton": label_font,
            "SuccessOutline.Toolbutton.TRadiobutton": label_font,
            "DangerOutline.Toolbutton.TRadiobutton": label_font,
            "WarningOutline.Toolbutton.TRadiobutton": label_font,
            "SecondaryOutline.Toolbutton.TRadiobutton": label_font,
        }
        for style_name, font in radiobutton_styles.items():
            style.configure(style_name, font=font)

        # 8. 更新按钮样式
        button_font = (base_font, font_sizes["Button"])

        # 基础按钮样式
        base_button_styles = [
            "TButton",
            "Button",
            "Toolbutton",
            "Outline.TButton",
            "Toolbutton.TButton",
            "Outline.Toolbutton.TButton",
        ]
        for style_name in base_button_styles:
            style.configure(style_name, font=button_font)

        # 特定按钮样式变体
        specific_button_styles = [
            "InfoOutline.TButton",
            "SuccessOutline.TButton",
            "DangerOutline.TButton",
            "WarningOutline.TButton",
            "SecondaryOutline.TButton",
            "InfoOutline.Toolbutton.TButton",
            "SuccessOutline.Toolbutton.TButton",
            "DangerOutline.Toolbutton.TButton",
            "WarningOutline.Toolbutton.TButton",
            "SecondaryOutline.Toolbutton.TButton",
            "SuccessOutline.Toolbutton",
            "DangerOutline.Toolbutton",
            "InfoOutline.Toolbutton",
            "WarningOutline.Toolbutton",
            "SecondaryOutline.Toolbutton",
        ]
        for style_name in specific_button_styles:
            style.configure(style_name, font=button_font)

        # 颜色变体按钮样式
        color_variants = [
            "Primary",
            "Secondary",
            "Success",
            "Info",
            "Warning",
            "Danger",
            "Light",
            "Dark",
        ]
        color_button_templates = [
            f"{{}}.TButton",
            f"{{}}Outline.TButton",
            f"{{}}.Toolbutton.TButton",
            f"{{}}Outline.Toolbutton.TButton",
        ]
        bootstyle_templates = [f"{{}}-toolbutton", f"{{}}-outline-toolbutton"]

        for color in color_variants:
            # 颜色按钮样式
            for template in color_button_templates:
                style_name = template.format(color)
                style.configure(style_name, font=button_font)

            # 直接使用bootstyle名称作为样式
            for template in bootstyle_templates:
                style_name = template.format(color.lower())
                style.configure(style_name, font=button_font)

        # 9. 更新日志文本样式
        log_font = (base_font, font_sizes["LogText"])
        style.configure("LogText.TText", font=log_font)
    except Exception as e:
        print(f"Error initializing font styles: {e}")


# =========================
# 更新所有控件的字体
# =========================
def update_all_widget_fonts(widget, style, font_size_percent):
    """更新所有控件的字体大小

    Args:
        widget: 根控件
        style: ttkbootstrap.Style对象
        font_size_percent: 字体大小百分比（50-200）
    """
    # 初始化字体样式 - 这会更新所有控件的样式字体
    init_font_styles(style, font_size_percent)

    # 缩放因子
    scale_factor = font_size_percent / 100.0
    base_font = "Segoe UI"

    # 定义默认字体大小
    default_sizes = {
        "Label": 9,
        "Button": 9,
        "Entry": 9,
        "Combobox": 9,
        "Radiobutton": 9,
        "Checkbutton": 9,
        "Treeview": 9,
        "LogText": 8,
    }

    # 递归更新所有控件的字体
    def update_widget_font(w):
        try:
            widget_type = type(w).__name__

            # 确定默认字体大小
            if widget_type in ["Label", "TLabel", "TTKLabel"] or "Label" in widget_type:
                default_size = default_sizes["Label"]
            elif (
                widget_type in ["Button", "TButton", "TTKButton"]
                or "Button" in widget_type
            ):
                default_size = default_sizes["Button"]
            elif (
                widget_type in ["Entry", "TEntry", "TTKEntry"] or "Entry" in widget_type
            ):
                default_size = default_sizes["Entry"]
            elif (
                widget_type in ["Combobox", "TCombobox", "TTKCombobox"]
                or "Combobox" in widget_type
            ):
                default_size = default_sizes["Combobox"]
            elif (
                widget_type in ["Radiobutton", "TRadiobutton", "TTKRadiobutton"]
                or "Radiobutton" in widget_type
            ):
                default_size = default_sizes["Radiobutton"]
            elif (
                widget_type in ["Checkbutton", "TCheckbutton", "TTKCheckbutton"]
                or "Checkbutton" in widget_type
            ):
                default_size = default_sizes["Checkbutton"]
            elif (
                widget_type in ["Treeview", "TTKTreeview"] or "Treeview" in widget_type
            ):
                default_size = default_sizes["Treeview"]
            elif widget_type in ["Text", "TKText", "TTKText"] or "Text" in widget_type:
                default_size = default_sizes["LogText"]
            elif (
                widget_type in ["Frame", "TFrame", "TTKFrame"] or "Frame" in widget_type
            ):
                # 跳过框架，只处理其内部控件
                pass
            else:
                # 对于其他控件类型，尝试将其作为按钮处理，特别是ttkbootstrap按钮
                # 检查控件是否有configure方法，尝试获取其样式
                try:
                    style_name = w.cget("style")
                    if "Button" in style_name or "Toolbutton" in style_name:
                        default_size = default_sizes["Button"]
                    else:
                        return  # 跳过不支持字体的控件
                except:
                    return  # 跳过不支持字体的控件

            # 计算新字体大小
            new_size = int(default_size * scale_factor)
            new_size = max(5, min(30, new_size))

            # 构建新字体
            new_font = (base_font, new_size)

            # 特殊处理标题和粗体文本
            try:
                if widget_type == "Label" and (
                    "PartyFish" in str(w.cget("text")) or "标题" in str(w.cget("text"))
                ):
                    new_font = (base_font, int(14 * scale_factor), "bold")
                elif widget_type == "Label" and "统计" in str(w.cget("text")):
                    new_font = (base_font, int(10 * scale_factor), "bold")
                elif widget_type == "Label" and "运行日志" in str(w.cget("text")):
                    new_font = (base_font, int(10 * scale_factor), "bold")
            except:
                pass

            # 尝试直接更新控件字体，如果失败则跳过
            try:
                w.configure(font=new_font)
            except Exception as e:
                # 对于ttkbootstrap按钮，可能无法直接设置字体，需要通过样式更新
                # 这已经在init_font_styles中处理了，所以这里可以安全跳过
                pass

        except Exception as e:
            # 跳过不支持字体的控件
            pass

        # 递归处理子控件
        for child in w.winfo_children():
            update_widget_font(child)

    # 开始递归更新
    update_widget_font(widget)

    # 重新配置所有已创建的控件，应用新的样式设置
    widget.update_idletasks()


# =========================
# 加载和保存参数
# =========================
def save_parameters():
    """保存参数到文件"""
    # 保存当前配置的核心参数
    config_params[current_config_index] = {
        "t": t,
        "leftclickdown": leftclickdown,
        "leftclickup": leftclickup,
        "times": times,
        "paogantime": paogantime,
    }

    params = {
        # 保存配置信息
        "config_names": config_names,
        "config_params": config_params,
        "current_config_index": current_config_index,
        # 保存全局参数（不受配置切换影响）
        "jiashi_var": jiashi_var,
        "resolution": resolution_choice,
        "custom_width": TARGET_WIDTH,
        "custom_height": TARGET_HEIGHT,
        "hotkey": hotkey_name,
        "uno_hotkey": uno_hotkey_name,
        "record_fish_enabled": record_fish_enabled,
        "legendary_screenshot_enabled": legendary_screenshot_enabled,
        "first_capture_screenshot_enabled": first_capture_screenshot_enabled,
        "font_size": font_size,
        "jitter_range": JITTER_RANGE,
        "fish_bucket_sound_enabled": fish_bucket_sound_enabled,
        "bucket_detection_mode": bucket_detection_mode,  # 新增保存鱼桶检测模式
        "bait_recognition_algorithm": bait_recognition_algorithm,  # 新增保存鱼饵识别算法
        # 放生功能设置
        "release_fish_enabled": release_fish_enabled,
        "release_standard_enabled": release_standard_enabled,
        "release_uncommon_enabled": release_uncommon_enabled,
        "release_rare_enabled": release_rare_enabled,
        "release_epic_enabled": release_epic_enabled,
        "release_legendary_enabled": release_legendary_enabled,
        "release_phantom_rare_enabled": release_phantom_rare_enabled,
        # 卡密和硬件信息（从现有文件读取，避免覆盖）
        CARD_KEY_SAVE_KEY: None,
        HARDWARE_INFO_SAVE_KEY: None,
    }
    
    # 读取现有卡密和硬件信息，避免覆盖
    try:
        with open(PARAMETER_FILE, "r", encoding="utf-8") as f:
            existing_params = json.load(f)
            params[CARD_KEY_SAVE_KEY] = existing_params.get(CARD_KEY_SAVE_KEY, None)
            params[HARDWARE_INFO_SAVE_KEY] = existing_params.get(HARDWARE_INFO_SAVE_KEY, None)
    except Exception:
        pass  # 文件不存在或解析错误，保持默认值

    try:
        with open(PARAMETER_FILE, "w", encoding="utf-8") as f:
            json.dump(params, f)
        print("💾 [保存] 参数已成功保存到文件")
    except Exception as e:
        print(f"❌ [错误] 保存参数失败: {e}")


def load_parameters():
    """从文件加载参数"""
    global fish_bucket_sound_enabled, bucket_detection_mode  # 新增加载鱼桶满/没鱼饵警告!音效开关状态和检测模式
    global t, leftclickdown, leftclickup, times, paogantime, jiashi_var
    global resolution_choice, TARGET_WIDTH, TARGET_HEIGHT, SCALE_X, SCALE_Y
    global hotkey_name, hotkey_modifiers, hotkey_main_key
    global font_size, record_fish_enabled, legendary_screenshot_enabled, first_capture_screenshot_enabled
    global config_names, config_params, current_config_index
    global JITTER_RANGE
    global bait_recognition_algorithm  # 新增加载鱼饵识别算法
    global uno_hotkey_name, uno_hotkey_modifiers, uno_hotkey_main_key  # 添加UNO热键全局变量
    global release_fish_enabled, release_standard_enabled, release_uncommon_enabled, release_rare_enabled, release_epic_enabled, release_legendary_enabled, release_phantom_rare_enabled  # 添加放生功能全局变量
    try:
        with open(PARAMETER_FILE, "r", encoding="utf-8") as f:
            params = json.load(f)

            # 加载配置信息
            if "config_names" in params:
                config_names = params["config_names"]
            if "config_params" in params:
                config_params = params["config_params"]
            if "current_config_index" in params:
                current_config_index = params["current_config_index"]

            # 加载当前配置的核心参数
            current_config = config_params[current_config_index]
            t = current_config["t"]
            leftclickdown = current_config["leftclickdown"]
            leftclickup = current_config["leftclickup"]
            times = current_config["times"]
            paogantime = current_config["paogantime"]

            # 加载全局参数
            jiashi_var = params.get("jiashi_var", jiashi_var)
            resolution_choice = params.get("resolution", "2K")
            # 加载钓鱼记录开关状态
            record_fish_enabled = params.get("record_fish_enabled", True)
            # 加载传奇鱼自动截屏开关状态
            legendary_screenshot_enabled = params.get(
                "legendary_screenshot_enabled", True
            )
            # 加载首次捕获自动截屏开关状态
            first_capture_screenshot_enabled = params.get(
                "first_capture_screenshot_enabled", True
            )
            # 加载字体大小设置
            font_size = params.get("font_size", 100)  # 默认100%
            # 加载时间抖动范围
            JITTER_RANGE = params.get("jitter_range", 0)
            # 加载鱼桶满/没鱼饵！音效开关状态
            fish_bucket_sound_enabled = params.get("fish_bucket_sound_enabled", True)
            # 加载鱼桶检测模式
            bucket_detection_mode = params.get("bucket_detection_mode", "mode1")
            # 加载鱼饵识别算法
        bait_recognition_algorithm = params.get(
            "bait_recognition_algorithm", "template"
        )
        # 加载放生功能设置
        release_fish_enabled = params.get("release_fish_enabled", False)
        release_standard_enabled = params.get("release_standard_enabled", False)
        release_uncommon_enabled = params.get("release_uncommon_enabled", False)
        release_rare_enabled = params.get("release_rare_enabled", False)
        release_epic_enabled = params.get("release_epic_enabled", False)
        release_legendary_enabled = params.get("release_legendary_enabled", False)
        release_phantom_rare_enabled = params.get("release_phantom_rare_enabled", False)

        # 加载热键设置（新格式支持组合键）
        saved_hotkey = params.get("hotkey", "F2")
        try:
            modifiers, main_key, main_key_name = parse_hotkey_string(saved_hotkey)
            if main_key is not None:
                hotkey_name = saved_hotkey
                hotkey_modifiers = modifiers
                hotkey_main_key = main_key
        except Exception:
            # 解析失败，使用默认值
            hotkey_name = "F2"
            hotkey_modifiers = set()
            hotkey_main_key = keyboard.Key.f2

        # 加载UNO热键设置
        saved_uno_hotkey = params.get("uno_hotkey", "F3")
        try:
            uno_modifiers, uno_main_key, uno_main_key_name = parse_hotkey_string(
                saved_uno_hotkey
            )
            if uno_main_key is not None:
                uno_hotkey_name = saved_uno_hotkey
                uno_hotkey_modifiers = uno_modifiers
                uno_hotkey_main_key = uno_main_key
        except Exception:
            # 解析失败，使用默认值
            uno_hotkey_name = "F3"
            uno_hotkey_modifiers = set()
            uno_hotkey_main_key = keyboard.Key.f3

        # 根据分辨率选择设置目标分辨率
        if resolution_choice == "1080P":
            TARGET_WIDTH, TARGET_HEIGHT = 1920, 1080
        elif resolution_choice == "2K":
            TARGET_WIDTH, TARGET_HEIGHT = 2560, 1440
        elif resolution_choice == "4K":
            TARGET_WIDTH, TARGET_HEIGHT = 3840, 2160
        elif resolution_choice == "current":
            # 使用当前系统分辨率
            TARGET_WIDTH, TARGET_HEIGHT = get_current_screen_resolution()
        elif resolution_choice == "自定义":
            TARGET_WIDTH = params.get("custom_width", 2560)
            TARGET_HEIGHT = params.get("custom_height", 1440)
    except FileNotFoundError:
        print("📄 [信息] 未找到参数文件，使用默认值")
    except Exception as e:
        print(f"❌ [错误] 加载参数失败: {e}")

    # 重新计算缩放比例
    SCALE_X = TARGET_WIDTH / BASE_WIDTH
    SCALE_Y = TARGET_HEIGHT / BASE_HEIGHT
    calculate_scale_factors()  # 计算所有缩放比例（包括SCALE_UNIFORM）
    update_region_coords()  # 更新区域坐标

    # 添加分辨率验证逻辑，确保分辨率设置正确
    # 获取当前系统实际分辨率
    actual_width, actual_height = get_current_screen_resolution()

    # 计算当前目标分辨率与实际分辨率的差异
    if resolution_choice in ["1080P", "2K", "4K"]:
        # 对于预设分辨率，检查实际分辨率是否匹配
        preset_width, preset_height = {
            "1080P": (1920, 1080),
            "2K": (2560, 1440),
            "4K": (3840, 2160),
        }[resolution_choice]

        # 计算宽度和高度差异百分比
        width_diff = abs(preset_width - actual_width) / actual_width * 100
        height_diff = abs(preset_height - actual_height) / actual_height * 100

        # 如果差异超过10%，自动切换到current模式
        if width_diff > 10 or height_diff > 10:
            print(
                f"⚠️  [警告] 保存的分辨率({resolution_choice})与实际分辨率({actual_width}×{actual_height})差异较大，自动切换到当前分辨率"
            )
            resolution_choice = "current"
            TARGET_WIDTH, TARGET_HEIGHT = actual_width, actual_height
            # 重新计算缩放比例
            SCALE_X = TARGET_WIDTH / BASE_WIDTH
            SCALE_Y = TARGET_HEIGHT / BASE_HEIGHT
            calculate_scale_factors()  # 计算所有缩放比例（包括SCALE_UNIFORM）
            update_region_coords()  # 更新区域坐标
    elif resolution_choice == "current":
        # 对于current模式，确保使用的是最新的实际分辨率
        if TARGET_WIDTH != actual_width or TARGET_HEIGHT != actual_height:
            TARGET_WIDTH, TARGET_HEIGHT = actual_width, actual_height
            # 重新计算缩放比例
            SCALE_X = TARGET_WIDTH / BASE_WIDTH
            SCALE_Y = TARGET_HEIGHT / BASE_HEIGHT
            calculate_scale_factors()  # 计算所有缩放比例（包括SCALE_UNIFORM）
            update_region_coords()  # 更新区域坐标

    # 更新全局当前分辨率变量
    global CURRENT_SCREEN_WIDTH, CURRENT_SCREEN_HEIGHT
    CURRENT_SCREEN_WIDTH, CURRENT_SCREEN_HEIGHT = actual_width, actual_height


def switch_config(index):
    """切换配置，只更新5个核心钓鱼参数"""
    global current_config_index, t, leftclickdown, leftclickup, times, paogantime

    if index < 0 or index >= MAX_CONFIGS:
        return False

    # 保存当前配置的参数
    config_params[current_config_index] = {
        "t": t,
        "leftclickdown": leftclickdown,
        "leftclickup": leftclickup,
        "times": times,
        "paogantime": paogantime,
    }

    # 切换到新配置
    current_config_index = index

    # 加载新配置的参数
    new_config = config_params[current_config_index]
    t = new_config["t"]
    leftclickdown = new_config["leftclickdown"]
    leftclickup = new_config["leftclickup"]
    times = new_config["times"]
    paogantime = new_config["paogantime"]

    # 保存参数
    save_parameters()

    return True


def rename_config(index, new_name):
    """重命名配置"""
    global config_names
    if index < 0 or index >= MAX_CONFIGS:
        return False

    config_names[index] = new_name
    save_parameters()
    return True


# =========================
# 更新参数
# =========================
def update_parameters(
    t_var,
    leftclickdown_var,
    leftclickup_var,
    times_var,
    paogantime_var,
    jiashi_var_option,
    resolution_var,
    custom_width_var,
    custom_height_var,
    hotkey_var=None,
    record_fish_var=None,
    legendary_screenshot_var=None,
    first_capture_screenshot_var=None,
    jitter_var=None,
    uno_hotkey_var_param=None,
    release_enabled_var=None,
    release_standard_var=None,
    release_uncommon_var=None,
    release_rare_var=None,
    release_epic_var=None,
    release_legendary_var=None,
    release_phantom_rare_var=None,
):
    global t, leftclickdown, leftclickup, times, paogantime, jiashi_var
    global resolution_choice, TARGET_WIDTH, TARGET_HEIGHT, SCALE_X, SCALE_Y
    global hotkey_name, hotkey_modifiers, hotkey_main_key
    global record_fish_enabled, legendary_screenshot_enabled, first_capture_screenshot_enabled, JITTER_RANGE, fish_bucket_sound_enabled
    global uno_hotkey_name, uno_hotkey_modifiers, uno_hotkey_main_key
    global release_fish_enabled, release_standard_enabled, release_uncommon_enabled, release_rare_enabled, release_epic_enabled, release_legendary_enabled, release_phantom_rare_enabled
    with param_lock:  # 使用锁保护参数更新
        try:
            t = float(t_var.get())
            leftclickdown = float(leftclickdown_var.get())
            leftclickup = float(leftclickup_var.get())
            times = int(times_var.get())
            paogantime = float(paogantime_var.get())
            jiashi_var = jiashi_var_option.get()

            # 更新钓鱼记录开关状态
            if record_fish_var is not None:
                record_fish_enabled = bool(record_fish_var.get())

            # 更新传奇鱼自动截屏开关状态
            if legendary_screenshot_var is not None:
                legendary_screenshot_enabled = bool(legendary_screenshot_var.get())

            # 更新首次捕获自动截屏开关状态
            if first_capture_screenshot_var is not None:
                first_capture_screenshot_enabled = bool(first_capture_screenshot_var.get())

            # 更新时间抖动范围
            if jitter_var is not None:
                JITTER_RANGE = int(jitter_var.get())

            # 更新放生功能设置
            if release_enabled_var is not None:
                release_fish_enabled = bool(release_enabled_var.get())
            if release_standard_var is not None:
                release_standard_enabled = bool(release_standard_var.get())
            if release_uncommon_var is not None:
                release_uncommon_enabled = bool(release_uncommon_var.get())
            if release_rare_var is not None:
                release_rare_enabled = bool(release_rare_var.get())
            if release_epic_var is not None:
                release_epic_enabled = bool(release_epic_var.get())
            if release_legendary_var is not None:
                release_legendary_enabled = bool(release_legendary_var.get())
            if 'release_phantom_rare_var' in locals() and release_phantom_rare_var is not None:
                release_phantom_rare_enabled = bool(release_phantom_rare_var.get())

            # 更新热键设置（新格式支持组合键）
            if hotkey_var is not None:
                new_hotkey = hotkey_var.get()
                if new_hotkey:
                    try:
                        modifiers, main_key, main_key_name = parse_hotkey_string(
                            new_hotkey
                        )
                        if main_key is not None:
                            hotkey_name = new_hotkey
                            hotkey_modifiers = modifiers
                            hotkey_main_key = main_key
                    except Exception:
                        pass  # 保持原有热键设置

            # 更新UNO热键设置
            if uno_hotkey_var_param is not None:
                new_uno_hotkey = uno_hotkey_var_param.get()
                if new_uno_hotkey:
                    try:
                        uno_modifiers, uno_main_key, uno_main_key_name = (
                            parse_hotkey_string(new_uno_hotkey)
                        )
                        if uno_main_key is not None:
                            uno_hotkey_name = new_uno_hotkey
                            uno_hotkey_modifiers = uno_modifiers
                            uno_hotkey_main_key = uno_main_key
                    except Exception as e:
                        print(f"❌ [错误] 解析UNO热键失败: {e}")
                        pass  # 保持原有UNO热键设置

            # 更新分辨率设置
            resolution_choice = resolution_var.get()
            if resolution_choice == "1080P":
                TARGET_WIDTH, TARGET_HEIGHT = 1920, 1080
            elif resolution_choice == "2K":
                TARGET_WIDTH, TARGET_HEIGHT = 2560, 1440
            elif resolution_choice == "4K":
                TARGET_WIDTH, TARGET_HEIGHT = 3840, 2160
            elif resolution_choice == "current":
                # 使用当前系统分辨率
                TARGET_WIDTH, TARGET_HEIGHT = get_current_screen_resolution()
                # 更新输入框显示
                custom_width_var.set(str(TARGET_WIDTH))
                custom_height_var.set(str(TARGET_HEIGHT))
            elif resolution_choice == "自定义":
                # 自定义分辨率限制
                min_width, max_width = 800, 7680
                min_height, max_height = 600, 4320

                # 获取输入值
                width = int(custom_width_var.get())
                height = int(custom_height_var.get())

                # 应用限制
                TARGET_WIDTH = max(min_width, min(max_width, width))
                TARGET_HEIGHT = max(min_height, min(max_height, height))

                # 更新输入框显示
                custom_width_var.set(str(TARGET_WIDTH))
                custom_height_var.set(str(TARGET_HEIGHT))

            # 重新计算缩放比例
            SCALE_X = TARGET_WIDTH / BASE_WIDTH
            SCALE_Y = TARGET_HEIGHT / BASE_HEIGHT
            calculate_scale_factors()  # 计算所有缩放比例（包括SCALE_UNIFORM）
            update_region_coords()  # 更新区域坐标

            print(f"┌" + "─" * 48 + "┐")
            print(f"│  ⚙️  参数更新成功                               │")
            print(f"├" + "─" * 48 + "┤")
            print(
                f"│  ⏱️  循环间隔: {t:.1f}s    📍 收线: {leftclickdown:.1f}s    📍 放线: {leftclickup:.1f}s".ljust(
                    40
                )
                + "│"
            )
            print(
                f"│  🎣 最大拉杆: {times}次     ⏳ 抛竿: {paogantime:.1f}s    {'✅' if jiashi_var else '❌'} 加时: {'是' if jiashi_var else '否'}".ljust(
                    40
                )
                + "│"
            )
            print(
                f"│  🖥️  分辨率: {resolution_choice} ({TARGET_WIDTH}×{TARGET_HEIGHT})".ljust(
                    40
                )
                + "│"
            )
            print(
                f"│  📐 缩放比例: X={SCALE_X:.2f}  Y={SCALE_Y:.2f}  统一={SCALE_UNIFORM:.2f}".ljust(
                    40
                )
                + "│"
            )
            print(
                f"│  🎯 鱼饵识别算法: {bait_recognition_algorithms[bait_recognition_algorithm]}".ljust(
                    40
                )
                + "│"
            )
            print(f"│  ⌨️  热键: {hotkey_name}".ljust(40) + "│")
            print(f"│  🎲 时间抖动: ±{JITTER_RANGE}%".ljust(40) + "│")
            print(f"└" + "─" * 48 + "┘")
            # 保存到文件
            save_parameters()
        except ValueError as e:
            print(f"⚠️  [警告] 请输入有效的数值！错误: {e}")
        except Exception as e:
            print(f"❌ [错误] 更新参数失败: {e}")


# =========================
# 调试功能
# =========================
def show_debug_window():
    """显示调试窗口，展示OCR识别的详细信息"""
    global debug_window, debug_auto_refresh

    if debug_window is not None and debug_window.winfo_exists():
        # 如果调试窗口已存在，先销毁它
        debug_window.destroy()

    # 创建调试窗口
    debug_window = ttkb.Toplevel()
    debug_window.title("🐛 调试信息")
    debug_window.geometry("800x600")
    debug_window.minsize(600, 400)
    debug_window.resizable(True, True)

    # 设置窗口图标（与主窗口相同）
    set_window_icon(debug_window)

    # 主框架
    main_frame = ttkb.Frame(debug_window, padding=12)
    main_frame.pack(fill=BOTH, expand=YES)

    # 标题
    title_label = ttkb.Label(
        main_frame,
        text="OCR 调试信息",
        font=("Segoe UI", 14, "bold"),
        bootstyle="primary",
    )
    title_label.pack(pady=(0, 10))

    # 控制框架
    control_frame = ttkb.Frame(main_frame)
    control_frame.pack(fill=X, pady=(0, 10))

    # 自动刷新开关
    auto_refresh_var = ttkb.BooleanVar(value=debug_auto_refresh)
    auto_refresh_check = ttkb.Checkbutton(
        control_frame, text="自动刷新", variable=auto_refresh_var, bootstyle="info"
    )
    auto_refresh_check.pack(side=LEFT)

    def toggle_auto_refresh():
        """切换自动刷新状态"""
        global debug_auto_refresh
        debug_auto_refresh = auto_refresh_var.get()

    auto_refresh_check.configure(command=toggle_auto_refresh)

    # 屏幕分辨率信息标签，显示在自动刷新右边
    def update_resolution_label():
        """更新分辨率信息标签"""
        max_width, max_height = get_max_screen_resolution()
        current_width, current_height = (
            get_current_screen_resolution()
        )  # 使用实际系统分辨率

        resolution_text = (
            f"🖥️  当前分辨率: {current_width}×{current_height} | 最大分辨率: {max_width}×{max_height}\n"
            + f"🖥️  缩放比例: X={SCALE_X:.2f} Y={SCALE_Y:.2f} 统一={SCALE_UNIFORM:.2f}"
        )
        resolution_label.configure(text=resolution_text)

    resolution_label = ttkb.Label(
        control_frame,
        font=("Consolas", 10),  # 增大字体大小，提高可读性
        bootstyle="info",
    )
    resolution_label.pack(side=TOP, fill=X, pady=(5, 0))  # 调整为顶部填充，增加垂直间距

    # 初始更新分辨率标签
    update_resolution_label()

    # 手动触发OCR按钮
    def manual_ocr_trigger():
        """手动触发OCR识别，用于测试调试功能"""
        temp_scr = None
        try:
            # 临时初始化scr对象
            debug_info = {
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[
                    :-3
                ],
                "action": "manual_ocr_start",
                "message": "开始手动触发OCR识别，正在初始化截图对象...",
            }
            add_debug_info(debug_info)
            update_debug_info()

            # 初始化mss截图对象
            temp_scr = mss.mss()

            # 添加调试信息，记录截图对象初始化成功
            debug_info = {
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[
                    :-3
                ],
                "action": "manual_ocr_scr_init",
                "message": "截图对象初始化成功，正在执行OCR识别...",
                "scr_type": type(temp_scr).__name__,
            }
            add_debug_info(debug_info)
            update_debug_info()

            # 调用OCR识别相关函数，传入临时初始化的scr对象
            img = capture_fish_info_region(temp_scr)
            if img is not None:
                fish_name, fish_quality, fish_weight = recognize_fish_info_ocr(img)
                # 添加调试信息，记录OCR识别结果
                debug_info = {
                    "timestamp": datetime.datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S.%f"
                    )[:-3],
                    "action": "manual_ocr_complete",
                    "parsed_info": {
                        "鱼名": fish_name if fish_name else "未识别",
                        "品质": fish_quality if fish_quality else "未识别",
                        "重量": fish_weight if fish_weight else "未识别",
                    },
                    "message": "手动触发OCR识别完成",
                    "image_shape": img.shape,
                    "scr_type": type(temp_scr).__name__,
                }
                add_debug_info(debug_info)
            else:
                # 添加调试信息，通知OCR识别失败
                debug_info = {
                    "timestamp": datetime.datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S.%f"
                    )[:-3],
                    "action": "manual_ocr_failed",
                    "message": "OCR识别失败，无法截取鱼信息区域",
                    "scr_type": type(temp_scr).__name__,
                }
                add_debug_info(debug_info)

            # 立即更新调试信息显示
            update_debug_info()
        except Exception as e:
            # 添加错误调试信息
            debug_info = {
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[
                    :-3
                ],
                "action": "manual_ocr_error",
                "error": f"手动触发OCR识别失败: {str(e)}",
                "exception_type": type(e).__name__,
            }
            add_debug_info(debug_info)
            # 立即更新调试信息显示
            update_debug_info()
        finally:
            # 确保scr对象正确关闭
            if temp_scr is not None:
                try:
                    temp_scr.close()
                    # 添加调试信息，记录截图对象关闭
                    debug_info = {
                        "timestamp": datetime.datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S.%f"
                        )[:-3],
                        "action": "manual_ocr_scr_close",
                        "message": "截图对象已关闭",
                        "scr_type": (
                            type(temp_scr).__name__ if temp_scr is not None else "未知"
                        ),
                    }
                    add_debug_info(debug_info)
                    update_debug_info()
                except Exception as close_error:
                    # 添加错误调试信息
                    debug_info = {
                        "timestamp": datetime.datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S.%f"
                        )[:-3],
                        "action": "manual_ocr_scr_close_error",
                        "error": f"关闭截图对象失败: {str(close_error)}",
                        "exception_type": type(close_error).__name__,
                    }
                    add_debug_info(debug_info)
                    update_debug_info()

    manual_ocr_btn = ttkb.Button(
        control_frame,
        text="🔍 手动触发OCR",
        command=manual_ocr_trigger,
        bootstyle="primary-outline",
    )
    manual_ocr_btn.pack(side=RIGHT, padx=(10, 0))

    # 测试警告音效按钮
    test_sound_btn = ttkb.Button(
        control_frame,
        text="🔊 测试警告音效",
        command=play_fish_bucket_warning_sound,
        bootstyle="warning-outline",
    )
    test_sound_btn.pack(side=RIGHT, padx=(10, 0))

    # 刷新按钮
    refresh_btn = ttkb.Button(
        control_frame,
        text="🔄 刷新",
        command=lambda: update_debug_info(),
        bootstyle="info-outline",
    )
    refresh_btn.pack(side=RIGHT, padx=(10, 0))

    # UNO相关按钮
    def uno_toggle_recognition():
        """切换UNO持续识别"""
        global uno_recognition_running
        if uno_recognition_running:
            uno_stop_continuous_recognition()
        else:
            uno_start_continuous_recognition()

    def uno_test_popup():
        """测试UNO弹窗"""
        uno_show_popup()

    uno_test_btn = ttkb.Button(
        control_frame,
        text="📝 测试UNO弹窗",
        command=uno_test_popup,
        bootstyle="info-outline",
    )
    uno_test_btn.pack(side=RIGHT, padx=(10, 0))

    # 测试放生操作按钮
    def test_release_fish():
        """测试放生操作"""
        print("🔍 手动触发放生操作")
        success = release_fish()
        if success:
            print("✅ 放生操作执行成功")
        else:
            print("❌ 放生操作执行失败")

    release_fish_btn = ttkb.Button(
        control_frame,
        text="🐟 测试放生操作",
        command=test_release_fish,
        bootstyle="success-outline",
    )
    release_fish_btn.pack(side=RIGHT, padx=(10, 0))

    # 调试模式开关
    debug_mode_var = ttkb.BooleanVar(value=debug_mode)
    debug_mode_check = ttkb.Checkbutton(
        control_frame, text="启用调试模式", variable=debug_mode_var, bootstyle="warning"
    )
    debug_mode_check.pack(side=RIGHT)

    def toggle_debug_mode():
        """切换调试模式"""
        global debug_mode
        debug_mode = debug_mode_var.get()

    debug_mode_check.configure(command=toggle_debug_mode)

    # 信息显示区域
    info_frame = ttkb.Frame(main_frame)
    info_frame.pack(fill=BOTH, expand=YES)

    # 滚动条
    scrollbar = ttkb.Scrollbar(info_frame, orient="vertical")
    scrollbar.pack(side=RIGHT, fill=Y)

    # 文本框
    debug_text = tk.Text(
        info_frame,
        wrap="word",
        font=("Consolas", 10),
        bg="#1e1e1e",
        fg="#d4d4d4",
        insertbackground="white",
        yscrollcommand=scrollbar.set,
    )
    debug_text.pack(fill=BOTH, expand=YES)
    scrollbar.configure(command=debug_text.yview)

    # 添加行号
    debug_text.tag_configure("line_number", foreground="#606060")
    debug_text.tag_configure("timestamp", foreground="#569cd6")
    debug_text.tag_configure("region", foreground="#4ec9b0")
    debug_text.tag_configure("ocr_result", foreground="#ce9178")
    debug_text.tag_configure("parsed_info", foreground="#dcdcaa")
    debug_text.tag_configure("error", foreground="#f48771")

    def update_debug_info():
        """更新调试信息显示"""
        debug_text.delete(1.0, END)

        # 显示调试模式状态
        if not debug_mode:
            debug_text.insert(END, "🔴 调试模式已关闭\n", "error")
            debug_text.insert(END, "请勾选'启用调试模式'以查看OCR调试信息\n")
            return

        # 获取屏幕分辨率信息
        max_width, max_height = get_max_screen_resolution()
        current_width, current_height = TARGET_WIDTH, TARGET_HEIGHT

        # 获取历史记录（线程安全）
        with debug_history_lock:
            # 复制当前历史记录，避免在迭代时被修改
            debug_info_list = list(debug_info_history)

        # 显示调试模式状态和历史记录信息
        debug_text.insert(END, "🟢 调试模式已启用\n", "timestamp")
        debug_text.insert(
            END, f"📊 历史记录: 当前共有 {len(debug_info_list)} 条调试信息\n"
        )
        debug_text.insert(
            END, f"🔄 自动刷新: {'开启' if debug_auto_refresh else '关闭'}\n"
        )
        debug_text.insert(END, "-" * 60 + "\n")

        # 显示信息统计
        debug_text.insert(
            END, f"📋 共显示 {len(debug_info_list)} 条调试信息\n", "timestamp"
        )
        debug_text.insert(END, "显示所有日志：\n")
        debug_text.insert(END, "-" * 60 + "\n")

        if not debug_info_list:
            debug_text.insert(END, "📭 暂无调试信息\n")
            debug_text.insert(END, "等待OCR识别...\n")
            debug_text.insert(END, "💡 提示: 点击'手动触发OCR'按钮可立即测试OCR识别\n")
            return

        # 显示所有信息
        for info in debug_info_list:
            timestamp = info.get("timestamp", "未知时间")
            region = info.get("region", {})
            ocr_result = info.get("ocr_result", [])
            parsed_info = info.get("parsed_info", {})
            error = info.get("error", None)
            action = info.get("action", "未知操作")
            message = info.get("message", None)
            elapse = info.get("elapse", None)
            image_shape = info.get("image_shape", None)
            result_count = info.get("result_count", None)
            has_text = info.get("has_text", None)
            exception_type = info.get("exception_type", None)
            full_text = info.get("full_text", None)

            # 显示时间戳和操作类型
            debug_text.insert(END, f"📅 {timestamp} | 🔧 {action}\n", "timestamp")

            # 显示自定义消息
            if message:
                debug_text.insert(END, f"💬 {message}\n")

            # 显示识别区域
            if region:
                x1, y1, x2, y2 = (
                    region.get("x1", 0),
                    region.get("y1", 0),
                    region.get("x2", 0),
                    region.get("y2", 0),
                )
                width, height = x2 - x1, y2 - y1
                debug_text.insert(
                    END,
                    f"📍 识别区域: ({x1}, {y1}) - ({x2}, {y2}) | 宽: {width}, 高: {height}\n",
                    "region",
                )

            # 显示图像信息
            if image_shape:
                debug_text.insert(END, f"🖼️ 图像尺寸: {image_shape}\n")

            # 显示识别耗时
            if elapse is not None and isinstance(elapse, (int, float)):
                debug_text.insert(END, f"⏱️ 识别耗时: {elapse:.3f}秒\n")

            # 显示识别结果统计
            if result_count is not None:
                debug_text.insert(
                    END,
                    f"📊 识别结果: {result_count} 行文本 | 包含有效文本: {'是' if has_text else '否'}\n",
                )

            # 显示完整识别文本
            if full_text:
                debug_text.insert(END, f"📝 完整识别文本: {full_text}\n")

            # 显示OCR原始结果
            if ocr_result:
                debug_text.insert(END, "📋 OCR原始结果 (包含置信度):\n", "ocr_result")
                for i, line in enumerate(ocr_result):
                    if isinstance(line, list) and len(line) >= 2:
                        text = line[1]
                        confidence = line[2] if len(line) > 2 else 0
                        # 确保置信度是数字类型
                        if isinstance(confidence, (int, float)):
                            debug_text.insert(
                                END, f"   [{i+1}] {text} (置信度: {confidence:.2f})\n"
                            )
                        else:
                            debug_text.insert(
                                END, f"   [{i+1}] {text} (置信度: {confidence})\n"
                            )
                    else:
                        debug_text.insert(END, f"   [{i+1}] {line}\n")
            else:
                debug_text.insert(END, "📋 OCR原始结果: 无\n", "ocr_result")

            # 显示解析后的信息
            if parsed_info:
                debug_text.insert(END, "🔍 解析结果:\n", "parsed_info")
                for key, value in parsed_info.items():
                    debug_text.insert(END, f"   {key}: {value}\n")

            # 显示错误信息
            if error:
                error_line = f"❌ 错误: {error}\n"
                if exception_type:
                    error_line += f"   异常类型: {exception_type}\n"
                debug_text.insert(END, error_line, "error")

            debug_text.insert(END, "-" * 60 + "\n")

        # 滚动到底部
        debug_text.see(END)

    # 定时更新
    after_id = None

    def schedule_update():
        """定时更新调试信息"""
        global after_id
        if (
            debug_auto_refresh
            and debug_window is not None
            and debug_window.winfo_exists()
        ):
            update_debug_info()
            after_id = debug_window.after(
                1000, schedule_update
            )  # 每秒更新一次，保存after ID

    schedule_update()

    # 窗口关闭时的清理
    def on_close():
        """窗口关闭事件处理"""
        global debug_window, after_id
        if debug_window is not None:
            # 先停止定时更新
            if after_id is not None:
                debug_window.after_cancel(after_id)
                after_id = None
            # 销毁窗口
            debug_window.destroy()
            debug_window = None

    debug_window.protocol("WM_DELETE_WINDOW", on_close)

    # 初始更新
    update_debug_info()

    return debug_window


# =========================
# 运行日志界面功能
# =========================
def update_log_display(log_text_widget, auto_scroll=True):
    """更新运行日志显示"""
    # 从队列中获取所有新的日志条目
    log_entries = []
    while not log_queue.empty():
        try:
            log_entries.append(log_queue.get_nowait())
        except queue.Empty:
            break

    # 如果有新的日志条目，添加到文本框中
    if log_entries:
        # 保存当前滚动位置
        scroll_position = log_text_widget.yview()

        # 启用文本框编辑
        log_text_widget.config(state="normal")

        # 添加新的日志条目
        for entry in log_entries:
            # 根据日志类型添加不同的颜色标记
            # 注意：先检查具体的类型，最后检查一般类型
            if "❌" in entry and ("[错误]" in entry or "错误" in entry):
                log_text_widget.insert("end", entry + "\n", "error")
            elif "⚠️" in entry and ("[警告]" in entry or "警告" in entry):
                log_text_widget.insert("end", entry + "\n", "warning")
            elif "💾" in entry or (
                "[保存]" in entry and "❌" not in entry
            ):  # 排除包含❌的保存信息
                log_text_widget.insert("end", entry + "\n", "save")
            elif "✅" in entry or "[初始化]" in entry:
                log_text_widget.insert("end", entry + "\n", "init")
            elif "▶️" in entry or "⏸️" in entry or "[状态]" in entry:
                log_text_widget.insert("end", entry + "\n", "status")
            elif "🐟" in entry or "[钓到]" in entry:
                log_text_widget.insert("end", entry + "\n", "fish")
            elif "🖼️" in entry or "[模板]" in entry:
                log_text_widget.insert("end", entry + "\n", "template")
            elif "⏱️" in entry or "[时间]" in entry:
                log_text_widget.insert("end", entry + "\n", "time")
            elif "📸" in entry or "[截屏]" in entry:
                log_text_widget.insert("end", entry + "\n", "screenshot")
            elif "🎣" in entry or "[提示]" in entry:
                log_text_widget.insert("end", entry + "\n", "hint")
            elif "📌" in entry or "[调试]" in entry:
                log_text_widget.insert("end", entry + "\n", "debug")
            elif "📊" in entry or "[会话]" in entry:
                log_text_widget.insert("end", entry + "\n", "session")
            elif "🔍" in entry or "[OCR]" in entry:
                log_text_widget.insert("end", entry + "\n", "ocr")
            elif "📄" in entry or "[信息]" in entry:
                log_text_widget.insert("end", entry + "\n", "info")
            elif "❌" in entry:  # 单独的❌匹配，放在最后
                log_text_widget.insert("end", entry + "\n", "error")
            elif "⚠️" in entry:  # 单独的⚠️匹配，放在最后
                log_text_widget.insert("end", entry + "\n", "warning")
            else:
                log_text_widget.insert("end", entry + "\n")

        # 限制日志行数，防止内存过大
        line_count = int(log_text_widget.index("end-1c").split(".")[0])
        if line_count > 1000:
            # 删除前500行
            log_text_widget.delete("1.0", "500.0")

        # 如果开启了自动滚动，滚动到底部
        if auto_scroll:
            log_text_widget.see("end")
        # 否则保持原来的滚动位置
        elif scroll_position[1] < 1.0:  # 如果不是在底部
            log_text_widget.yview_moveto(scroll_position[0])

        # 禁用文本框编辑（只读）
        log_text_widget.config(state="disabled")

        # 恢复滚动位置
        if scroll_position == 0:  # 如果之前就在顶部，保持在顶部
            log_text_widget.yview_moveto(0)


# =========================
# 创建 Tkinter 窗口（现代化UI设计 - 左右分栏布局）
# =========================
def create_gui():
    # 加载保存的参数
    load_parameters()
    # 声明全局变量
    global uno_input1_var, uno_input2_var, uno_popup_shown, root

    # 创建现代化主题窗口
    root = ttkb.Window(themename="darkly")  # 使用深色主题
    root.title("🎣 PartyFish 自动钓鱼助手")
    root.geometry("1110x1000")  # 增大窗口高度，为运行日志留出空间
    root.minsize(840, 650)  # 调整最小尺寸，确保运行日志区域可见
    root.maxsize(2560, 1600)  # 调整最大尺寸，支持更大的显示器
    root.resizable(True, True)  # 允许调整大小

    # 设置窗口图标（如果有的话）
    set_window_icon(root)

    # 响应式布局：窗口大小变化时调整布局
    def on_window_resize(event):
        """窗口大小变化时调整布局"""
        # 调整钓鱼记录表格列宽
        if fish_tree_ref:
            # 获取当前主窗口宽度
            window_width = root.winfo_width()

            # 计算右侧面板的可用宽度（假设左侧面板宽度为250px，加上间距8px）
            available_width = max(window_width - 200, 400)  # 最小400px

            # 调整比例，时间列与名称/重量列相同（时间:名称:品质:重量 = 63:63:36:63）
            time_ratio = 63  # 时间列比例改为63，与名称/重量列一致
            name_ratio = 63
            quality_ratio = 36
            weight_ratio = 63
            total_ratio = time_ratio + name_ratio + quality_ratio + weight_ratio

            # 计算Treeview容器的可用宽度，完全跟随窗口变化
            tree_container_width = available_width - 30  # 减去滚动条和边距

            # 严格按照比例计算各列宽度，真正实现响应式
            time_width = int(tree_container_width * (time_ratio / total_ratio))
            name_width = int(tree_container_width * (name_ratio / total_ratio))
            quality_width = int(tree_container_width * (quality_ratio / total_ratio))
            weight_width = int(
                tree_container_width - time_width - name_width - quality_width - 4
            )  # 减去4个像素的边框间距

            # 设置合理的最小宽度，确保内容能正常显示
            time_width = max(time_width, 100)  # 时间列最小宽度
            name_width = max(name_width, 60)  # 名称列最小宽度
            quality_width = max(quality_width, 35)  # 品质列最小宽度
            weight_width = max(weight_width, 60)  # 重量列最小宽度

            # 应用新列宽
            fish_tree_ref.column("时间", width=time_width, anchor="center")
            fish_tree_ref.column("名称", width=name_width, anchor="center")
            fish_tree_ref.column("品质", width=quality_width, anchor="center")
            fish_tree_ref.column("重量", width=weight_width, anchor="center")

    # 绑定窗口大小变化事件
    root.bind("<Configure>", on_window_resize)

    # ==================== 主容器（固定布局，左右分栏） ====================
    main_frame = ttkb.Frame(root, padding=12)
    main_frame.pack(fill=BOTH, expand=YES)

    # 配置主框架的行列权重
    main_frame.columnconfigure(0, weight=0)  # 左侧面板固定宽度
    main_frame.columnconfigure(1, weight=1)  # 右侧面板自适应扩展
    main_frame.rowconfigure(0, weight=1)  # 内容区域自适应高度

    # ==================== 左侧面板（设置区域） ====================
    left_panel = ttkb.Frame(main_frame, width=100)  # 设置左侧面板固定宽度
    left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
    left_panel.grid_propagate(False)  # 允许面板内容改变宽度

    # ==================== 固定标题区域 ====================
    # 标题区域固定，不随滚动条滚动
    title_frame = ttkb.Frame(left_panel)
    title_frame.pack(fill=X, pady=(12, 8))

    title_label = ttkb.Label(
        title_frame,
        text="🎣 PartyFish",
        font=("Segoe UI", 16, "bold"),
        bootstyle="primary",
    )
    title_label.pack()

    subtitle_label = ttkb.Label(
        title_frame, text="自动钓鱼助手", font=("Segoe UI", 10), bootstyle="secondary"
    )
    subtitle_label.pack(pady=(2, 0))

    # 添加分隔线
    separator = ttkb.Separator(left_panel, bootstyle="secondary")
    separator.pack(fill=X, pady=(0, 8))

    # ==================== 垂直滚动条 ====================
    # 先添加垂直滚动条，确保它从顶部到底部，和左侧面板一样长
    left_scrollbar = ttkb.Scrollbar(
        left_panel, orient="vertical", bootstyle="secondary"
    )
    left_scrollbar.pack(side=RIGHT, fill=Y, pady=(0, 12))

    # ==================== 可滚动内容区域 ====================
    # 创建滚动容器，用于放置可滚动的内容
    scrollable_content_frame = ttkb.Frame(left_panel, width=300)  # 180 - 24 (左右边距)
    scrollable_content_frame.pack(fill=BOTH, expand=YES, padx=12, pady=(0, 12))
    scrollable_content_frame.pack_propagate(False)  # 防止内容改变框架宽度

    # 创建Canvas作为滚动区域
    left_canvas = tk.Canvas(
        scrollable_content_frame,
        yscrollcommand=left_scrollbar.set,
        background="#212529",  # 深色主题背景色，与ttkbootstrap darkly主题匹配
        highlightthickness=0,  # 去除Canvas的高亮边框
        relief="flat",  # 平边框样式
        width=156,  # 180 - 24 (左右边距)
    )
    left_canvas.pack(side=LEFT, fill=BOTH, expand=YES)

    # 配置滚动条与Canvas关联，使用标准的yview方法，它可以正确处理所有滚动条事件
    left_scrollbar.config(command=left_canvas.yview)

    # 创建内部框架，用于放置所有可滚动的左侧面板内容
    # 设置与Canvas相同的背景色，避免滚动时出现拖影
    left_content_frame = ttkb.Frame(left_canvas, bootstyle="dark")

    # 保存canvas window的ID，用于后续调整宽度
    canvas_window = left_canvas.create_window(
        (0, 0), window=left_content_frame, anchor="nw", tags="content_window"
    )

    # 优化滚动性能，减少拖影
    def smooth_scroll(event):
        # 使用更平滑的滚动增量
        left_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        # 强制Canvas重绘，避免拖影
        left_canvas.update_idletasks()

    # 修复鼠标滚轮绑定，确保所有组件都能响应鼠标滚轮
    # 先解绑所有现有的鼠标滚轮绑定，避免冲突
    left_canvas.unbind("<MouseWheel>")
    left_content_frame.unbind("<MouseWheel>")

    # 绑定鼠标滚轮事件到Canvas和内容框架
    left_canvas.bind("<MouseWheel>", smooth_scroll)
    left_content_frame.bind("<MouseWheel>", smooth_scroll)

    # 为内容框架中的所有子组件绑定鼠标滚轮事件
    # 定义一个递归函数，为所有子组件绑定事件
    def bind_mousewheel_recursively(widget):
        # 跳过已经绑定过的组件，避免重复绑定
        if hasattr(widget, "_mousewheel_bound") and widget._mousewheel_bound:
            return

        # 绑定鼠标滚轮事件
        widget.bind("<MouseWheel>", smooth_scroll)
        widget._mousewheel_bound = True

        # 递归绑定所有子组件
        for child in widget.winfo_children():
            bind_mousewheel_recursively(child)

    # 绑定内容框架的子组件
    bind_mousewheel_recursively(left_content_frame)

    # 为新添加的组件自动绑定鼠标滚轮事件
    def on_content_frame_child_added(event):
        bind_mousewheel_recursively(event.widget)

    left_content_frame.bind("<Map>", on_content_frame_child_added)

    # 绑定canvas的Configure事件，确保内容框架宽度与canvas一致
    def on_canvas_configure(event):
        # 调整canvas的宽度，确保内容框架与canvas宽度一致
        left_canvas.itemconfig(canvas_window, width=event.width)

    left_canvas.bind("<Configure>", on_canvas_configure)

    # 更新滚动区域大小
    def update_scroll_region(event):
        # 强制更新布局
        left_content_frame.update_idletasks()
        # 设置滚动区域，确保包含整个内容
        left_canvas.config(scrollregion=left_canvas.bbox("all"))

    # 绑定内容框架的Configure事件，更新滚动区域
    left_content_frame.bind("<Configure>", update_scroll_region)

    # ==================== 配置管理 ====================
    config_frame = ttkb.Frame(left_content_frame)
    config_frame.pack(fill=X, pady=(0, 4))

    # 配置按钮列表
    config_buttons = []
    # 配置输入框列表（用于重命名）
    config_entries = []

    # 当前配置索引变量（用于闭包）
    config_index_var = [0]

    # 配置网格布局，4列均匀分布
    for i in range(MAX_CONFIGS):
        config_frame.columnconfigure(i, weight=1, uniform="config")
    config_frame.rowconfigure(0, weight=1)

    def update_config_buttons():
        """更新配置按钮的样式，高亮当前配置"""
        for i, btn in enumerate(config_buttons):
            if i == current_config_index:
                btn.configure(bootstyle="success")  # 当前配置使用填充样式
            else:
                btn.configure(bootstyle="success-outline")  # 其他配置使用轮廓样式

    def on_config_click(index):
        """配置按钮点击事件"""
        # 保存当前参数到变量
        t_var.set(str(t))
        leftclickdown_var.set(str(leftclickdown))
        leftclickup_var.set(str(leftclickup))
        times_var.set(str(times))
        paogantime_var.set(str(paogantime))

        # 切换配置
        if switch_config(index):
            # 更新输入框显示
            t_var.set(str(t))
            leftclickdown_var.set(str(leftclickdown))
            leftclickup_var.set(str(leftclickup))
            times_var.set(str(times))
            paogantime_var.set(str(paogantime))

            # 更新按钮样式
            update_config_buttons()

    def on_rename_config(index):
        """开始重命名配置"""
        # 确保所有其他输入框都已关闭
        for idx in range(MAX_CONFIGS):
            if idx != index and config_entries[idx].winfo_ismapped():
                config_entries[idx].grid_remove()
                config_buttons[idx].grid()

        # 隐藏按钮，显示输入框
        config_buttons[index].grid_remove()

        # 设置输入框的值并显示
        config_entries[index].delete(0, tk.END)
        config_entries[index].insert(0, config_names[index])
        config_entries[index].grid(row=0, column=index, padx=2, sticky="ew")

        # 自动选中所有文本并获得焦点
        config_entries[index].select_range(0, tk.END)
        config_entries[index].focus_set()

    def save_config_name(index, event=None):
        """保存配置名称"""
        # 确保是当前编辑的输入框
        if not config_entries[index].winfo_ismapped():
            return

        new_name = config_entries[index].get().strip()
        if new_name and new_name != config_names[index]:
            rename_config(index, new_name)
            config_buttons[index].configure(text=new_name)

        # 隐藏输入框，显示按钮
        config_entries[index].grid_remove()
        config_buttons[index].grid(row=0, column=index, padx=2, sticky="ew")

    def cancel_rename(index, event=None):
        """取消重命名配置"""
        # 确保是当前编辑的输入框
        if not config_entries[index].winfo_ismapped():
            return

        # 隐藏输入框，显示按钮
        config_entries[index].grid_remove()
        config_buttons[index].grid(row=0, column=index, padx=2, sticky="ew")

    # 创建4个配置按钮和对应的输入框
    for i in range(MAX_CONFIGS):
        # 使用默认参数保存当前索引值，避免闭包问题
        current_idx = i

        # 创建按钮
        btn = ttkb.Button(
            config_frame,
            text=config_names[i],
            bootstyle="success-outline",
            width=0,  # 宽度0，让按钮自动扩展
            command=lambda idx=current_idx: on_config_click(idx),
        )
        # 使用grid布局，固定列位置，水平扩展
        btn.grid(row=0, column=i, padx=2, sticky="ew")
        config_buttons.append(btn)

        # 创建对应的输入框（初始隐藏）
        entry = ttkb.Entry(
            config_frame, width=0, justify=tk.CENTER  # 宽度0，让输入框自动扩展
        )

        # 绑定回车保存
        def on_entry_return(idx):
            def handler(event):
                save_config_name(idx, event)

            return handler

        entry.bind("<Return>", on_entry_return(current_idx))

        # 绑定ESC取消
        def on_entry_escape(idx):
            def handler(event):
                cancel_rename(idx, event)

            return handler

        entry.bind("<Escape>", on_entry_escape(current_idx))

        # 绑定失去焦点保存
        def on_entry_focusout(idx):
            def handler(event):
                save_config_name(idx, event)

            return handler

        entry.bind("<FocusOut>", on_entry_focusout(current_idx))

        # 绑定右键点击保存配置名称
        def on_entry_right_click(idx):
            def handler(event):
                save_config_name(idx, event)

            return handler

        entry.bind("<Button-3>", on_entry_right_click(current_idx))

        # 初始隐藏输入框
        entry.grid(row=0, column=i, padx=2, sticky="ew")
        entry.grid_remove()
        config_entries.append(entry)

        # 绑定右击事件用于重命名
        def on_button_right_click(idx):
            def handler(event):
                on_rename_config(idx)

            return handler

        btn.bind("<Button-3>", on_button_right_click(current_idx))

    # 初始更新按钮样式
    update_config_buttons()

    # 添加右键修改提示
    tip_label = ttkb.Label(
        config_frame,
        text="可右键点击修改名字",
        font=("Segoe UI", 8),
        bootstyle="info",
        anchor="center",
    )
    tip_label.grid(row=1, column=0, columnspan=4, pady=(2, 0), sticky="ew")

    # ==================== 钓鱼参数卡片 ====================
    params_card = ttkb.Labelframe(
        left_content_frame, text=" ⚙️ 钓鱼参数 ", padding=12, bootstyle="info"
    )
    params_card.pack(fill=X, pady=(0, 8))

    # 参数输入样式 - 优化布局和样式
    def create_param_row(parent, label_text, var, row, tooltip=""):
        # 使用更紧凑的布局
        label = ttkb.Label(
            parent, text=label_text, font=("Segoe UI", 9), bootstyle="info"
        )
        label.grid(row=row, column=0, sticky=W, pady=4, padx=(0, 8))

        entry = ttkb.Entry(parent, textvariable=var, width=12, font=("Segoe UI", 9))
        entry.grid(row=row, column=1, sticky=E, pady=4)

        # 保存输入框引用到全局列表
        input_entries.append(entry)

        return entry

    # 配置列宽 - 更合理的比例
    params_card.columnconfigure(0, weight=1, minsize=180)
    params_card.columnconfigure(1, weight=0, minsize=60)

    # 循环间隔
    t_var = ttkb.StringVar(value=str(t))
    create_param_row(params_card, "循环间隔 (秒)", t_var, 0)

    # 收线时间
    leftclickdown_var = ttkb.StringVar(value=str(leftclickdown))
    create_param_row(params_card, "收线时间 (秒)", leftclickdown_var, 1)

    # 放线时间
    leftclickup_var = ttkb.StringVar(value=str(leftclickup))
    create_param_row(params_card, "放线时间 (秒)", leftclickup_var, 2)

    # 最大拉线次数
    times_var = ttkb.StringVar(value=str(times))
    create_param_row(params_card, "最大拉杆次数", times_var, 3)

    # 抛竿时间
    paogantime_var = ttkb.StringVar(value=str(paogantime))
    create_param_row(params_card, "抛竿时间 (秒)", paogantime_var, 4)

    # ==================== 加时选项卡片 ====================
    jiashi_card = ttkb.Labelframe(
        left_content_frame, text=" ⏱️ 加时选项 ", padding=12, bootstyle="warning"
    )
    jiashi_card.pack(fill=X, pady=(0, 8))

    jiashi_var_option = ttkb.IntVar(value=jiashi_var)

    jiashi_frame = ttkb.Frame(jiashi_card)
    jiashi_frame.pack(fill=X, pady=4)

    jiashi_label = ttkb.Label(
        jiashi_frame, text="是否自动加时", font=("Segoe UI", 9), bootstyle="warning"
    )
    jiashi_label.pack(side=LEFT, padx=4)

    jiashi_btn_frame = ttkb.Frame(jiashi_frame)
    jiashi_btn_frame.pack(side=RIGHT, padx=4)

    jiashi_yes = ttkb.Radiobutton(
        jiashi_btn_frame,
        text="是",
        variable=jiashi_var_option,
        value=1,
        bootstyle="success-outline-toolbutton",
    )
    jiashi_yes.pack(side=LEFT, padx=5)

    jiashi_no = ttkb.Radiobutton(
        jiashi_btn_frame,
        text="否",
        variable=jiashi_var_option,
        value=0,
        bootstyle="danger-outline-toolbutton",
    )
    jiashi_no.pack(side=LEFT, padx=5)

    # ==================== 时间抖动设置卡片 ====================
    jitter_card = ttkb.Labelframe(
        left_content_frame, text=" 🎲 时间抖动设置 ", padding=8, bootstyle="warning"
    )
    jitter_card.pack(fill=X, pady=(0, 8))

    # 时间抖动变量
    jitter_var = ttkb.IntVar(value=JITTER_RANGE)

    # 创建水平布局框架
    jitter_frame = ttkb.Frame(jitter_card)
    jitter_frame.pack(fill=X)

    # 时间抖动范围标签
    jitter_label = ttkb.Label(
        jitter_frame,
        text="时间抖动范围 (±%):",
        bootstyle="warning",
        font=("Segoe UI", 9),
    )
    jitter_label.pack(side=LEFT, padx=(0, 4))

    # 时间抖动滑块
    jitter_slider = ttkb.Scale(
        jitter_frame,
        from_=0,
        to=30,
        orient="horizontal",
        variable=jitter_var,
        bootstyle="warning",
        length=80,
        cursor="hand2",
    )
    jitter_slider.pack(side=LEFT, padx=4, fill=X, expand=True)

    # 时间抖动数值显示 - 更醒目的样式
    jitter_value_label = ttkb.Label(
        jitter_frame,
        text=f"{jitter_var.get()}%",
        bootstyle="warning",
        font=("Segoe UI", 10, "bold"),
    )
    jitter_value_label.pack(side=LEFT, padx=(0, 2))

    # 时间抖动说明文字 - 优化样式
    jitter_info_label = ttkb.Label(
        jitter_card,
        text="随机波动避免检测",
        bootstyle="info",
        font=("Segoe UI", 8),
    )
    jitter_info_label.pack(pady=(4, 2), padx=2)

    # 时间抖动滑块变化事件处理
    def on_jitter_change(*args):
        update_parameters(
            t_var,
            leftclickdown_var,
            leftclickup_var,
            times_var,
            paogantime_var,
            jiashi_var_option,
            resolution_var,
            custom_width_var,
            custom_height_var,
            hotkey_var,
            record_fish_var,
            legendary_screenshot_var,
            first_capture_screenshot_var,
            jitter_var=jitter_var,
        )
        jitter_value_label.configure(text=f"{jitter_var.get()}%")

    # 滑块命令事件
    jitter_slider.configure(command=on_jitter_change)

    # 变量跟踪事件（确保键盘操作也能更新显示）
    jitter_var.trace(
        "w", lambda *args: jitter_value_label.configure(text=f"{jitter_var.get()}%")
    )
    # ==================== 鱼饵识别算法设置卡片 ====================
    bait_algorithm_card = ttkb.Labelframe(
        left_content_frame,
        text=" 🎯 鱼饵识别算法 ",
        padding=12,
        bootstyle="primary",
    )
    bait_algorithm_card.pack(fill=X, pady=(0, 8))

    # 鱼饵识别算法变量
    bait_algorithm_var = ttkb.StringVar(value=bait_recognition_algorithm)

    # 创建算法选择水平框架
    algorithm_frame = ttkb.Frame(bait_algorithm_card)
    algorithm_frame.pack(fill=X, pady=4)

    # 算法选择标签
    algorithm_label = ttkb.Label(
        algorithm_frame,
        text="识别算法:",
        bootstyle="primary",
        font=("Segoe UI", 9),
    )
    algorithm_label.pack(side=LEFT, padx=(0, 8))

    # 算法选择下拉框
    # 设置当前算法的中文名称
    current_algorithm_name = bait_recognition_algorithms[bait_recognition_algorithm]

    algorithm_combo = ttkb.Combobox(
        algorithm_frame,
        textvariable=bait_algorithm_var,
        values=list(bait_recognition_algorithms.values()),
        state="readonly",
        font=(("Segoe UI", 9)),
        width=15,
    )
    # 初始化为当前算法的中文名称
    bait_algorithm_var.set(current_algorithm_name)
    algorithm_combo.pack(side=LEFT, padx=(0, 8))

    # 算法说明标签
    algorithm_desc_label = ttkb.Label(
        algorithm_frame,
        text=bait_recognition_algorithms[bait_recognition_algorithm],
        bootstyle="info",
        font=("Segoe UI", 9),
    )
    algorithm_desc_label.pack(side=LEFT, padx=(0, 8))

    # 算法选择变化事件处理
    def on_algorithm_change(event=None):
        """切换鱼饵识别算法"""
        global bait_recognition_algorithm
        selected_algorithm_name = bait_algorithm_var.get()
        # 创建反向映射字典：中文名称 -> 英文键名
        algorithm_name_to_key = {v: k for k, v in bait_recognition_algorithms.items()}
        # 根据中文名称获取对应的英文键名
        selected_algorithm_key = algorithm_name_to_key[selected_algorithm_name]

        if selected_algorithm_key != bait_recognition_algorithm:
            bait_recognition_algorithm = selected_algorithm_key
            # 保存设置
            save_parameters()
            print(
                f"⚙️  [配置] 鱼饵识别算法已切换为: {selected_algorithm_key} ({selected_algorithm_name})"
            )

    # 绑定算法选择变化事件
    algorithm_combo.bind("<<ComboboxSelected>>", on_algorithm_change)
    # ==================== 鱼桶满检测设置卡片 ====================
    bucket_card = ttkb.Labelframe(
        left_content_frame,
        text=" 🪣 鱼桶满/没鱼饵检测 ",
        padding=12,
        bootstyle="warning",
    )
    bucket_card.pack(fill=X, pady=(0, 8))

    # 音效开关
    global fish_bucket_sound_enabled
    fish_bucket_sound_var = ttkb.BooleanVar(value=fish_bucket_sound_enabled)

    # 创建音效开关水平框架
    sound_frame = ttkb.Frame(bucket_card)
    sound_frame.pack(fill=X, pady=(0, 4))

    # 音效开关标签
    sound_label = ttkb.Label(
        sound_frame, text="启用警告音效", bootstyle="warning", font=("Segoe UI", 9)
    )
    sound_label.pack(side=LEFT, padx=(0, 5), pady=0)

    # 创建一个框架来容纳单选按钮，并将其靠右显示
    sound_rb_frame = ttkb.Frame(sound_frame)
    sound_rb_frame.pack(side=RIGHT, padx=0, pady=0)

    # "是"单选按钮
    sound_yes = ttkb.Radiobutton(
        sound_rb_frame,
        text="是",
        variable=fish_bucket_sound_var,
        value=True,
        bootstyle="success-outline-toolbutton",
        cursor="hand2",
    )
    sound_yes.pack(side=LEFT, padx=3)

    # "否"单选按钮
    sound_no = ttkb.Radiobutton(
        sound_rb_frame,
        text="否",
        variable=fish_bucket_sound_var,
        value=False,
        bootstyle="danger-outline-toolbutton",
        cursor="hand2",
    )
    sound_no.pack(side=LEFT, padx=3)

    def toggle_fish_bucket_sound():
        """切换鱼桶满了/没鱼饵警告音效开关"""
        global fish_bucket_sound_enabled
        fish_bucket_sound_enabled = fish_bucket_sound_var.get()
        # 保存设置
        save_parameters()

    # 绑定单选按钮事件
    sound_yes.configure(command=toggle_fish_bucket_sound)
    sound_no.configure(command=toggle_fish_bucket_sound)

    # 运行模式选择
    global bucket_detection_mode
    bucket_mode_var = ttkb.StringVar(value=bucket_detection_mode)

    mode_frame = ttkb.Frame(bucket_card)
    mode_frame.pack(fill=X, pady=(8, 0))

    ttkb.Label(
        mode_frame, text="运行模式:", bootstyle="warning", font=("Segoe UI", 9, "bold")
    ).pack(anchor=CENTER, pady=(0, 4))

    # 创建按钮组容器
    rb_frame = ttkb.Frame(mode_frame, padding=2)
    rb_frame.pack(fill=X, pady=(0, 4))

    # 创建按钮式单选按钮组
    mode1_rb = ttkb.Radiobutton(
        rb_frame,
        text="1.自动暂停",
        variable=bucket_mode_var,
        value="mode1",
        bootstyle="primary toolbutton",
        cursor="hand2",
    )
    mode1_rb.pack(fill=X, pady=1, padx=2)

    mode2_rb = ttkb.Radiobutton(
        rb_frame,
        text="2.自动挂机",
        variable=bucket_mode_var,
        value="mode2",
        bootstyle="primary toolbutton",
        cursor="hand2",
    )
    mode2_rb.pack(fill=X, pady=1, padx=2)

    mode3_rb = ttkb.Radiobutton(
        rb_frame,
        text="3.收杆模式",
        variable=bucket_mode_var,
        value="mode3",
        bootstyle="primary toolbutton",
        cursor="hand2",
    )
    mode3_rb.pack(fill=X, pady=1, padx=2)

    def on_bucket_mode_change():
        """切换鱼桶满检测模式"""
        global bucket_detection_mode
        bucket_detection_mode = bucket_mode_var.get()
        # 保存设置
        save_parameters()

    # 绑定模式变化事件
    bucket_mode_var.trace_add("write", lambda *args: on_bucket_mode_change())

    # 说明文字
    info_label = ttkb.Label(
        bucket_card, text="按照选择的模式执行", bootstyle="info", font=("Segoe UI", 8)
    )
    info_label.pack(anchor=CENTER, pady=(4, 0))
    # ==================== 热键设置卡片 ====================
    hotkey_card = ttkb.Labelframe(
        left_content_frame, text=" ⌨️ 热键设置 ", padding=12, bootstyle="primary"
    )
    hotkey_card.pack(fill=X, pady=(0, 8))

    # 热键显示变量
    hotkey_var = ttkb.StringVar(value=hotkey_name)

    # 热键捕获状态
    is_capturing_hotkey = [False]  # 使用列表以便在闭包中修改
    captured_modifiers = [set()]
    captured_main_key = [None]
    captured_main_key_name = [""]
    capture_listener = [None]

    hotkey_frame = ttkb.Frame(hotkey_card)
    hotkey_frame.pack(fill=X, pady=4)

    hotkey_label = ttkb.Label(
        hotkey_frame,
        text="启动/暂停热键",
        font=("Segoe UI", 9, "bold"),
        bootstyle="primary",
    )
    hotkey_label.pack(side=LEFT, padx=(0, 8))

    # 热键显示按钮（点击后进入捕获模式）
    hotkey_btn = ttkb.Button(
        hotkey_frame, text=hotkey_name, bootstyle="primary", width=12
    )
    hotkey_btn.pack(side=RIGHT, padx=(8, 0))

    # 热键信息提示（合并显示，点击按钮时会变化）
    hotkey_info_label = ttkb.Label(
        hotkey_card,
        text=f"按 {hotkey_name} 启动/暂停 | 点击按钮修改",
        bootstyle="primary",
        font=("Segoe UI", 8, "bold"),
    )
    hotkey_info_label.pack(pady=(4, 0), padx=4)

    # 提示标签（用于捕获模式显示）
    hotkey_tip_label = ttkb.Label(
        hotkey_card, text="", bootstyle="secondary", font=("Segoe UI", 8)
    )

    def stop_hotkey_capture():
        """停止热键捕获"""
        is_capturing_hotkey[0] = False
        # 停止键盘监听器
        if capture_listener[0] is not None:
            try:
                capture_listener[0].stop()
            except:
                pass
            capture_listener[0] = None
        # 停止鼠标监听器
        if "mouse_capture_listener" in globals():
            mouse_listener = globals()["mouse_capture_listener"]
            if mouse_listener is not None:
                try:
                    mouse_listener.stop()
                except:
                    pass
            globals()["mouse_capture_listener"] = None
        hotkey_btn.configure(bootstyle="info-outline")
        hotkey_tip_label.pack_forget()  # 隐藏提示
        hotkey_info_label.configure(
            text=f"按 {hotkey_var.get()} 启动/暂停 | 点击按钮修改"
        )

    def on_capture_key_press(key):
        """捕获按键按下事件"""
        if not is_capturing_hotkey[0]:
            return False  # 停止监听

        # 检查是否是修饰键
        if key in MODIFIER_KEYS:
            captured_modifiers[0].add(MODIFIER_KEYS[key])
            # 更新按钮显示
            display_parts = []
            if "ctrl" in captured_modifiers[0]:
                display_parts.append("Ctrl")
            if "alt" in captured_modifiers[0]:
                display_parts.append("Alt")
            if "shift" in captured_modifiers[0]:
                display_parts.append("Shift")
            display_parts.append("...")
            root.after(0, lambda: hotkey_btn.configure(text="+".join(display_parts)))
            return True

        # 这是主按键
        captured_main_key[0] = key
        captured_main_key_name[0] = key_to_name(key)

        # 生成热键字符串
        new_hotkey = format_hotkey_display(
            captured_modifiers[0], captured_main_key_name[0]
        )

        # 更新GUI
        def update_gui():
            hotkey_var.set(new_hotkey)
            hotkey_btn.configure(text=new_hotkey)
            hotkey_info_label.configure(text=f"新热键: {new_hotkey} | 点击保存生效")
            stop_hotkey_capture()

        root.after(0, update_gui)
        return False  # 停止监听

    def on_capture_key_release(key):
        """捕获按键释放事件"""
        if not is_capturing_hotkey[0]:
            return False
        # 释放修饰键时移除
        if key in MODIFIER_KEYS:
            captured_modifiers[0].discard(MODIFIER_KEYS[key])
        return True

    def on_capture_mouse_click(x, y, button, pressed):
        """捕获鼠标点击事件"""
        if not is_capturing_hotkey[0] or not pressed:
            return

        # 只允许鼠标侧键（x1, x2），禁用左右中键
        if button not in [mouse.Button.x1, mouse.Button.x2]:
            return

        # 鼠标侧键作为主按键
        captured_main_key[0] = button
        captured_main_key_name[0] = key_to_name(button)

        # 生成热键字符串
        new_hotkey = format_hotkey_display(
            captured_modifiers[0], captured_main_key_name[0]
        )

        # 更新GUI
        def update_gui():
            hotkey_var.set(new_hotkey)
            hotkey_btn.configure(text=new_hotkey)
            hotkey_info_label.configure(text=f"新热键: {new_hotkey} | 点击保存生效")
            stop_hotkey_capture()

        root.after(0, update_gui)

    def start_hotkey_capture():
        """开始热键捕获"""
        if is_capturing_hotkey[0]:
            stop_hotkey_capture()
            return

        is_capturing_hotkey[0] = True
        captured_modifiers[0] = set()
        captured_main_key[0] = None
        captured_main_key_name[0] = ""

        hotkey_btn.configure(text="请按键...", bootstyle="warning")
        hotkey_info_label.configure(text="按下组合键（如Ctrl+F2）或单键/鼠标侧键")
        hotkey_tip_label.configure(text="5秒内按键，或再次点击取消")
        hotkey_tip_label.pack(pady=(2, 0))  # 显示提示

        # 启动键盘监听器，设置suppress=False允许事件传递
        capture_listener[0] = keyboard.Listener(
            on_press=on_capture_key_press,
            on_release=on_capture_key_release,
            suppress=False,
        )
        capture_listener[0].start()

        # 启动鼠标监听器
        global mouse_capture_listener
        mouse_capture_listener = mouse.Listener(on_click=on_capture_mouse_click)
        mouse_capture_listener.daemon = True
        mouse_capture_listener.start()

        # 5秒后自动取消
        def auto_cancel():
            if is_capturing_hotkey[0]:
                root.after(0, lambda: hotkey_btn.configure(text=hotkey_var.get()))
                stop_hotkey_capture()

        root.after(5000, auto_cancel)

    hotkey_btn.configure(command=start_hotkey_capture)

    # ==================== 分辨率设置卡片 ====================
    resolution_card = ttkb.Labelframe(
        left_content_frame, text=" 🖥️ 分辨率设置 ", padding=12, bootstyle="success"
    )
    resolution_card.pack(fill=X, pady=(0, 8))

    resolution_var = ttkb.StringVar(value=resolution_choice)
    custom_width_var = ttkb.StringVar(value=str(TARGET_WIDTH))
    custom_height_var = ttkb.StringVar(value=str(TARGET_HEIGHT))

    # 分辨率选择按钮组（使用2x2网格布局）
    res_btn_frame = ttkb.Frame(resolution_card)
    res_btn_frame.pack(fill=X, pady=(0, 8))

    # 分辨率选择（2x2网格布局）
    resolutions = [
        ("1080P", "1080P"),
        ("2K", "2K"),
        ("4K", "4K"),
        ("当前", "current"),
        ("自定义", "自定义"),
    ]

    def update_resolution_info():
        res = resolution_var.get()
        if res == "1080P":
            resolution_info_var.set("当前: 1920×1080")
        elif res == "2K":
            resolution_info_var.set("当前: 2560×1440")
        elif res == "4K":
            resolution_info_var.set("当前: 3840×2160")
        elif res == "current":
            # 显示当前系统分辨率
            current_width, current_height = get_current_screen_resolution()
            resolution_info_var.set(f"当前: {current_width}×{current_height}")
        else:
            resolution_info_var.set(
                f"当前: {custom_width_var.get()}×{custom_height_var.get()}"
            )

    def on_resolution_change():
        """当分辨率选择改变时，更新自定义输入框状态并保存更改"""
        # 更新分辨率信息
        update_resolution_info()

        # 根据选择更新显示值
        if resolution_var.get() == "current":
            # 使用当前系统分辨率
            current_width, current_height = get_current_screen_resolution()
            custom_width_var.set(str(current_width))
            custom_height_var.set(str(current_height))
        elif resolution_var.get() == "1080P":
            custom_width_var.set("1920")
            custom_height_var.set("1080")
        elif resolution_var.get() == "2K":
            custom_width_var.set("2560")
            custom_height_var.set("1440")
        elif resolution_var.get() == "4K":
            custom_width_var.set("3840")
            custom_height_var.set("2160")

        # 保存分辨率更改
        update_parameters(
            t_var,
            leftclickdown_var,
            leftclickup_var,
            times_var,
            paogantime_var,
            jiashi_var_option,
            resolution_var,
            custom_width_var,
            custom_height_var,
            hotkey_var,
            record_fish_var,
            legendary_screenshot_var,
            first_capture_screenshot_var,
        )

    # 创建分辨率选择按钮（3行2列布局）
    # 配置第3列（索引2）的权重为8，用于控制自定义分辨率输入框区域的横向扩展比例
    res_btn_frame.columnconfigure(0, weight=9)
    # 配置第9列（索引8）的权重为2，用于控制右侧空白区域的横向扩展比例，保持布局平衡
    res_btn_frame.columnconfigure(3, weight=1)

    # 3行2列布局排列：
    # 第1行: 1080P, 2K
    # 第2行: 4K, 当前
    # 第3行: 自定义, [自定义输入框]

    # 创建第1行按钮
    rb_1080p = ttkb.Radiobutton(
        res_btn_frame,
        text="1080P",
        variable=resolution_var,
        value="1080P",
        bootstyle="info-outline-toolbutton",
        command=on_resolution_change,
    )
    rb_1080p.grid(row=0, column=0, padx=2, pady=2, sticky="ew")

    rb_2k = ttkb.Radiobutton(
        res_btn_frame,
        text="2K",
        variable=resolution_var,
        value="2K",
        bootstyle="info-outline-toolbutton",
        command=on_resolution_change,
    )
    rb_2k.grid(row=0, column=1, padx=2, pady=2, sticky="ew")

    # 创建第2行按钮
    rb_4k = ttkb.Radiobutton(
        res_btn_frame,
        text="4K",
        variable=resolution_var,
        value="4K",
        bootstyle="info-outline-toolbutton",
        command=on_resolution_change,
    )
    rb_4k.grid(row=1, column=0, padx=2, pady=2, sticky="ew")

    rb_current = ttkb.Radiobutton(
        res_btn_frame,
        text="当前",
        variable=resolution_var,
        value="current",
        bootstyle="info-outline-toolbutton",
        command=on_resolution_change,
    )
    rb_current.grid(row=1, column=1, padx=2, pady=2, sticky="ew")

    # 创建第3行左侧的自定义按钮
    rb_custom = ttkb.Radiobutton(
        res_btn_frame,
        text="自定义",
        variable=resolution_var,
        value="自定义",
        bootstyle="info-outline-toolbutton",
        command=on_resolution_change,
    )
    rb_custom.grid(row=2, column=0, padx=2, pady=2, sticky="ew")

    # 创建第3行右侧的自定义输入框
    custom_input_frame = ttkb.Frame(res_btn_frame)
    custom_input_frame.grid(row=2, column=1, padx=2, pady=2, sticky="ew")

    custom_width_label = ttkb.Label(
        custom_input_frame, text="宽:", width=2, font=("Segoe UI", 9)
    )
    custom_width_label.pack(side=LEFT, padx=(0, 2))

    custom_width_entry = ttkb.Entry(
        custom_input_frame, textvariable=custom_width_var, width=5, font=("Segoe UI", 9)
    )
    custom_width_entry.pack(side=LEFT, padx=(0, 8))

    # 为自定义宽度输入框添加事件处理
    def on_custom_width_change(event):
        """当自定义宽度改变时，保存更改"""
        if resolution_var.get() == "自定义":
            update_parameters(
                t_var,
                leftclickdown_var,
                leftclickup_var,
                times_var,
                paogantime_var,
                jiashi_var_option,
                resolution_var,
                custom_width_var,
                custom_height_var,
                hotkey_var,
                record_fish_var,
                legendary_screenshot_var,
                first_capture_screenshot_var,
            )

    custom_width_entry.bind("<FocusOut>", on_custom_width_change)
    custom_width_entry.bind("<Return>", on_custom_width_change)

    custom_height_label = ttkb.Label(
        custom_input_frame, text="高:", width=2, font=("Segoe UI", 9)
    )
    custom_height_label.pack(side=LEFT, padx=(0, 2))

    custom_height_entry = ttkb.Entry(
        custom_input_frame,
        textvariable=custom_height_var,
        width=5,
        font=("Segoe UI", 9),
    )
    custom_height_entry.pack(side=LEFT)

    # 为自定义高度输入框添加事件处理
    def on_custom_height_change(event):
        """当自定义高度改变时，保存更改"""
        if resolution_var.get() == "自定义":
            update_parameters(
                t_var,
                leftclickdown_var,
                leftclickup_var,
                times_var,
                paogantime_var,
                jiashi_var_option,
                resolution_var,
                custom_width_var,
                custom_height_var,
                hotkey_var,
                record_fish_var,
                legendary_screenshot_var,
            )

    custom_height_entry.bind("<FocusOut>", on_custom_height_change)
    custom_height_entry.bind("<Return>", on_custom_height_change)

    # 当前分辨率信息标签
    resolution_info_var = ttkb.StringVar(value=f"当前: {TARGET_WIDTH}×{TARGET_HEIGHT}")
    info_label = ttkb.Label(
        resolution_card,
        textvariable=resolution_info_var,
        bootstyle="info",
        font=("Segoe UI", 9),
    )
    # 始终显示分辨率信息标签
    info_label.pack(pady=(4, 0))

    # ==================== 钓鱼记录开关卡片 ====================
    record_card = ttkb.Labelframe(
        left_content_frame, text=" 📝 钓鱼记录设置 ", padding=12, bootstyle="info"
    )
    record_card.pack(fill=X, pady=(0, 8))

    # 钓鱼记录开关
    record_fish_var = ttkb.IntVar(value=1 if record_fish_enabled else 0)

    record_frame = ttkb.Frame(record_card)
    record_frame.pack(fill=X, pady=4)

    record_label = ttkb.Label(
        record_frame, text="是否启用钓鱼记录", font=("Segoe UI", 9), bootstyle="info"
    )
    record_label.pack(side=LEFT, padx=(0, 8))

    record_btn_frame = ttkb.Frame(record_frame)
    record_btn_frame.pack(side=RIGHT)

    record_yes = ttkb.Radiobutton(
        record_btn_frame,
        text="是",
        variable=record_fish_var,
        value=1,
        bootstyle="success-outline-toolbutton",
    )
    record_yes.pack(side=LEFT, padx=5)

    record_no = ttkb.Radiobutton(
        record_btn_frame,
        text="否",
        variable=record_fish_var,
        value=0,
        bootstyle="danger-outline-toolbutton",
    )
    record_no.pack(side=LEFT, padx=5)

    # 传奇鱼自动截屏开关
    legendary_screenshot_var = ttkb.IntVar(
        value=1 if legendary_screenshot_enabled else 0
    )

    legendary_frame = ttkb.Frame(record_card)
    legendary_frame.pack(fill=X, pady=4)

    legendary_label = ttkb.Label(
        legendary_frame, text="传奇鱼自动截屏", font=("Segoe UI", 9), bootstyle="info"
    )
    legendary_label.pack(side=LEFT, padx=(0, 8))

    legendary_btn_frame = ttkb.Frame(legendary_frame)
    legendary_btn_frame.pack(side=RIGHT)

    legendary_yes = ttkb.Radiobutton(
        legendary_btn_frame,
        text="是",
        variable=legendary_screenshot_var,
        value=1,
        bootstyle="success-outline-toolbutton",
    )
    legendary_yes.pack(side=LEFT, padx=5)

    legendary_no = ttkb.Radiobutton(
        legendary_btn_frame,
        text="否",
        variable=legendary_screenshot_var,
        value=0,
        bootstyle="danger-outline-toolbutton",
    )
    legendary_no.pack(side=LEFT, padx=5)

    # 首次捕获自动截屏开关
    first_capture_screenshot_var = ttkb.IntVar(
        value=1 if first_capture_screenshot_enabled else 0
    )

    first_capture_frame = ttkb.Frame(record_card)
    first_capture_frame.pack(fill=X, pady=4)

    first_capture_label = ttkb.Label(
        first_capture_frame, text="首次捕获自动截屏", font=("Segoe UI", 9), bootstyle="info"
    )
    first_capture_label.pack(side=LEFT, padx=(0, 8))

    first_capture_btn_frame = ttkb.Frame(first_capture_frame)
    first_capture_btn_frame.pack(side=RIGHT)

    first_capture_yes = ttkb.Radiobutton(
        first_capture_btn_frame,
        text="是",
        variable=first_capture_screenshot_var,
        value=1,
        bootstyle="success-outline-toolbutton",
    )
    first_capture_yes.pack(side=LEFT, padx=5)

    first_capture_no = ttkb.Radiobutton(
        first_capture_btn_frame,
        text="否",
        variable=first_capture_screenshot_var,
        value=0,
        bootstyle="danger-outline-toolbutton",
    )
    first_capture_no.pack(side=LEFT, padx=5)

    # ==================== UNO UI ====================
    # 添加UNO的UI元素
    uno_card = ttkb.Labelframe(
        left_content_frame, text=" 🎮 UNO 设置 ", padding=12, bootstyle="primary"
    )
    uno_card.pack(fill=X, pady=(0, 8))

    # UNO开关
    uno_var = ttkb.IntVar(value=0)

    uno_frame = ttkb.Frame(uno_card)
    uno_frame.pack(fill=X, pady=4)

    uno_btn_frame = ttkb.Frame(uno_frame)
    uno_btn_frame.pack(side=RIGHT)

    # ==================== UNO热键设置 ====================
    # UNO热键显示变量
    global uno_hotkey_var
    uno_hotkey_var = ttkb.StringVar(value=uno_hotkey_name)

    # UNO热键捕获状态
    uno_is_capturing_hotkey = [False]  # 使用列表以便在闭包中修改
    uno_captured_modifiers = [set()]
    uno_captured_main_key = [None]
    uno_captured_main_key_name = [""]
    uno_capture_listener = [None]

    uno_hotkey_frame = ttkb.Frame(uno_card)
    uno_hotkey_frame.pack(fill=X, pady=4)

    uno_hotkey_label = ttkb.Label(
        uno_hotkey_frame,
        text="UNO功能热键",
        font=("Segoe UI", 9, "bold"),
        bootstyle="primary",
    )
    uno_hotkey_label.pack(side=LEFT, padx=(0, 8))

    # UNO热键显示按钮（点击后进入捕获模式）
    uno_hotkey_btn = ttkb.Button(
        uno_hotkey_frame, text=uno_hotkey_name, bootstyle="primary", width=12
    )
    uno_hotkey_btn.pack(side=RIGHT, padx=(8, 0))

    # UNO热键信息提示
    uno_hotkey_info_label = ttkb.Label(
        uno_card,
        text=f"按 {uno_hotkey_name} 触发UNO功能 | 点击按钮修改",
        bootstyle="primary",
        font=("Segoe UI", 8, "bold"),
    )
    uno_hotkey_info_label.pack(pady=(4, 0), padx=4)

    # UNO热键提示标签（用于捕获模式显示）
    uno_hotkey_tip_label = ttkb.Label(
        uno_card, text="", bootstyle="secondary", font=("Segoe UI", 8)
    )

    def uno_stop_hotkey_capture():
        """停止UNO热键捕获"""
        uno_is_capturing_hotkey[0] = False
        # 停止键盘监听器
        if uno_capture_listener[0] is not None:
            try:
                uno_capture_listener[0].stop()
            except:
                pass
            uno_capture_listener[0] = None
        # 停止鼠标监听器
        if "uno_mouse_capture_listener" in globals():
            mouse_listener = globals()["uno_mouse_capture_listener"]
            if mouse_listener is not None:
                try:
                    mouse_listener.stop()
                except:
                    pass
            globals()["uno_mouse_capture_listener"] = None
        uno_hotkey_btn.configure(bootstyle="info-outline")
        uno_hotkey_tip_label.pack_forget()  # 隐藏提示
        uno_hotkey_info_label.configure(
            text=f"按 {uno_hotkey_var.get()} 触发UNO功能 | 点击按钮修改"
        )

    def uno_on_capture_key_press(key):
        """捕获UNO热键按下事件"""
        if not uno_is_capturing_hotkey[0]:
            return False  # 停止监听

        # 检查是否是修饰键
        if key in MODIFIER_KEYS:
            uno_captured_modifiers[0].add(MODIFIER_KEYS[key])
            # 更新按钮显示
            display_parts = []
            if "ctrl" in uno_captured_modifiers[0]:
                display_parts.append("Ctrl")
            if "alt" in uno_captured_modifiers[0]:
                display_parts.append("Alt")
            if "shift" in uno_captured_modifiers[0]:
                display_parts.append("Shift")
            display_parts.append("...")
            root.after(
                0, lambda: uno_hotkey_btn.configure(text="+".join(display_parts))
            )
            return True

        # 这是主按键
        uno_captured_main_key[0] = key
        uno_captured_main_key_name[0] = key_to_name(key)

        # 生成热键字符串
        new_hotkey = format_hotkey_display(
            uno_captured_modifiers[0], uno_captured_main_key_name[0]
        )

        # 更新GUI
        def update_gui():
            uno_hotkey_var.set(new_hotkey)
            uno_hotkey_btn.configure(text=new_hotkey)
            uno_hotkey_info_label.configure(text=f"新热键: {new_hotkey} | 点击保存生效")
            uno_stop_hotkey_capture()

        root.after(0, update_gui)
        return False  # 停止监听

    def uno_on_capture_key_release(key):
        """捕获UNO热键释放事件"""
        if not uno_is_capturing_hotkey[0]:
            return False
        # 释放修饰键时移除
        if key in MODIFIER_KEYS:
            uno_captured_modifiers[0].discard(MODIFIER_KEYS[key])
        return True

    def uno_on_capture_mouse_click(x, y, button, pressed):
        """捕获UNO热键鼠标点击事件"""
        if not uno_is_capturing_hotkey[0] or not pressed:
            return

        # 只允许鼠标侧键（x1, x2），禁用左右中键
        if button not in [mouse.Button.x1, mouse.Button.x2]:
            return

        # 鼠标侧键作为主按键
        uno_captured_main_key[0] = button
        uno_captured_main_key_name[0] = key_to_name(button)

        # 生成热键字符串
        new_hotkey = format_hotkey_display(
            uno_captured_modifiers[0], uno_captured_main_key_name[0]
        )

        # 更新GUI
        def update_gui():
            uno_hotkey_var.set(new_hotkey)
            uno_hotkey_btn.configure(text=new_hotkey)
            uno_hotkey_info_label.configure(text=f"新热键: {new_hotkey} | 点击保存生效")
            uno_stop_hotkey_capture()

        root.after(0, update_gui)

    def uno_start_hotkey_capture():
        """开始UNO热键捕获"""
        if uno_is_capturing_hotkey[0]:
            uno_stop_hotkey_capture()
            return

        # 重置捕获状态
        uno_captured_modifiers[0] = set()
        uno_captured_main_key[0] = None
        uno_captured_main_key_name[0] = ""

        uno_is_capturing_hotkey[0] = True

        # 启动键盘监听器
        uno_capture_listener[0] = keyboard.Listener(
            on_press=uno_on_capture_key_press,
            on_release=uno_on_capture_key_release,
            suppress=False,
        )
        uno_capture_listener[0].start()

        # 启动鼠标监听器（用于检测侧键）
        mouse_listener = mouse.Listener(
            on_click=uno_on_capture_mouse_click, suppress=False
        )
        mouse_listener.start()
        globals()["uno_mouse_capture_listener"] = mouse_listener

        # 更新UI
        uno_hotkey_btn.configure(text="请按键...", bootstyle="warning")
        uno_hotkey_info_label.configure(text="按下组合键（如Ctrl+F3）或单键/鼠标侧键")
        uno_hotkey_tip_label.configure(text="5秒内按键，或再次点击取消")
        uno_hotkey_tip_label.pack(pady=(2, 0))  # 显示提示

        # 5秒后自动取消捕获
        def auto_cancel():
            if uno_is_capturing_hotkey[0]:
                root.after(
                    0, lambda: uno_hotkey_btn.configure(text=uno_hotkey_var.get())
                )
                uno_stop_hotkey_capture()

        root.after(5000, auto_cancel)

    # 设置UNO热键按钮的点击事件
    uno_hotkey_btn.configure(command=uno_start_hotkey_capture)

    # UNO输入框设置
    uno_inputs_frame = ttkb.Frame(uno_card)
    uno_inputs_frame.pack(fill=X, pady=8)

    # 当前牌数
    uno_input1_frame = ttkb.Frame(uno_inputs_frame)
    uno_input1_frame.pack(fill=X, pady=4)
    uno_input1_label = ttkb.Label(
        uno_input1_frame,
        text="当前牌数:",
        font=("Segoe UI", 9),
        bootstyle="primary",
        width=8,
    )
    uno_input1_label.pack(side=LEFT, padx=(0, 8))
    uno_input1_var = ttkb.IntVar(value=7)
    uno_input1_spacer = ttkb.Frame(uno_input1_frame)
    uno_input1_spacer.pack(side=LEFT, fill=X, expand=YES)
    uno_input1 = ttkb.Entry(
        uno_input1_frame,
        textvariable=uno_input1_var,
        width=2,
        font=("Segoe UI", 9),
        bootstyle="light",
        state="readonly",
    )
    uno_input1.pack(side=RIGHT, padx=(0, 5))  # 靠右显示，右边间距5

    # 抽取牌数次数
    uno_input2_frame = ttkb.Frame(uno_inputs_frame)
    uno_input2_frame.pack(fill=X, pady=4)
    uno_input2_label = ttkb.Label(
        uno_input2_frame,
        text="抽取牌数:",
        font=("Segoe UI", 9),
        bootstyle="primary",
        width=8,
    )
    uno_input2_label.pack(side=LEFT, padx=(0, 8))
    uno_input2_var = ttkb.IntVar(value=35)
    uno_input2_spacer = ttkb.Frame(uno_input2_frame)
    uno_input2_spacer.pack(side=LEFT, fill=X, expand=YES)
    uno_input2 = ttkb.Entry(
        uno_input2_frame, textvariable=uno_input2_var, width=2, bootstyle="primary"
    )
    uno_input2.pack(side=RIGHT, padx=(0, 5))  # 靠右显示，右边间距5

    # ==================== 放生设置 ====================
    # 添加放生功能的UI元素
    release_card = ttkb.Labelframe(
        left_content_frame, text=" 🐠 放生设置 ", padding=12, bootstyle="success"
    )
    release_card.pack(fill=X, pady=(0, 8))

    # 放生功能总开关
    release_enabled_var = ttkb.BooleanVar(value=release_fish_enabled)
    release_frame = ttkb.Frame(release_card)
    release_frame.pack(fill=X, pady=4)

    release_label = ttkb.Label(
        release_frame,
        text="启用放生功能",
        font=("Segoe UI", 9, "bold"),
        bootstyle="success",
    )
    release_label.pack(side=LEFT, padx=(0, 8))

    release_switch = ttkb.Checkbutton(
        release_frame,
        variable=release_enabled_var,
        bootstyle="success-switch",
    )
    release_switch.pack(side=RIGHT)

    # 品质选择框
    release_quality_frame = ttkb.Frame(release_card)
    release_quality_frame.pack(fill=X, pady=(8, 0))

    ttkb.Label(
        release_quality_frame,
        text="选择要放生的品质",
        font=("Segoe UI", 9),
        bootstyle="success",
    ).pack(anchor=CENTER, pady=(0, 4))

    # 品质选择复选框
    release_quality_check_frame = ttkb.Frame(release_card)
    release_quality_check_frame.pack(fill=X, pady=4)

    # 第一行：标准、非凡
    release_quality_row1 = ttkb.Frame(release_quality_check_frame)
    release_quality_row1.pack(fill=X, pady=1)

    # 标准鱼
    release_standard_var = ttkb.BooleanVar(value=release_standard_enabled)
    standard_cb = ttkb.Checkbutton(
        release_quality_row1,
        text="⚪ 标准",
        variable=release_standard_var,
        bootstyle="success",
    )
    standard_cb.pack(side=LEFT, padx=2)

    # 非凡鱼
    release_uncommon_var = ttkb.BooleanVar(value=release_uncommon_enabled)
    uncommon_cb = ttkb.Checkbutton(
        release_quality_row1,
        text="🟢 非凡",
        variable=release_uncommon_var,
        bootstyle="success",
    )
    uncommon_cb.pack(side=LEFT, padx=2)

    # 幻神稀有鱼
    release_phantom_rare_var = ttkb.BooleanVar(value=release_phantom_rare_enabled)
    phantom_rare_cb = ttkb.Checkbutton(
        release_quality_row1,
        text="🔱 幻神稀有",
        variable=release_phantom_rare_var,
        bootstyle="success",
    )
    phantom_rare_cb.pack(side=LEFT, padx=2)

    # 第二行：稀有、史诗、传奇
    release_quality_row2 = ttkb.Frame(release_quality_check_frame)
    release_quality_row2.pack(fill=X, pady=1)

    # 稀有鱼
    release_rare_var = ttkb.BooleanVar(value=release_rare_enabled)
    rare_cb = ttkb.Checkbutton(
        release_quality_row2,
        text="🔵 稀有",
        variable=release_rare_var,
        bootstyle="success",
    )
    rare_cb.pack(side=LEFT, padx=2)

    # 史诗鱼
    release_epic_var = ttkb.BooleanVar(value=release_epic_enabled)
    epic_cb = ttkb.Checkbutton(
        release_quality_row2,
        text="🟣 史诗",
        variable=release_epic_var,
        bootstyle="success",
    )
    epic_cb.pack(side=LEFT, padx=2)

    # 传奇鱼
    release_legendary_var = ttkb.BooleanVar(value=release_legendary_enabled)
    legendary_cb = ttkb.Checkbutton(
        release_quality_row2,
        text="🟡 传奇",
        variable=release_legendary_var,
        bootstyle="success",
    )
    legendary_cb.pack(side=LEFT, padx=2)

    # ==================== 右侧面板（钓鱼记录区域） ====================
    right_panel = ttkb.Frame(main_frame)
    right_panel.grid(row=0, column=1, sticky="nsew")

    # 配置右侧面板的行列权重，确保内部组件能正确扩展
    right_panel.columnconfigure(0, weight=1)  # 唯一列自适应宽度
    right_panel.rowconfigure(0, weight=1)  # 唯一行自适应高度

    # 创建右侧面板的垂直分割
    right_paned = tk.PanedWindow(
        right_panel, orient="vertical", sashwidth=6, sashrelief="raised", bg="#2d3748"
    )
    right_paned.pack(fill=BOTH, expand=YES)

    # 上半部分：钓鱼记录
    fish_record_frame = ttkb.Frame(right_paned, padding=8)
    right_paned.add(fish_record_frame, minsize=300)

    # 下半部分：运行日志
    log_frame = ttkb.Frame(right_paned, padding=8)
    right_paned.add(log_frame, minsize=200)

    # ==================== 钓鱼记录卡片 ====================
    # 先创建style对象
    style = ttk.Style()

    # 设置自定义海洋蓝边框
    style.configure("OceanBlue.TLabelframe", bordercolor="#1E90FF")
    style.configure("OceanBlue.TLabelframe.Label", foreground="#1E90FF")

    fish_record_card = ttkb.Labelframe(
        fish_record_frame, text=" 🐟 钓鱼记录 ", padding=12, bootstyle="primary"
    )
    fish_record_card.pack(fill=BOTH, expand=YES)
    fish_record_card.configure(style="OceanBlue.TLabelframe")

    # 切换按钮（本次/总览）
    record_view_frame = ttkb.Frame(fish_record_card)
    record_view_frame.pack(fill=X, pady=(0, 10))

    view_mode = ttkb.StringVar(value="current")

    current_btn = ttkb.Radiobutton(
        record_view_frame,
        text="本次钓鱼",
        variable=view_mode,
        value="current",
        bootstyle="info-outline-toolbutton",
        command=lambda: update_fish_display(),
    )
    current_btn.pack(side=LEFT, padx=5)

    today_btn = ttkb.Radiobutton(
        record_view_frame,
        text="当天钓鱼",
        variable=view_mode,
        value="today",
        bootstyle="info-outline-toolbutton",
        command=lambda: update_fish_display(),
    )
    today_btn.pack(side=LEFT, padx=5)

    all_btn = ttkb.Radiobutton(
        record_view_frame,
        text="历史总览",
        variable=view_mode,
        value="all",
        bootstyle="info-outline-toolbutton",
        command=lambda: update_fish_display(),
    )
    all_btn.pack(side=LEFT, padx=5)

    # 刷新按钮
    refresh_btn = ttkb.Button(
        record_view_frame,
        text="🔄",
        command=lambda: update_fish_display(),
        bootstyle="info-outline",
        width=3,
    )
    refresh_btn.pack(side=RIGHT, padx=5)

    # 搜索和筛选框
    search_frame = ttkb.Frame(fish_record_card)
    search_frame.pack(fill=X, pady=(0, 10))

    search_var = ttkb.StringVar()
    search_entry = ttkb.Entry(search_frame, textvariable=search_var, width=15)
    search_entry.pack(side=LEFT, padx=(0, 5))
    search_entry.insert(0, "搜索鱼名...")

    # 保存搜索输入框到全局列表
    input_entries.append(search_entry)

    def on_search_focus_in(event):
        if search_entry.get() == "搜索鱼名...":
            search_entry.delete(0, "end")

    def on_search_focus_out(event):
        if not search_entry.get():
            search_entry.insert(0, "搜索鱼名...")

    search_entry.bind("<FocusIn>", on_search_focus_in)
    search_entry.bind("<FocusOut>", on_search_focus_out)
    search_entry.bind("<Return>", lambda e: update_fish_display())

    search_btn = ttkb.Button(
        search_frame,
        text="🔍",
        command=lambda: update_fish_display(),
        bootstyle="info-outline",
        width=3,
    )
    search_btn.pack(side=LEFT, padx=(0, 10))

    # 品质筛选
    quality_var = ttkb.StringVar(value="全部")
    quality_label = ttkb.Label(search_frame, text="品质:")
    quality_label.pack(side=LEFT)
    quality_combo = ttkb.Combobox(
        search_frame,
        textvariable=quality_var,
        values=["全部"] + GUI_QUALITY_LEVELS,
        width=8,
        state="readonly",
    )
    quality_combo.pack(side=LEFT, padx=5)
    quality_combo.bind("<<ComboboxSelected>>", lambda e: update_fish_display())

    # 保存品质筛选组合框到全局列表
    combo_boxes.append(quality_combo)

    # 统计信息卡片
    # 设置自定义亮色主题，与深色背景搭配
    style.configure("Custom.TLabelframe", bordercolor="#4F46E5")
    style.configure(
        "Custom.TLabelframe.Label", foreground="#E2E8F0", font=("Segoe UI", 10, "bold")
    )

    stats_card = ttkb.Labelframe(
        fish_record_card, text=" 📊 钓鱼统计 ", padding=15, bootstyle="primary"
    )
    stats_card.pack(fill=X, pady=(0, 12))
    stats_card.configure(relief="solid", borderwidth=1)
    stats_card.configure(style="Custom.TLabelframe")

    # 创建统计标签变量
    standard_var = ttkb.StringVar(value="⚪ 标准: 0 (0.00%)")
    uncommon_var = ttkb.StringVar(value="🟢 非凡: 0 (0.00%)")
    rare_var = ttkb.StringVar(value="🔵 稀有: 0 (0.00%)")
    epic_var = ttkb.StringVar(value="🟣 史诗: 0 (0.00%)")
    legendary_var = ttkb.StringVar(value="🟡 传奇: 0 (0.00%)")
    total_var = ttkb.StringVar(value="📝 总计: 0 条")

    # 品质统计布局 - 更美观的网格布局
    stats_grid = ttkb.Frame(stats_card)
    stats_grid.pack(fill=BOTH, expand=YES, side=LEFT)

    # 品质统计容器
    quality_stats_frame = ttkb.Frame(stats_grid)
    quality_stats_frame.pack(side=LEFT, fill=X, expand=YES)

    # 第一行：标准、非凡、稀有
    row1_frame = ttkb.Frame(quality_stats_frame)
    row1_frame.pack(fill=X, pady=(0, 5))

    standard_label = ttkb.Label(
        row1_frame,
        textvariable=standard_var,
        foreground="#94A3B8",
        font=("Segoe UI", 9, "bold"),
    )
    standard_label.pack(side=LEFT, padx=12, pady=3, expand=YES)

    uncommon_label = ttkb.Label(
        row1_frame,
        textvariable=uncommon_var,
        foreground="#34D399",
        font=("Segoe UI", 9, "bold"),
    )
    uncommon_label.pack(side=LEFT, padx=12, pady=3, expand=YES)

    rare_label = ttkb.Label(
        row1_frame,
        textvariable=rare_var,
        foreground="#60A5FA",
        font=("Segoe UI", 9, "bold"),
    )
    rare_label.pack(side=LEFT, padx=12, pady=3, expand=YES)

    # 传奇
    row2_frame = ttkb.Frame(quality_stats_frame)
    row2_frame.pack(fill=X, pady=(5, 0))

    epic_label = ttkb.Label(
        row2_frame,
        textvariable=epic_var,
        foreground="#A78BFA",
        font=("Segoe UI", 9, "bold"),
    )
    epic_label.pack(side=LEFT, padx=12, pady=3, expand=YES)

    legendary_label = ttkb.Label(
        row2_frame,
        textvariable=legendary_var,
        foreground="#FBBF24",
        font=("Segoe UI", 9, "bold"),
    )
    legendary_label.pack(side=LEFT, padx=12, pady=3, expand=YES)

    total_label = ttkb.Label(
        row2_frame,
        textvariable=total_var,
        foreground="#64748B",
        font=("Segoe UI", 9, "bold"),
    )
    total_label.pack(side=LEFT, padx=12, pady=3, expand=YES)

    # 清空按钮 - 更优雅的设计
    button_frame = ttkb.Frame(stats_card)
    button_frame.pack(side=RIGHT, fill=Y, padx=(10, 0))

    clear_btn = ttkb.Button(
        button_frame,
        text="🗑️ 清空记录",
        command=lambda: clear_fish_records(),
        bootstyle="danger-outline",
    )
    clear_btn.pack(side=TOP, pady=5, padx=5)

    # 统计卡片和Treeview之间的分隔线
    divider = ttkb.Separator(fish_record_card, orient="horizontal")
    divider.pack(fill=X, pady=10)

    # 记录列表容器（包含Treeview和滚动条）- 现代化设计
    tree_container = ttkb.Frame(fish_record_card, borderwidth=1, relief="solid")
    tree_container.pack(fill=BOTH, expand=YES, pady=(0, 8))

    # 记录列表（使用Treeview）
    columns = ("时间", "名称", "品质", "重量")
    fish_tree = ttkb.Treeview(
        tree_container,
        columns=columns,
        show="headings",
        style="CustomTreeview.Treeview",  # 使用自定义样式名称，避免bootstyle冲突
    )

    # 保存Treeview引用到全局变量
    global fish_tree_ref
    fish_tree_ref = fish_tree

    # 添加垂直滚动条（放在Treeview右侧）
    tree_scroll = ttkb.Scrollbar(
        tree_container,
        orient="vertical",
        command=fish_tree.yview,
        bootstyle="secondary",
    )
    fish_tree.configure(yscrollcommand=tree_scroll.set)

    # 设置列标题样式 - 现代化设计
    style.configure(
        "CustomTreeview.Treeview.Heading",
        background="#3B82F6",
        foreground="#ffffff",
        font=("Segoe UI", 10, "bold"),
        borderwidth=0,
        relief="flat",
        padding=(10, 5),
    )

    # 设置列标题
    fish_tree.heading("时间", text="时间", anchor="center")
    fish_tree.heading("名称", text="鱼名", anchor="center")
    fish_tree.heading("品质", text="品质", anchor="center")
    fish_tree.heading("重量", text="重量", anchor="center")

    # 不设置固定列宽，而是在程序初始化后调用动态调整列宽的函数
    # 初始化列宽为0，稍后会根据字体大小动态调整
    fish_tree.column(
        "时间", width=0, anchor="center", stretch=YES, minwidth=120
    )  # 启用自动拉伸
    fish_tree.column(
        "名称", width=0, anchor="center", stretch=YES, minwidth=150
    )  # 启用自动拉伸
    fish_tree.column(
        "品质", width=0, anchor="center", stretch=YES, minwidth=80
    )  # 启用自动拉伸
    fish_tree.column(
        "重量", width=0, anchor="center", stretch=YES, minwidth=100
    )  # 启用自动拉伸

    # 布局Treeview和滚动条
    fish_tree.pack(side=LEFT, fill=BOTH, expand=YES)
    tree_scroll.pack(side=RIGHT, fill=Y)

    # 配置品质颜色标签（背景色和前景色）- 优化配色方案
    # 标准-浅灰色, 非凡-清新绿, 稀有-海洋蓝, 史诗-优雅紫, 传奇-尊贵金
    # 文字颜色统一为黑色，背景色使用更鲜艳的颜色
    quality_colors = {
        # 将标准和繁体标准合并为同一颜色配置
        **{q: ("#FFFFFF", "#000000") for q in ["标准", "標準"]},
        "非凡": ("#2ECC71", "#000000"),
        "稀有": ("#1E90FF", "#FFFFFF"),
        **{q: ("#9B59B6", "#FFFFFF") for q in ["史诗", "史詩"]},
        # 将传奇、傳奇合并为同一颜色配置
        **{q: ("#F1C40F", "#000000") for q in ["传奇", "传说", "傳奇"]},
    }

    for quality, (bg, fg) in quality_colors.items():
        fish_tree.tag_configure(quality, background=bg, foreground=fg)

    # 设置Treeview行高和字体 - 现代化设计
    # 移除background和fieldbackground设置，让标签背景色能够显示
    style.configure(
        "CustomTreeview.Treeview",
        font=("Segoe UI", 9, "bold"),
        foreground="#1E293B",
        rowheight=28,
        bordercolor="#E2E8F0",
        relief="flat",
    )

    # 设置Treeview选中项样式
    style.map(
        "CustomTreeview.Treeview",
        background=[("selected", "#3B82F6")],
        foreground=[("selected", "#FFFFFF")],
    )

    # 绑定鼠标滚轮到Treeview
    def on_tree_mousewheel(event):
        fish_tree.yview_scroll(int(-1 * (event.delta / 120)), "units")

    fish_tree.bind("<MouseWheel>", on_tree_mousewheel)

    # 统计信息
    stats_var = ttkb.StringVar(value="共 0 条记录")
    stats_label = ttkb.Label(fish_record_card, textvariable=stats_var, bootstyle="info")
    stats_label.pack()

    def update_fish_display():
        """更新钓鱼记录显示"""
        # 清空列表
        for item in fish_tree.get_children():
            fish_tree.delete(item)

        # 获取搜索关键词
        keyword = search_var.get()
        if keyword == "搜索鱼名...":
            keyword = ""

        # 获取视图模式
        mode = view_mode.get()
        quality_filter = quality_var.get()

        # 获取所有记录
        all_records = []

        # 根据视图模式选择数据源和筛选逻辑
        if mode == "current":
            # 本次钓鱼
            all_records = current_session_fish
            filtered = search_fish_records(keyword, quality_filter, True)
        elif mode == "today":
            # 当天钓鱼
            # 获取今天的日期字符串
            today = datetime.date.today().strftime("%Y-%m-%d")
            # 从所有记录中筛选出今天的记录
            all_records = [
                record
                for record in all_fish_records
                if record.timestamp.startswith(today)
            ]
            # 应用品质筛选和关键词搜索
            filtered = []
            for record in all_records:
                # 品质筛选
                if quality_filter != "全部":
                    if quality_filter == "传奇":
                        if record.quality not in ["传奇", "傳奇"]:
                            continue
                    elif quality_filter == "标准":
                        if record.quality not in ["标准", "標準"]:
                            continue
                    elif quality_filter == "史诗":
                        if record.quality not in ["史詩", "史诗"]:
                            continue
                    else:
                        if record.quality != quality_filter:
                            continue
                # 关键词搜索
                if keyword and keyword.lower() not in record.name.lower():
                    continue
                filtered.append(record)
        else:  # all
            # 历史总览
            all_records = all_fish_records
            filtered = search_fish_records(keyword, quality_filter, False)

        # 计算品质统计
        total = len(all_records)
        quality_counts = {
            "标准": 0,
            "非凡": 0,
            "稀有": 0,
            "史诗": 0,
            "传奇": 0,
        }

        for record in all_records:
            quality = record.quality
            # 处理繁体中文品质，映射到简体中文键
            if quality in ["傳奇", "傅奇"]:
                quality = "传奇"
            elif quality == "史詩":
                quality = "史诗"
            elif quality == "传说":
                quality = "传奇"
            elif quality == "標準":
                quality = "标准"

            if quality in quality_counts:
                quality_counts[quality] += 1

        # 合并传奇和传说的计数（因为它们是同一品质的不同名称）
        total_legendary = quality_counts["传奇"]

        # 计算概率并更新标签
        def calc_percentage(count):
            return (count / total * 100) if total > 0 else 0

        # 品质图标映射
        quality_icons = {
            "标准": "⚪",
            "非凡": "🟢",
            "稀有": "🔵",
            "史诗": "🟣",
            "传奇": "🟡",
        }

        # 格式化显示，优化样式和颜色
        def format_quality_stat(icon, name, count, percentage):
            # 品质名称与颜色映射
            color_map = {
                "标准": "#64748B",
                "非凡": "#10B981",
                "稀有": "#3B82F6",
                "史诗": "#8B5CF6",
                "传奇": "#F59E0B",
            }
            color = color_map.get(name, "#64748B")
            return f"{icon} {name}: <span style='color:{color}; font-weight:bold;'>{count}</span> (<span style='color:{color};'>{percentage:.2f}%</span>)"

        # 更新品质统计标签
        standard_var.set(
            f"⚪ 标准: {quality_counts['标准']} ({calc_percentage(quality_counts['标准']):.2f}%)"
        )
        uncommon_var.set(
            f"🟢 非凡: {quality_counts['非凡']} ({calc_percentage(quality_counts['非凡']):.2f}%)"
        )
        rare_var.set(
            f"🔵 稀有: {quality_counts['稀有']} ({calc_percentage(quality_counts['稀有']):.2f}%)"
        )
        epic_var.set(
            f"🟣 史诗: {quality_counts['史诗']} ({calc_percentage(quality_counts['史诗']):.2f}%)"
        )
        legendary_var.set(
            f"🟡 传奇: {total_legendary} ({calc_percentage(total_legendary):.2f}%)"
        )

        # 根据视图模式更新总计显示
        total_icon = "📊"
        if mode == "current":
            total_var.set(f"{total_icon} 本次总计: {total} 条")
        elif mode == "today":
            total_var.set(f"{total_icon} 当天总计: {total} 条")
        else:
            total_var.set(f"{total_icon} 历史总计: {total} 条")

        # 显示记录（倒序，最新的在前面）
        for record in reversed(filtered[-300:]):  # 最多显示300条
            # 直接使用完整时间戳（格式：YYYY-MM-DD HH:MM:SS）
            time_display = record.timestamp if record.timestamp else "未知时间"

            # 根据品质确定标签（用于显示颜色）
            quality_tag = (
                record.quality
                if record.quality
                in ["标准", "非凡", "稀有", "史诗", "史詩", "传奇", "標準", "傳奇"]
                else "标准"
            )

            fish_tree.insert(
                "",
                "end",
                values=(time_display, record.name, record.quality, record.weight),
                tags=(quality_tag,),
            )

        # 更新统计
        total_display = len(filtered)
        if mode == "current":
            stats_var.set(f"本次: {total_display} 条")
        elif mode == "today":
            stats_var.set(f"当天: {total_display} 条")
        else:
            stats_var.set(f"总计: {total_display} 条")

    # 设置GUI更新回调
    global gui_fish_update_callback

    def safe_update():
        try:
            root.after(0, update_fish_display)
        except:
            pass

    gui_fish_update_callback = safe_update

    def clear_fish_records():
        """清空钓鱼记录"""
        # 询问确认
        use_session = view_mode.get() == "current"
        if use_session:
            confirm_text = "确定要清空本次钓鱼记录吗？"
        else:
            confirm_text = "确定要清空所有历史钓鱼记录吗？此操作不可恢复！"

        result = messagebox.askyesno("确认清空", confirm_text, parent=root)
        if not result:
            return

        with fish_record_lock:
            if use_session:
                # 清空当前会话记录
                global current_session_fish
                current_session_fish.clear()
            else:
                # 清空所有记录
                global all_fish_records
                all_fish_records.clear()
                # 清空记录文件
                try:
                    with open(FISH_RECORD_FILE, "w", encoding="utf-8") as f:
                        f.write("")
                except Exception as e:
                    print(f"❌ [错误] 清空记录文件失败: {e}")

        # 更新显示
        update_fish_display()

    # 初始加载
    update_fish_display()

    # ==================== 运行日志卡片 ====================
    log_card = ttkb.Labelframe(
        log_frame, text=" 📝 运行日志 ", padding=12, bootstyle="primary"
    )
    log_card.pack(fill=BOTH, expand=YES)

    # 控制按钮框架
    log_control_frame = ttkb.Frame(log_card)
    log_control_frame.pack(fill=X, pady=(0, 10))

    # 清空日志按钮
    def clear_logs():
        """清空运行日志"""
        result = messagebox.askyesno(
            "确认清空", "确定要清空所有运行日志吗？", parent=root
        )
        if result:
            global log_history
            with log_history_lock:
                log_history.clear()
            # 清空文本框
            log_text.config(state="normal")
            log_text.delete(1.0, tk.END)
            log_text.config(state="disabled")
            print("🧹 [日志] 运行日志已清空")

    clear_log_btn = ttkb.Button(
        log_control_frame,
        text="🧹 清空日志",
        command=clear_logs,
        bootstyle="danger-outline",
        width=12,
    )
    clear_log_btn.pack(side=LEFT, padx=(0, 10))

    # 自动滚动开关
    auto_scroll_var = tk.BooleanVar(value=True)
    auto_scroll_check = ttkb.Checkbutton(
        log_control_frame,
        text="自动滚动到底部",
        variable=auto_scroll_var,
        bootstyle="info",
    )
    auto_scroll_check.pack(side=LEFT, padx=(0, 10))

    # 日志行数显示
    log_count_var = ttkb.StringVar(value="日志行数: 0")
    log_count_label = ttkb.Label(
        log_control_frame,
        textvariable=log_count_var,
        bootstyle="info",
        font=("Segoe UI", 9),
    )
    log_count_label.pack(side=LEFT)

    # 日志显示区域
    log_text_frame = ttkb.Frame(log_card)
    log_text_frame.pack(fill=BOTH, expand=YES)

    # 垂直滚动条
    log_scroll_y = ttkb.Scrollbar(
        log_text_frame, orient="vertical", bootstyle="secondary"
    )
    log_scroll_y.pack(side=RIGHT, fill=Y)

    # 水平滚动条
    log_scroll_x = ttkb.Scrollbar(
        log_text_frame, orient="horizontal", bootstyle="secondary"
    )
    log_scroll_x.pack(side=BOTTOM, fill=X)

    # 日志文本框
    global log_text
    log_text = tk.Text(
        log_text_frame,
        wrap="word",  # 自动换行
        font=("Consolas", 8),
        bg="#1a1a1a",
        fg="#e0e0e0",
        insertbackground="blue",
        yscrollcommand=log_scroll_y.set,
        xscrollcommand=log_scroll_x.set,
        state="disabled",
        relief="flat",
        borderwidth=0,
    )
    log_text.pack(side=LEFT, fill=BOTH, expand=YES)

    # 配置滚动条
    log_scroll_y.config(command=log_text.yview)

    # 配置文本标签（颜色）
    log_text.tag_configure("error", foreground="#ff6b6b")  # 红色，错误信息
    log_text.tag_configure("warning", foreground="#ffd93d")  # 黄色，警告信息
    log_text.tag_configure("info", foreground="#4ecdc4")  # 青色，信息
    log_text.tag_configure("save", foreground="#1dd1a1")  # 绿色，保存成功
    log_text.tag_configure("init", foreground="#54a0ff")  # 蓝色，初始化
    log_text.tag_configure("status", foreground="#5f27cd")  # 紫色，状态变化
    log_text.tag_configure("fish", foreground="#ff9ff3")  # 粉色，钓鱼记录
    log_text.tag_configure("template", foreground="#f368e0")  # 紫红色，模板相关
    log_text.tag_configure("time", foreground="#54a0ff")  # 蓝色，时间信息
    log_text.tag_configure("screenshot", foreground="#ff9f43")  # 橙色，截图相关
    log_text.tag_configure("hint", foreground="#54a0ff")  # 蓝色，提示信息
    log_text.tag_configure("debug", foreground="#c8d6e5")  # 浅灰色，调试信息
    log_text.tag_configure("session", foreground="#00cec9")  # 青色，会话信息
    log_text.tag_configure("ocr", foreground="#a29bfe")  # 紫色，OCR相关

    # 定时更新日志显示
    def update_log_display_periodic():
        """定时更新运行日志显示"""
        try:
            if root.winfo_exists():
                update_log_display(log_text)
                # 更新日志行数显示
                line_count = int(log_text.index("end-1c").split(".")[0])
                log_count_var.set(f"日志行数: {line_count}")
                # 设置下次更新
                root.after(500, update_log_display_periodic)  # 每500ms更新一次
        except:
            pass  # 窗口关闭时忽略错误

    # 启动日志更新
    root.after(100, update_log_display_periodic)

    # 添加初始日志
    initial_log = "[系统] 运行日志界面已初始化，所有控制台输出将显示在此处"
    log_history.append(initial_log)
    print("📋 [系统] 运行日志界面已启动")

    # ==================== 操作按钮区域（左侧面板底部） ====================
    # 将按钮框架从可滚动区域移到左侧面板，使其固定显示
    btn_frame = ttkb.Frame(left_panel)
    btn_frame.pack(fill=X, padx=12, pady=(0, 8))

    # 使用网格布局实现更紧凑的按钮排列
    btn_frame.columnconfigure(0, weight=1)
    btn_frame.columnconfigure(1, weight=1)

    def update_and_refresh():
        """更新参数并刷新显示"""
        update_parameters(
            t_var,
            leftclickdown_var,
            leftclickup_var,
            times_var,
            paogantime_var,
            jiashi_var_option,
            resolution_var,
            custom_width_var,
            custom_height_var,
            hotkey_var,
            record_fish_var,
            legendary_screenshot_var,
            jitter_var=jitter_var,
            uno_hotkey_var_param=uno_hotkey_var,
            release_enabled_var=release_enabled_var,
            release_standard_var=release_standard_var,
            release_uncommon_var=release_uncommon_var,
            release_rare_var=release_rare_var,
            release_epic_var=release_epic_var,
            release_legendary_var=release_legendary_var,
            release_phantom_rare_var=release_phantom_rare_var,
        )
        resolution_info_var.set(f"当前: {TARGET_WIDTH}×{TARGET_HEIGHT}")
        hotkey_info_label.config(text=f"按 {hotkey_name} 启动/暂停 | 点击按钮修改")
        hotkey_btn.configure(text=hotkey_name)  # 更新热键按钮显示
        # 显示保存成功提示
        status_label.config(text="✅ 参数已保存", bootstyle="success")
        root.after(
            2000,
            lambda: status_label.config(
                text=f"按 {hotkey_name} 启动/暂停", bootstyle="light"
            ),
        )

    update_button = ttkb.Button(
        btn_frame,
        text="💾 保存设置",
        command=update_and_refresh,
        bootstyle="success",
        width=0,  # 让按钮自动扩展
    )
    update_button.grid(row=0, column=0, padx=2, pady=2, sticky="ew")

    # 调试按钮
    debug_button = ttkb.Button(
        btn_frame,
        text="🐛 调试",
        command=show_debug_window,
        bootstyle="warning-outline",
        width=0,  # 让按钮自动扩展
    )
    debug_button.grid(row=0, column=1, padx=2, pady=2, sticky="ew")

    # ==================== 状态栏（左侧面板底部） ====================
    status_frame = ttkb.Frame(left_panel)
    status_frame.pack(fill=X, pady=(8, 12), padx=12)

    separator = ttkb.Separator(status_frame, bootstyle="secondary")
    separator.pack(fill=X, pady=(0, 8))

    # 状态栏内容框架 - 使用pack布局
    status_content_frame = ttkb.Frame(status_frame)
    status_content_frame.pack(fill=X, expand=YES)

    # 左侧内容 - 使用pack布局
    left_status_frame = ttkb.Frame(status_content_frame)
    left_status_frame.pack(side=LEFT, fill=Y)

    status_label = ttkb.Label(
        left_status_frame,
        text=f"按 {hotkey_name} 启动/暂停",
        bootstyle="light",
        font=("Segoe UI", 9, "bold"),
    )
    status_label.pack(anchor="w")

    version_label = ttkb.Label(
        left_status_frame,
        text="v.2.12 | PartyFish",
        bootstyle="light",
        font=("Segoe UI", 8, "bold"),
    )
    version_label.pack(anchor="w", pady=(2, 0))

    # 右侧内容 - 使用pack布局
    right_status_frame = ttkb.Frame(status_content_frame)
    right_status_frame.pack(side=RIGHT, fill=Y, padx=(80, 0))

    dev_label = ttkb.Label(
        right_status_frame, text="by ", bootstyle="light", font=("Segoe UI", 9, "bold")
    )
    dev_label.pack(side=LEFT, padx=(0, 2))

    # 可点击的开发者链接
    dev_link = ttkb.Label(
        right_status_frame,
        text="开发者",
        bootstyle="light",
        cursor="hand2",
        font=("Segoe UI", 9, "bold"),
    )
    dev_link.pack(side=LEFT)

    # 开发者窗口引用，用于跟踪窗口是否已存在
    dev_window_instance = None

    # 开发者信息窗口函数
    def show_developers_window(event=None):
        """显示开发者信息窗口"""
        nonlocal dev_window_instance

        # 如果窗口已存在，激活它并返回
        if dev_window_instance and dev_window_instance.winfo_exists():
            dev_window_instance.lift()
            dev_window_instance.focus_force()
            return

        # 先定义open_github函数
        def open_github():
            """打开GitHub主页"""
            webbrowser.open("https://github.com/FADEDTUMI/PartyFish/")

        dev_window = tk.Toplevel(root)
        dev_window.title("开发者信息")
        dev_window.geometry("400x200")
        dev_window.resizable(False, False)

        # 设置窗口图标（与主窗口相同）
        set_window_icon(dev_window)

        # 保存窗口实例
        dev_window_instance = dev_window

        # 窗口关闭时重置实例
        def on_close():
            nonlocal dev_window_instance
            dev_window_instance = None
            dev_window.destroy()

        dev_window.protocol("WM_DELETE_WINDOW", on_close)

        # 创建内容框架
        content_frame = ttkb.Frame(dev_window, padding="20")
        content_frame.pack(fill=BOTH, expand=True)

        # 标题（可点击打开GitHub）
        title_label = ttkb.Label(
            content_frame,
            text="PartyFish 开发者",
            bootstyle="primary",
            font=("Helvetica", 16, "bold"),
            cursor="hand2",
        )
        title_label.pack(pady=(0, 20))
        title_label.bind("<Button-1>", lambda e: open_github())

        # 开发者列表
        developers = ["FadedTUMI", "PeiXiaoXiao", "MaiDong"]

        for dev in developers:
            dev_label = ttkb.Label(
                content_frame,
                text=f"• {dev}",
                bootstyle="light",
                font=("Helvetica", 12),
            )
            dev_label.pack(pady=5, anchor="w")

        # GitHub 链接按钮
        github_button = ttkb.Button(
            content_frame,
            text="访问 GitHub 仓库",
            bootstyle="success-outline",
            command=open_github,
        )
        github_button.pack(pady=(20, 0))

    dev_link.bind("<Button-1>", show_developers_window)

    # 鼠标悬停效果
    def on_enter(event):
        dev_link.configure(bootstyle="primary")

    def on_leave(event):
        dev_link.configure(bootstyle="light")

    dev_link.bind("<Enter>", on_enter)
    dev_link.bind("<Leave>", on_leave)

    # 应用保存的字体大小设置
    update_all_widget_fonts(root, style, font_size)

    # 在GUI初始化完成后，根据当前字体大小动态调整Treeview列宽
    # 确保程序启动时就能显示正确的列宽
    print(f"初始化后应用字体大小: {font_size}%")

    # 计算新的字体大小（像素单位）
    # 确保字体大小按照要求计算：
    # - 100% 时为 12px
    # - 150% 时为 18px
    # - 200% 时为 24px
    base_font_size = 12  # 基础字体大小为12px（100%时）
    new_font_size = int(base_font_size * (font_size / 100.0))

    # 精确调整字体大小，确保符合要求
    if font_size == 100:
        new_font_size = 12
    elif font_size == 150:
        new_font_size = 18
    elif font_size == 200:
        new_font_size = 24

    print(f"初始化时使用的字体大小: {new_font_size}px")

    # 调整比例，时间列与名称/重量列相同（时间:名称:品质:重量 = 63:63:36:63）
    # 动态计算初始列宽
    time_ratio = 63  # 时间列比例改为63，与名称/重量列一致
    name_ratio = 63
    quality_ratio = 36
    weight_ratio = 63
    total_ratio = time_ratio + name_ratio + quality_ratio + weight_ratio

    # 初始Treeview容器宽度，使用更小的估算值，让列宽更紧凑
    initial_container_width = 300  # 更小的初始估算宽度

    # 计算初始列宽
    column_widths = {
        "时间": int(initial_container_width * (time_ratio / total_ratio)),
        "名称": int(initial_container_width * (name_ratio / total_ratio)),
        "品质": int(initial_container_width * (quality_ratio / total_ratio)),
        "重量": int(initial_container_width * (weight_ratio / total_ratio)),
    }

    print(f"初始化时计算得到的列宽: {column_widths}")

    # 应用新列宽到Treeview
    if fish_tree_ref:
        for col, width in column_widths.items():
            fish_tree_ref.column(col, width=width, anchor="center")

        # 初始化设置行高
        new_rowheight = int(new_font_size * 2.2)  # 行高为字体大小的2.2倍
        # 尝试修改多种Treeview样式，确保覆盖所有可能的样式名称
        style.configure("Treeview", rowheight=new_rowheight)
        style.configure(
            "Info.Treeview", rowheight=new_rowheight
        )  # 对应bootstyle="info"
        style.configure(
            "Table.Treeview", rowheight=new_rowheight
        )  # ttkbootstrap默认Treeview样式
        style.configure(
            "CustomTreeview.Treeview", rowheight=new_rowheight
        )  # 自定义样式

        # 强制更新Treeview布局，确保列宽和行高调整立即生效
        fish_tree_ref.update_idletasks()

    # 主动触发一次窗口大小变化事件，确保初始列宽正确设置
    # 创建一个虚拟事件对象来传递
    class DummyEvent:
        def __init__(self, width):
            self.width = width

    # 调用窗口大小变化处理函数，确保初始列宽设置正确
    on_window_resize(DummyEvent(root.winfo_width()))

    # 运行 GUI
    root.mainloop()


# =========================
# =========================
# 常数 t 定义：定义时间间隔为 0.3 秒（可以根据需要调整）
t = 0.3  # 将时间间隔缩短，提高响应速度
# 常数 leftclickup 和 leftclickdown，用于调整按下去和抬起的时间
leftclickdown = 2.5  # 鼠标左键按下去的时间（秒）
leftclickup = 2  # 鼠标左键抬起的时间（秒）
times = 15  # 最大钓鱼拉杆次数
paogantime = 0.5
# =========================
# 分辨率设置（修改此处适配不同分辨率）
# =========================
# 基准分辨率：2560x1440 (2K)
BASE_WIDTH = 2560
BASE_HEIGHT = 1440
# 目标分辨率（修改为您的屏幕分辨率）
# 初始默认值，后续会更新为当前系统分辨率
TARGET_WIDTH = 2560
TARGET_HEIGHT = 1440

# 分辨率选择（用于GUI和保存）
resolution_choice = "current"

# 计算缩放比例
SCALE_X = TARGET_WIDTH / BASE_WIDTH
SCALE_Y = TARGET_HEIGHT / BASE_HEIGHT


def calculate_scale_factors():
    """
    计算缩放比例，考虑不同宽高比的情况
    游戏UI通常基于16:9设计，非16:9分辨率需要特殊处理
    支持1080P(16:9)、2K(16:9)、4K(16:9)、16:10以及21:9等非标准分辨率
    """
    global SCALE_X, SCALE_Y, SCALE_UNIFORM

    # 基准宽高比 (16:9)
    base_aspect = BASE_WIDTH / BASE_HEIGHT  # 约1.78
    # 目标宽高比
    target_aspect = TARGET_WIDTH / TARGET_HEIGHT

    # 计算基础缩放
    SCALE_X = TARGET_WIDTH / BASE_WIDTH
    SCALE_Y = TARGET_HEIGHT / BASE_HEIGHT

    # 对于模板匹配和UI元素定位，使用基于宽高比的统一缩放
    # 游戏UI通常会保持水平居中，垂直方向调整位置
    # 16:10(1.6)、21:9(2.33)等非16:9分辨率需要特殊处理
    # 使用基于高度的缩放，确保垂直方向元素正确显示
    # 这样可以确保UI元素在各种分辨率下都能保持正确的垂直位置和大小
    SCALE_UNIFORM = SCALE_Y

    # 对于特殊宽高比，记录调试信息
    if abs(target_aspect - base_aspect) > 0.05:
        aspect_ratio_str = f"{int(target_aspect*100)/100:.2f}:1"
        if abs(target_aspect - 2.33) < 0.1:
            aspect_ratio_str = "21:9"
        elif abs(target_aspect - 1.6) < 0.1:
            aspect_ratio_str = "16:10"

        # 使用调试系统记录宽高比变化信息
        debug_info = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "action": "aspect_ratio_change",
            "message": f"宽高比变化: 目标 {target_aspect:.2f} ({aspect_ratio_str})，基准 {base_aspect:.2f} (16:9)，统一缩放 {SCALE_UNIFORM:.2f}",
            "data": {
                "target_aspect": target_aspect,
                "aspect_ratio_str": aspect_ratio_str,
                "base_aspect": base_aspect,
                "scale_uniform": SCALE_UNIFORM,
            },
        }
        add_debug_info(debug_info)

    return SCALE_X, SCALE_Y, SCALE_UNIFORM


# 初始化统一缩放比例
# 与calculate_scale_factors函数逻辑保持一致
# 使用基于高度的缩放，确保垂直方向元素正确显示
SCALE_UNIFORM = SCALE_Y


def scale_coords(x, y, w, h):
    """根据分辨率缩放坐标"""
    return (int(x * SCALE_X), int(y * SCALE_Y), int(w * SCALE_X), int(h * SCALE_Y))


def scale_coords_uniform(x, y, w, h):
    """使用统一缩放比例缩放坐标（避免变形）"""
    return (
        int(x * SCALE_UNIFORM),
        int(y * SCALE_UNIFORM),
        int(w * SCALE_UNIFORM),
        int(h * SCALE_UNIFORM),
    )


def scale_point(x, y):
    """根据分辨率缩放单点坐标"""
    return (int(x * SCALE_X), int(y * SCALE_Y))


def scale_position(x, y, w=0, h=0, anchor="center", coordinate_type="point"):
    """
    统一的位置缩放函数，支持多种锚定方式和坐标类型

    Args:
        x: 基础X坐标
        y: 基础Y坐标
        w: 宽度（可选，用于区域或尺寸计算）
        h: 高度（可选，用于区域或尺寸计算）
        anchor: 锚定方式，可选值："center", "bottom_right", "top_left", "top_right", "bottom_left", "bottom_center", "top_center"
        coordinate_type: 坐标类型，可选值："point"（单点）, "region"（区域）

    Returns:
        根据coordinate_type返回不同结果：
        - "point": (scaled_x, scaled_y) 单点坐标
        - "region": (scaled_x1, scaled_y1, scaled_w, scaled_h) 区域坐标（与现有函数兼容）
    """
    if coordinate_type == "point":
        # 单点坐标处理
        if anchor == "center":
            # 中心锚定 - 使用统一缩放比例
            center_offset_x = x - BASE_WIDTH / 2
            center_offset_y = y - BASE_HEIGHT / 2
            scaled_x = int(TARGET_WIDTH / 2 + center_offset_x * SCALE_UNIFORM)
            scaled_y = int(TARGET_HEIGHT / 2 + center_offset_y * SCALE_UNIFORM)
            return (scaled_x, scaled_y)
        elif anchor == "bottom_right":
            # 右下角锚定
            offset_from_right = BASE_WIDTH - x
            offset_from_bottom = BASE_HEIGHT - y
            scale = SCALE_UNIFORM
            scaled_x = TARGET_WIDTH - int(offset_from_right * scale)
            scaled_y = TARGET_HEIGHT - int(offset_from_bottom * scale)
            return (scaled_x, scaled_y)
        elif anchor == "top_left":
            # 左上角锚定
            scale = SCALE_UNIFORM
            return (int(x * scale), int(y * scale))
        elif anchor == "top_right":
            # 右上角锚定
            offset_from_right = BASE_WIDTH - x
            scale = SCALE_UNIFORM
            scaled_x = TARGET_WIDTH - int(offset_from_right * scale)
            scaled_y = int(y * scale)
            return (scaled_x, scaled_y)
        elif anchor == "bottom_left":
            # 左下角锚定
            offset_from_bottom = BASE_HEIGHT - y
            scale = SCALE_UNIFORM
            scaled_x = int(x * scale)
            scaled_y = TARGET_HEIGHT - int(offset_from_bottom * scale)
            return (scaled_x, scaled_y)
        elif anchor == "bottom_center":
            # 底部中心锚定
            center_offset_x = x - BASE_WIDTH / 2
            offset_from_bottom = BASE_HEIGHT - y
            scale = SCALE_UNIFORM
            scaled_x = int(TARGET_WIDTH / 2 + center_offset_x * scale)
            scaled_y = TARGET_HEIGHT - int(offset_from_bottom * scale)
            return (scaled_x, scaled_y)
        elif anchor == "top_center":
            # 顶部中心锚定
            center_offset_x = x - BASE_WIDTH / 2
            scale = SCALE_UNIFORM
            scaled_x = int(TARGET_WIDTH / 2 + center_offset_x * scale)
            scaled_y = int(y * scale)
            return (scaled_x, scaled_y)
        else:
            # 默认使用普通缩放
            return (int(x * SCALE_X), int(y * SCALE_Y))
    else:
        # 区域坐标处理
        if anchor == "center":
            # 中心锚定 - 使用统一缩放比例
            center_offset_x = x - BASE_WIDTH / 2
            center_offset_y = y - BASE_HEIGHT / 2
            new_x = int(TARGET_WIDTH / 2 + center_offset_x * SCALE_UNIFORM)
            new_y = int(TARGET_HEIGHT / 2 + center_offset_y * SCALE_UNIFORM)
            new_w = int(w * SCALE_UNIFORM)
            new_h = int(h * SCALE_UNIFORM)
            return (new_x, new_y, new_w, new_h)
        elif anchor == "bottom_right":
            # 右下角锚定
            offset_from_right = BASE_WIDTH - x
            offset_from_bottom = BASE_HEIGHT - y
            scale = SCALE_UNIFORM
            new_x = TARGET_WIDTH - int(offset_from_right * scale)
            new_y = TARGET_HEIGHT - int(offset_from_bottom * scale)
            new_w = int(w * scale)
            new_h = int(h * scale)
            return (new_x, new_y, new_w, new_h)
        elif anchor == "top_left":
            # 左上角锚定
            scale = SCALE_UNIFORM
            return (int(x * scale), int(y * scale), int(w * scale), int(h * scale))
        elif anchor == "bottom_center":
            # 底部中心锚定
            center_offset_x = x - BASE_WIDTH / 2
            offset_from_bottom = BASE_HEIGHT - y
            scale = SCALE_UNIFORM
            new_x = int(TARGET_WIDTH / 2 + center_offset_x * scale)
            new_y = TARGET_HEIGHT - int(offset_from_bottom * scale)
            new_w = int(w * scale)
            new_h = int(h * scale)
            return (new_x, new_y, new_w, new_h)
        elif anchor == "top_center":
            # 顶部中心锚定
            center_offset_x = x - BASE_WIDTH / 2
            scale = SCALE_UNIFORM
            new_x = int(TARGET_WIDTH / 2 + center_offset_x * scale)
            new_y = int(y * scale)
            new_w = int(w * scale)
            new_h = int(h * scale)
            return (new_x, new_y, new_w, new_h)
        elif anchor == "uniform":
            # 统一缩放
            return scale_coords_uniform(x, y, w, h)
        else:
            # 默认使用普通缩放
            return scale_coords(x, y, w, h)


def scale_point_center_anchored(x, y):
    """使用中心锚定方式缩放单点坐标（适用于居中UI元素如加时按钮）
    兼容旧代码，调用统一的scale_position函数
    """
    return scale_position(x, y, anchor="center", coordinate_type="point")


def release_fish():
    """
    执行放生操作流程
    1. 按住C键
    2. 把鼠标移动到1090,720
    3. 松开C键
    4. 点击1090,720（左键）
    5. 点击1930,590（右键）
    6. 点击2030,764（左键）
    7. 按下ESC键
    """
    global release_fish_enabled, release_standard_enabled, release_uncommon_enabled, release_rare_enabled, release_epic_enabled, release_legendary_enabled
    global is_casting, is_releasing, operation_lock

    scr = None
    try:
        # 检查是否正在抛杆，如果是则等待
        with operation_lock:
            while is_casting:
                print("⏳ [提示] 正在抛杆，等待抛杆完成后再放生")
                time.sleep(0.5)
            # 设置放生状态
            is_releasing = True
        
        # 创建新的截图对象，确保每次都是新鲜的
        scr = mss.mss()
        
        # 1. 将鼠标移动到屏幕中心，确保窗口焦点（不点击）
        screen_width, screen_height = get_current_screen_resolution()
        center_x = screen_width // 2
        center_y = screen_height // 2
        mouse_controller.position = (center_x, center_y)
        time.sleep(0.3)
        
        # 2. 按住C键 - 提高可靠性
        c_key = keyboard.KeyCode.from_char("c")
        keyboard_controller.press(c_key)
        time.sleep(0.1)  # 短暂延迟确保按键被按下
        
        # 再次按下确保按键状态正确
        keyboard_controller.press(c_key)
        time.sleep(1)

        # 2. 识别 tong_gray.png 在区域 (1042,675,89,79)
        # 缩放识别区域
        scaled_x, scaled_y, scaled_w, scaled_h = scale_position(
            1042, 675, 89, 79, anchor="center", coordinate_type="region"
        )
        # 添加标志变量，跟踪是否识别到桶
        tong_detected = False
        
        # 截取指定区域
        region_gray = capture_region(scaled_x, scaled_y, scaled_w, scaled_h, scr)
        if region_gray is not None:
            # 加载 tong_gray.png 模板
            tong_template_path = os.path.join(template_folder_path, "tong_gray.png")
            if os.path.exists(tong_template_path):
                img = Image.open(tong_template_path)
                tong_template = np.array(img)
                scale = SCALE_UNIFORM  # 使用统一缩放比例
                tong_template = scale_template(tong_template, scale, scale)
                # 进行模板匹配
                res = cv2.matchTemplate(region_gray, tong_template, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
                if max_val > 0.8:  # 匹配度大于0.8认为匹配成功
                    tong_detected = True
                    # 4. 点击1090,720（左键）
                    scaled_click_x, scaled_click_y = scale_position(
                        1090, 720, anchor="center", coordinate_type="point"
                    )
                    mouse_controller.position = (scaled_click_x, scaled_click_y)
                    time.sleep(0.3)
                    mouse_controller.click(mouse.Button.left, 1)
                    time.sleep(0.3)
        time.sleep(0.5)

        # 3. 松开C键 - 提高可靠性
        keyboard_controller.release(c_key)
        time.sleep(0.1)  # 短暂延迟确保按键被释放
        
        # 再次释放确保按键状态正确
        keyboard_controller.release(c_key)
        time.sleep(0.5)


        # 只有识别到桶时才执行后续操作
        if tong_detected:
            # 4. 点击1930,590（右键） - 使用右下角锚定，更适合屏幕右侧元素
            scaled_x2, scaled_y2 = scale_position(
                1930, 590, anchor="bottom_right", coordinate_type="point"
            )
            mouse_controller.position = (scaled_x2, scaled_y2)
            time.sleep(0.3)
            mouse_controller.click(mouse.Button.right, 1)
            time.sleep(0.3)

            # 5. 点击2030,764（左键） - 使用右下角锚定，更适合屏幕右侧元素
            scaled_x3, scaled_y3 = scale_position(
                2030, 764, anchor="bottom_right", coordinate_type="point"
            )
            mouse_controller.position = (scaled_x3, scaled_y3)
            time.sleep(0.3)
            mouse_controller.click(mouse.Button.left, 1)
            time.sleep(0.3)

            # 6. 按下ESC键退出
            keyboard_controller.tap(keyboard.Key.esc)  # 使用tap方法，自动处理按下和释放
            time.sleep(0.5)  # 按下后等待
        else:
            print("❌ [识别] 未识别到桶，跳过后续操作")

        if tong_detected:
            print("✅ [放生] 放生操作执行成功")
            return True
        else:
            print("❌ [放生] 未识别到桶，放生操作失败")
            return False
    except Exception as e:
        print(f"❌ [放生] 放生操作执行失败: {e}")
        # 确保C键被释放
        keyboard_controller.release(keyboard.KeyCode.from_char("c"))
        return False
    finally:
        # 无论是否异常，都要重置放生状态
        with operation_lock:
            is_releasing = False
        
        # 确保scr对象被正确关闭
        if scr is not None:
            try:
                scr.close()
            except:
                pass


def should_release_fish(quality, fish_name=""):
    """
    根据鱼的品质和名称判断是否需要放生

    Args:
        quality: 鱼的品质（标准、非凡、稀有、史诗、传奇）
        fish_name: 鱼的名称

    Returns:
        bool: 是否需要放生
    """
    global release_standard_enabled, release_uncommon_enabled, release_rare_enabled, release_epic_enabled, release_legendary_enabled, release_phantom_rare_enabled

    # 处理品质名称，统一转换为标准格式
    quality = (
        quality.replace("標準", "标准")
               .replace("傳奇", "传奇")
               .replace("史詩", "史诗")
               .replace("传说", "传奇")  # 合并传说和传奇为同一品质
    )

    # 高品质鱼（史诗、传奇）直接返回False，不允许放生
    if quality in ["史诗", "传奇"]:
        return False

    # 幻神稀有鱼列表
    phantom_rare_fishes = ["地包天鱼", "黄鸭叫", "辐射鲈", "鬼刀鱼", "鬼虎鱼", "鬼牙鱼", "芭蕃蓬蓬鱼", "幻光鱼", "甲方满意鱼", "蓝眼泪", "飞机头", "鳅鳅鱼", "拟岩鱼", "粗红线", "水法老", "大罐子鱼", "粉丝虾", "狼蛛蟹", "金蛙", "拳击虾", "大师龟"]
    
    # 检查是否是幻神稀有鱼
    if fish_name in phantom_rare_fishes and release_phantom_rare_enabled:
        return True
    elif quality == "标准" and release_standard_enabled:
        return True
    elif quality == "非凡" and release_uncommon_enabled:
        return True
    elif quality == "稀有" and release_rare_enabled:
        return True

    return False


def scale_corner_anchored(base_x, base_y, base_w, base_h, anchor="bottom_right"):
    """
    缩放锚定在角落的UI元素坐标
    游戏UI（如鱼饵数量）通常锚定在屏幕角落而不是按比例缩放

    兼容旧代码，调用统一的scale_position函数

    anchor: "bottom_right", "top_left", "center" 等
    """
    return scale_position(
        base_x, base_y, base_w, base_h, anchor=anchor, coordinate_type="region"
    )


def scale_coords_bottom_anchored(base_x, base_y, base_w, base_h):
    """
    缩放锚定在底部中央的UI元素坐标
    游戏UI（如F1/F2按钮）通常锚定在屏幕底部中央

    兼容旧代码，调用统一的scale_position函数
    """
    return scale_position(
        base_x, base_y, base_w, base_h, anchor="bottom_center", coordinate_type="region"
    )


def scale_coords_center_anchored(base_x, base_y, base_w, base_h):
    """
    使用中心锚定方式缩放区域坐标（适用于居中UI元素如加时检测区域）

    兼容旧代码，调用统一的scale_position函数
    """
    return scale_position(
        base_x, base_y, base_w, base_h, anchor="center", coordinate_type="region"
    )


# =========================
# 加时功能专用缩放函数
# =========================
def jiashi_scale_point(x, y):
    """加时功能专用的单点缩放函数"""
    # 使用全局统一缩放比例
    return (int(x * SCALE_UNIFORM), int(y * SCALE_UNIFORM))


def jiashi_scale_region(x, y, w, h):
    """加时功能专用的区域缩放函数"""
    # 使用全局统一缩放比例
    return (
        int(x * SCALE_UNIFORM),
        int(y * SCALE_UNIFORM),
        int(w * SCALE_UNIFORM),
        int(h * SCALE_UNIFORM),
    )


def jiashi_scale_point_center_anchored(x, y):
    """加时功能专用的中心锚定单点缩放函数"""
    # 使用全局统一缩放比例
    return scale_position(x, y, anchor="center", coordinate_type="point")


def jiashi_scale_coords_center_anchored(x, y, w, h):
    """加时功能专用的中心锚定区域缩放函数"""
    # 使用全局统一缩放比例
    return scale_position(x, y, w, h, anchor="center", coordinate_type="region")


def scale_coords_top_center(base_x, base_y, base_w, base_h):
    """
    缩放锚定在顶部中央的UI元素坐标（如钓鱼星星）
    """
    scale = SCALE_UNIFORM
    # X坐标：居中元素按中心点缩放
    center_offset_x = base_x - BASE_WIDTH / 2
    new_x = int(TARGET_WIDTH / 2 + center_offset_x * scale)
    # Y坐标：锚定在顶部
    new_y = int(base_y * scale)
    new_w = int(base_w * scale)
    new_h = int(base_h * scale)
    return (new_x, new_y, new_w, new_h)


def get_jiashi_region_by_resolution():
    """
    根据当前分辨率返回对应的加时识别区域
    返回: (x, y, w, h) 元组
    """
    # 获取当前屏幕分辨率
    screen_width, screen_height = get_current_screen_resolution()
    
    # 定义分辨率到识别区域的映射字典
    resolution_map = {
        (1920, 1080): (933, 505, 22, 22),
        (2560, 1440): (1244, 674, 29, 29),
        (2560, 1600): (1244, 754, 29, 29),
        (3840, 2160): (1865, 1012, 43, 43)
    }
    
    # 根据当前分辨率返回对应的识别区域
    if (screen_width, screen_height) in resolution_map:
        return resolution_map[(screen_width, screen_height)]
    else:
        # 如果没有匹配的分辨率，使用默认的缩放逻辑
        return scale_position(
            *JIASHI_REGION_BASE, anchor="center", coordinate_type="region"
        )


def update_region_coords():
    """
    根据当前缩放比例更新所有区域坐标
    """
    global region3_coords, region4_coords, region5_coords, region6_coords, jiashi_region_coords, btn_no_jiashi_coords, btn_yes_jiashi_coords
    # 先计算最新的缩放比例，确保适配当前分辨率
    calculate_scale_factors()
    # 上鱼星星 - 顶部中央区域
    region3_coords = scale_coords_top_center(1172, 165, 34, 34)
    # F1位置 - 底部中央区域
    region4_coords = scale_coords_bottom_anchored(1100, 1329, 10, 19)
    # F2位置 - 底部中央区域
    region5_coords = scale_coords_bottom_anchored(1212, 1329, 10, 19)
    # 上鱼右键 - 底部中央区域
    region6_coords = scale_coords_bottom_anchored(1146, 1316, 17, 21)
    # 加时界面检测区域 - 根据分辨率使用预设值
    jiashi_region_coords = get_jiashi_region_by_resolution()
    # 加时按钮坐标 - 使用底部中心锚定，与识别区域保持一致
    btn_no_jiashi_coords = scale_position(
        *BTN_NO_JIASHI_BASE, anchor="bottom_center", coordinate_type="point"
    )
    btn_yes_jiashi_coords = scale_position(
        *BTN_YES_JIASHI_BASE, anchor="bottom_center", coordinate_type="point"
    )
    # 当坐标更新时，检查是否需要重新加载模板
    reload_templates_if_scale_changed()


# =========================
# 参数设置
# =========================
template_folder_path = get_resources_path()

# =========================
# 鱼饵识别算法配置
# =========================
bait_recognition_algorithm = "template"  # 默认使用模板匹配算法
bait_recognition_algorithms = {
    "template": "模板匹配算法",
    "ocr": "OCR识别算法",
    "contour": "轮廓特征算法",
    "pixel": "像素统计算法",
}


# =========================
# 鱼饵识别器类
# =========================
class BaitRecognizer:
    """
    鱼饵识别器类，支持多种识别算法
    """

    def __init__(self):
        """初始化鱼饵识别器"""
        # 初始化模板（如果使用模板匹配算法）
        self.templates = []
        self._load_templates()

    def _load_templates(self):
        """加载数字模板"""
        # 这里可以根据实际情况加载模板
        # 由于模板匹配算法需要实际的模板文件，这里简化处理
        pass

    def recognize(self, image, algorithm="template"):
        """
        使用指定算法识别鱼饵数量

        Args:
            image: 截取的鱼饵区域图像（RGBA格式的NumPy数组）
            algorithm: 使用的识别算法，可选值："template", "ocr", "contour", "pixel"

        Returns:
            int: 识别出的鱼饵数量，如果识别失败则返回None
        """
        if image is None:
            return None

        # 转换为灰度图像
        gray_img = cv2.cvtColor(image, cv2.COLOR_RGBA2GRAY)

        # 根据选择的算法进行识别
        if algorithm == "template":
            return self._recognize_template(gray_img)
        elif algorithm == "ocr":
            return self._recognize_ocr(image)
        elif algorithm == "contour":
            return self._recognize_contour(gray_img)
        elif algorithm == "pixel":
            return self._recognize_pixel(gray_img)
        else:
            # 默认使用模板匹配算法
            return self._recognize_template(gray_img)

    def _recognize_template(self, gray_img):
        """
        使用模板匹配算法识别鱼饵数量

        Args:
            gray_img: 灰度图像

        Returns:
            int: 识别出的鱼饵数量，如果识别失败则返回None
        """
        # 根据统一缩放比例动态计算裁切尺寸
        scale = SCALE_UNIFORM
        crop_h = max(1, int(BAIT_CROP_HEIGHT_BASE * scale))
        crop_w = max(1, int(BAIT_CROP_WIDTH1_BASE * scale))

        # 确保不超出图像边界
        img_h, img_w = gray_img.shape[:2]
        crop_h = min(crop_h, img_h)
        crop_w = min(crop_w, img_w // 2)  # 确保单个数字宽度不超过一半

        # 初始化匹配结果
        best_match1 = None
        best_match2 = None
        best_match3 = None

        # 截取并处理区域1（第一个数字）
        if crop_w <= img_w:
            region1 = gray_img[0:crop_h, 0:crop_w]
            best_match1 = match_digit_template(region1)

        # 截取并处理区域2（第二个数字）
        if crop_w * 2 <= img_w:
            region2 = gray_img[0:crop_h, crop_w : crop_w * 2]
            best_match2 = match_digit_template(region2)

        # 单个数字居中区域 - 动态计算起始位置，适应各种分辨率
        mid_start = max(0, (img_w - crop_w) // 2)
        mid_end = min(mid_start + crop_w, img_w)
        region3 = gray_img[0:crop_h, mid_start:mid_end]
        best_match3 = match_digit_template(region3)

        if best_match1 and best_match2:
            # 从best_match中提取数字索引（i），并拼接成整数
            best_match1_val = best_match1[0]  # 提取区域1的数字索引
            best_match2_val = best_match2[0]  # 提取区域2的数字索引
            # 拼接两个匹配的数字，转换为整数
            return int(f"{best_match1_val}{best_match2_val}")
        elif best_match3:
            return int(f"{best_match3[0]}")
        else:
            return None

    def _match_digit_template(self, image):
        """匹配数字模板

        Args:
            image: 待匹配的图像

        Returns:
            tuple: (匹配的数字索引, 匹配位置)，如果匹配失败则返回None
        """
        best_match = None  # 最佳匹配信息
        best_val = 0  # 存储最佳匹配度

        # 这里应该使用实际的模板，目前简化处理
        # 实际实现中应该加载预定义的数字模板
        for i in range(10):
            # 简化处理，假设模板匹配成功
            # 实际实现中应该使用cv2.matchTemplate进行匹配
            pass

        # 这里返回None表示需要使用实际模板才能进行匹配
        # 实际实现中应该返回最佳匹配结果
        return None

    def _recognize_ocr(self, image):
        """
        使用OCR算法识别鱼饵数量

        Args:
            image: 原始图像

        Returns:
            int: 识别出的鱼饵数量，如果识别失败则返回None
        """
        if not OCR_AVAILABLE or ocr_engine is None:
            return None

        try:
            # 将RGBA图像转换为RGB
            img_rgb = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
            # 使用OCR识别文本
            result = ocr_engine(img_rgb)

            if result and len(result) > 0:
                for line in result:
                    text = line[1][0]
                    # 提取数字
                    digits = re.findall(r"\d+", text)
                    if digits:
                        return int(digits[0])
        except Exception as e:
            if debug_mode:
                print(f"⚠️  [OCR] 识别失败: {e}")
        return None

    def _recognize_contour(self, gray_img):
        """
        使用轮廓特征算法识别鱼饵数量

        Args:
            gray_img: 灰度图像

        Returns:
            int: 识别出的鱼饵数量，如果识别失败则返回None
        """
        try:
            # 二值化处理
            _, thresh = cv2.threshold(
                gray_img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
            )
            # 查找轮廓
            contours, _ = cv2.findContours(
                thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            # 过滤小轮廓
            valid_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > 10]

            # 根据轮廓数量和特征识别数字
            # 这里简化处理，实际实现中应该根据轮廓特征进行更复杂的判断
            if len(valid_contours) == 1:
                # 可能是单个数字
                return 1
            elif len(valid_contours) == 2:
                # 可能是两个数字
                return 2
        except Exception as e:
            if debug_mode:
                print(f"⚠️  [轮廓识别] 识别失败: {e}")
        return None

    def _recognize_pixel(self, gray_img):
        """
        使用像素统计算法识别鱼饵数量

        Args:
            gray_img: 灰度图像

        Returns:
            int: 识别出的鱼饵数量，如果识别失败则返回None
        """
        try:
            # 计算非零像素数量
            non_zero_count = cv2.countNonZero(gray_img)
            # 计算总像素数量
            total_count = gray_img.shape[0] * gray_img.shape[1]
            # 计算非零像素比例
            ratio = non_zero_count / total_count

            # 根据比例识别数字
            # 这里简化处理，实际实现中应该根据实际情况调整阈值
            if ratio < 0.1:
                return 0
            elif ratio < 0.2:
                return 1
            elif ratio < 0.3:
                return 2
            elif ratio < 0.4:
                return 3
            elif ratio < 0.5:
                return 4
            elif ratio < 0.6:
                return 5
            elif ratio < 0.7:
                return 6
            elif ratio < 0.8:
                return 7
            elif ratio < 0.9:
                return 8
            else:
                return 9
        except Exception as e:
            if debug_mode:
                print(f"⚠️  [像素统计] 识别失败: {e}")
        return None


# 创建全局鱼饵识别器实例
bait_recognizer = BaitRecognizer()

# =========================
# 钓鱼记录系统
# =========================
FISH_RECORD_FILE = "./fish_records.txt"

# 鱼信息识别区域（2K分辨率基准值）
FISH_INFO_REGION_BASE = (915, 75, 1640, 225)  # 左上角x, y, 右下角x, y

# 品质等级定义（包含"传奇"的别名，部分游戏版本可能使用不同名称）
QUALITY_LEVELS = [
    "标准",
    "非凡",
    "稀有",
    "史诗",
    "史詩",
    "传奇",
    "標準",
    "傳奇",
    "傅奇",
]
# GUI专用品质列表，不包含"传奇"选项，避免在GUI筛选中显示
GUI_QUALITY_LEVELS = ["标准", "非凡", "稀有", "史诗", "传奇"]
QUALITY_COLORS = {
    # 将标准和繁体标准合并为同一图标配置
    **{q: "⚪" for q in ["标准", "標準"]},
    "非凡": "🟢",
    "稀有": "🔵",
    **{q: "🟣" for q in ["史詩", "史诗"]},
    # 将传奇、傳奇、傅奇合并为同一图标配置
    **{q: "🟡" for q in ["传奇", "傳奇", "傅奇"]},  # 传奇与傳奇、傅奇同级，使用相同图标
}

# 当前会话数据
current_session_id = None
current_session_fish = []  # 当前会话钓到的鱼
all_fish_records = []  # 所有钓鱼记录（从文件加载）
fish_record_lock = threading.Lock()  # 钓鱼记录锁

# GUI更新回调（将在create_gui中设置）
gui_fish_update_callback = None


class FishRecord:
    """单条鱼的记录"""

    def __init__(self, name, quality, weight):
        self.name = name if name else "未知"
        self.quality = quality if quality in QUALITY_LEVELS else "标准"
        self.weight = weight if weight else "0"
        self.timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.session_id = current_session_id

    def to_dict(self):
        return {
            "name": self.name,
            "quality": self.quality,
            "weight": self.weight,
            "timestamp": self.timestamp,
            "session_id": self.session_id,
        }

    def to_line(self):
        """转换为文件存储格式"""
        return f"{self.session_id}|{self.timestamp}|{self.name}|{self.quality}|{self.weight}\n"

    @staticmethod
    def from_line(line):
        """从文件行解析"""
        try:
            parts = line.strip().split("|")
            if len(parts) >= 5:
                record = FishRecord.__new__(FishRecord)
                record.session_id = parts[0]
                record.timestamp = parts[1]
                record.name = parts[2]
                record.quality = parts[3]
                record.weight = parts[4]
                return record
        except:
            pass
        return None


def save_fish_record(fish_record):
    """保存单条钓鱼记录到文件"""
    try:
        with open(FISH_RECORD_FILE, "a", encoding="utf-8") as f:
            f.write(fish_record.to_line())
    except Exception as e:
        print(f"❌ [错误] 保存钓鱼记录失败: {e}")


def load_all_fish_records():
    """加载所有历史钓鱼记录"""
    global all_fish_records
    all_fish_records = []
    try:
        if os.path.exists(FISH_RECORD_FILE):
            with open(FISH_RECORD_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        record = FishRecord.from_line(line)
                        if record:
                            all_fish_records.append(record)
            print(f"📊 [信息] 已加载 {len(all_fish_records)} 条历史钓鱼记录")
    except Exception as e:
        print(f"❌ [错误] 加载钓鱼记录失败: {e}")


def start_new_session():
    """开始新的钓鱼会话"""
    global current_session_id, current_session_fish
    current_session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    current_session_fish = []
    print(f"🎣 [会话] 新钓鱼会话开始: {current_session_id}")


def end_current_session():
    """结束当前钓鱼会话"""
    global current_session_id, current_session_fish
    if current_session_fish:
        print(f"📊 [会话] 本次钓鱼结束，共钓到 {len(current_session_fish)} 条鱼")
        # 统计品质
        quality_count = {}
        for fish in current_session_fish:
            quality_count[fish.quality] = quality_count.get(fish.quality, 0) + 1
        for q, count in quality_count.items():
            emoji = QUALITY_COLORS.get(q, "⚪")
            print(f"   {emoji} {q}: {count} 条")
    current_session_id = None


def capture_fish_info_region(scr_param=None):
    """截取鱼信息区域的图像

    Args:
        scr_param: 截图对象，如果为None则使用全局scr对象

    Returns:
        img_rgb: RGB格式的鱼信息区域图像，如果截取失败则返回None
    """
    global scr
    # 优先使用传入的scr_param，如果为None则使用全局scr
    current_scr = scr_param if scr_param is not None else scr

    if current_scr is None:
        # 调试信息：记录错误
        if debug_mode:
            debug_info = {
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[
                    :-3
                ],
                "action": "capture_error",
                "error": "截图对象未初始化",
                "scr_source": "传入参数" if scr_param is not None else "全局对象",
            }
            add_debug_info(debug_info)
        return None

    # 根据分辨率缩放坐标
    x1, y1, x2, y2 = FISH_INFO_REGION_BASE
    region = (
        int(x1 * SCALE_X),
        int(y1 * SCALE_Y),
        int(x2 * SCALE_X),
        int(y2 * SCALE_Y),
    )

    try:
        frame = current_scr.grab(region)
        if frame is None:
            # 调试信息：记录错误
            if debug_mode:
                debug_info = {
                    "timestamp": datetime.datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S.%f"
                    )[:-3],
                    "region": {
                        "x1": region[0],
                        "y1": region[1],
                        "x2": region[2],
                        "y2": region[3],
                        "width": region[2] - region[0],
                        "height": region[3] - region[1],
                    },
                    "action": "capture_error",
                    "error": "截取图像失败",
                    "scr_source": "传入参数" if scr_param is not None else "全局对象",
                }
                add_debug_info(debug_info)
            return None
        img = np.array(frame)
        # 转换为RGB格式（OCR需要）
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)

        # 调试信息：记录截取区域
        if debug_mode:
            debug_info = {
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[
                    :-3
                ],
                "region": {
                    "x1": region[0],
                    "y1": region[1],
                    "x2": region[2],
                    "y2": region[3],
                    "width": region[2] - region[0],
                    "height": region[3] - region[1],
                },
                "action": "capture_region",
                "message": "成功截取鱼信息区域",
                "scr_source": "传入参数" if scr_param is not None else "全局对象",
            }
            add_debug_info(debug_info)

        return img_rgb
    except Exception as e:
        print(f"❌ [错误] 截取鱼信息区域失败: {e}")
        # 调试信息：记录错误
        if debug_mode:
            debug_info = {
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[
                    :-3
                ],
                "region": {
                    "x1": region[0],
                    "y1": region[1],
                    "x2": region[2],
                    "y2": region[3],
                    "width": region[2] - region[0],
                    "height": region[3] - region[1],
                },
                "action": "capture_error",
                "error": str(e),
                "scr_source": "传入参数" if scr_param is not None else "全局对象",
            }
            add_debug_info(debug_info)
        return None


def recognize_fish_info_ocr(img):
    """使用OCR识别鱼的信息"""
    if not OCR_AVAILABLE or ocr_engine is None:
        # 调试信息：记录错误
        if debug_mode:
            debug_info = {
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[
                    :-3
                ],
                "action": "ocr_error",
                "error": "OCR引擎不可用",
            }
            add_debug_info(debug_info)
        return None, None, None

    if img is None:
        # 调试信息：记录错误
        if debug_mode:
            debug_info = {
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[
                    :-3
                ],
                "action": "ocr_error",
                "error": "输入图像为空",
            }
            add_debug_info(debug_info)
        return None, None, None

    try:
        # 执行OCR识别
        result, elapse = ocr_engine(img)

        # 确保result是列表类型
        if result is None:
            result = []

        # 合并所有识别到的文本
        full_text = ""
        for line in result:
            if isinstance(line, list) and len(line) >= 2:
                full_text += line[1] + " "

        full_text = full_text.strip()

        # 解析鱼的信息
        fish_name = None
        fish_quality = None
        fish_weight = None
        is_first_capture = False

        if len(result) > 0 and full_text:
            # 识别品质
            for quality in QUALITY_LEVELS:
                if quality in full_text:
                    fish_quality = quality
                    break

            # 识别重量（匹配数字+kg或g的模式，支持简繁体）
            weight_pattern = r"(\d+\.?\d*)\s*(kg|g|千克|克|公斤|KG|G)?"
            weight_matches = re.findall(weight_pattern, full_text, re.IGNORECASE)
            if weight_matches:
                # 取最后一个匹配的数字作为重量
                for match in weight_matches:
                    if match[0]:
                        fish_weight = match[0]
                        unit = match[1].lower() if match[1] else "kg"
                        if unit in ["g", "克", "g"]:
                            fish_weight = str(float(fish_weight) / 1000)
                        fish_weight = f"{float(fish_weight):.2f}kg"

            # 识别鱼名 - 优先匹配"你钓到了XXX"或"首次捕获XXX"格式（支持简繁体）
            # 优化正则表达式，处理OCR可能将"钓"识别为"约"的情况
            fish_name_patterns = [
                r"(?:你?[钓釣約]到了|首次?捕[获獲])\s*[「【\[]?\s*(.+?)\s*[」】\]]?\s*(?:[标標][准準]|非凡|稀有|史[诗詩]|传奇|傳奇|[傳傅]奇)?$"
            ]

            for pattern in fish_name_patterns:
                match = re.search(pattern, full_text)
                if match:
                    # 检查是否是首次捕获
                    if "首次" in match.group(0) or "首次" in full_text:
                        is_first_capture = True
                    
                    extracted_name = match.group(1).strip()
                    # 清理鱼名中的数字、单位和特殊字符
                    extracted_name = re.sub(
                        r"\d+\.?\d*\s*(kg|g|千克|克|公斤|KG|G)?",
                        "",
                        extracted_name,
                        flags=re.IGNORECASE,
                    )
                    # 清理鱼名中可能包含的品质词
                    for quality in QUALITY_LEVELS:
                        if quality in extracted_name:
                            extracted_name = extracted_name.replace(quality, " ")
                    # 清理鱼名中的多余字符，保留中文和英文
                    extracted_name = re.sub(
                        r"[^\u4e00-\u9fff\uf900-\ufaffa-zA-Z\s]",
                        "",
                        extracted_name,
                    )
                    # 移除多余空格，只保留必要的空格
                    extracted_name = re.sub(r"\s+", " ", extracted_name).strip()
                    # 移除单个字符（可能是OCR误识别）
                    if extracted_name:
                        words = extracted_name.split()
                        filtered_words = [word for word in words if len(word) > 1 or word in ["a", "A"]]
                        extracted_name = " ".join(filtered_words).strip()
                    if extracted_name and len(extracted_name) >= 2:
                        fish_name = extracted_name
                        # 特别处理美髯公，确保能被正确识别
                        cleaned_fish_name = fish_name.replace(" ", "")
                if "美髯公" in cleaned_fish_name or (
                    ("美" in cleaned_fish_name)
                    and ("公" in cleaned_fish_name)
                    and len(cleaned_fish_name) <= 3
                ):
                    fish_name = "美髯公"
                break

            # 如果上述模式都没匹配到，尝试备用方案
            if not fish_name:
                name_text = full_text
                # 移除常见前缀（支持简繁体）
                prefixes_to_remove = [r"你?[钓釣約](?:到了|到)|(?:首次)?捕[获獲]"]
                for prefix in prefixes_to_remove:
                    name_text = name_text.replace(prefix, " ")
                # 移除所有品质词
                for quality in QUALITY_LEVELS:
                    name_text = name_text.replace(quality, " ")
                # 移除数字和单位
                name_text = re.sub(
                    r"\d+\.?\d*\s*(kg|g|千克|克|公斤|KG|G)?",
                    "",
                    name_text,
                    flags=re.IGNORECASE,
                )
                # 清理特殊字符，保留中文和英文（包括繁体）
                name_text = re.sub(
                    r"[^\u4e00-\u9fff\uf900-\ufaffa-zA-Z\s]",
                    " ",
                    name_text,
                )
                # 移除多余空格
                name_text = re.sub(r"\s+", " ", name_text).strip()
                # 移除单个字符（可能是OCR误识别）
                if name_text:
                    words = name_text.split()
                    filtered_words = [word for word in words if len(word) > 1 or word in ["a", "A"]]
                    name_text = " ".join(filtered_words).strip()

                # 改进的鱼名提取逻辑
                # 1. 尝试直接使用清理后的文本作为鱼名
                if name_text and len(name_text) >= 2:
                    fish_name = name_text
                    # 特别处理美髯公，确保能被正确识别
                    cleaned_fish_name = fish_name.replace(" ", "")
                    if "美髯公" in cleaned_fish_name or (
                        ("美" in cleaned_fish_name)
                        and ("公" in cleaned_fish_name)
                        and len(cleaned_fish_name) <= 3
                    ):
                        fish_name = "美髯公"

                # 2. 如果直接使用不行，尝试提取连续的中文词
                if not fish_name:
                    # 取最长的连续中文词作为鱼名（支持繁体）
                    chinese_words = re.findall(r"[\u4e00-\u9fff]{2,}", name_text)
                    if chinese_words:
                        # 选择最长的词作为鱼名
                        fish_name = max(chinese_words, key=len)
                        # 特别处理美髯公，确保能被正确识别
                        cleaned_fish_name = fish_name.replace(" ", "")
                        if "美髯公" in cleaned_fish_name or (
                            ("美" in cleaned_fish_name)
                            and ("公" in cleaned_fish_name)
                            and len(cleaned_fish_name) <= 3
                        ):
                            fish_name = "美髯公"

            # 如果还是没匹配到，尝试直接从完整文本中提取鱼名
            if not fish_name:
                # 移除品质词和重量
                clean_text = full_text
                for quality in QUALITY_LEVELS:
                    clean_text = clean_text.replace(quality, " ")
                # 移除数字和单位
                weight_pattern = r"\d+\.?\d*\s*(kg|g|千克|克|公斤|KG|G)?"
                clean_text = re.sub(weight_pattern, "", clean_text, flags=re.IGNORECASE)
                # 移除前缀
                for prefix in prefixes_to_remove:
                    clean_text = clean_text.replace(prefix, " ")
                # 清理特殊字符
                clean_text = re.sub(
                    r"[^\u4e00-\u9fff\uf900-\ufaffa-zA-Z\s]",
                    " ",
                    clean_text,
                )
                # 移除多余空格
                clean_text = re.sub(r"\s+", " ", clean_text).strip()
                # 移除单个字符（可能是OCR误识别）
                if clean_text:
                    words = clean_text.split()
                    filtered_words = [word for word in words if len(word) > 1 or word in ["a", "A"]]
                    clean_text = " ".join(filtered_words).strip()
                # 直接使用清理后的文本作为鱼名（如果长度合适）
                if clean_text and len(clean_text) >= 2:
                    fish_name = clean_text
                    # 特别处理美髯公，确保能被正确识别
                    cleaned_fish_name = fish_name.replace(" ", "")
                    # 特别处理各种鱼名，确保能被正确识别
                    if "美髯公" in cleaned_fish_name or (
                        ("美" in cleaned_fish_name)
                        and ("公" in cleaned_fish_name)
                        and len(cleaned_fish_name) <= 3
                    ):
                        fish_name = "美髯公"

        # 调试信息：记录OCR识别结果和详细的鱼信息识别
        if debug_mode:
            # 基本OCR识别结果日志
            debug_info = {
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[
                    :-3
                ],
                "action": "ocr_recognize",
                "message": "鱼信息OCR识别完成",
                "ocr_result": result,
                "full_text": full_text,
                "elapse": elapse,
                "image_shape": img.shape if img is not None else "无图像",
                "result_count": len(result),
                "has_text": bool(full_text),
            }
            add_debug_info(debug_info)

            # 详细的鱼信息识别日志
            debug_info = {
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[
                    :-3
                ],
                "action": "fish_info_recognition_complete",
                "message": "鱼信息识别完整流程完成",
                "parsed_info": {
                    "鱼名": fish_name if fish_name else "未识别",
                    "品质": fish_quality if fish_quality else "未识别",
                    "重量": fish_weight if fish_weight else "未识别",
                },
                "full_text": full_text,
            }
            add_debug_info(debug_info)

        if len(result) == 0 or not full_text:
            return None, None, None, False

        return fish_name, fish_quality, fish_weight, is_first_capture

    except Exception as e:
        print(f"❌ [错误] OCR识别失败: {e}")
        # 调试信息：记录OCR错误
        if debug_mode:
            debug_info = {
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[
                    :-3
                ],
                "action": "ocr_error",
                "error": str(e),
                "exception_type": type(e).__name__,
            }
            add_debug_info(debug_info)
        return None, None, None


def record_caught_fish():
    """识别并记录钓到的鱼"""
    global current_session_fish, all_fish_records
    global record_fish_enabled

    # 调试信息：记录函数开始执行
    if debug_mode:
        debug_info = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "action": "fish_record_start",
            "message": "开始记录钓到的鱼",
            "ocr_available": OCR_AVAILABLE,
            "record_fish_enabled": record_fish_enabled,
        }
        add_debug_info(debug_info)

    if not OCR_AVAILABLE or not record_fish_enabled:
        # 调试信息：记录钓鱼记录开关状态
        if debug_mode:
            debug_info = {
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[
                    :-3
                ],
                "action": "fish_record_check",
                "message": "钓鱼记录未执行",
                "reason": "OCR不可用" if not OCR_AVAILABLE else "钓鱼记录开关已关闭",
                "ocr_available": OCR_AVAILABLE,
                "record_fish_enabled": record_fish_enabled,
            }
            add_debug_info(debug_info)
        return None

    # 等待鱼信息显示
    time.sleep(0.3)

    # 调试信息：记录准备截取鱼信息区域
    if debug_mode:
        debug_info = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "action": "fish_record_capture_start",
            "message": "准备截取鱼信息区域",
        }
        add_debug_info(debug_info)

    # 截取鱼信息区域
    img = capture_fish_info_region()
    if img is None:
        # 调试信息：记录鱼信息区域截取失败
        if debug_mode:
            debug_info = {
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[
                    :-3
                ],
                "action": "fish_record_capture_failed",
                "message": "鱼信息区域截取失败",
            }
            add_debug_info(debug_info)
        return None

    # 调试信息：记录鱼信息区域截取成功
    if debug_mode:
        debug_info = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "action": "fish_record_capture_success",
            "message": "鱼信息区域截取成功",
            "image_shape": img.shape if img is not None else "无图像",
        }
        add_debug_info(debug_info)
        debug_info = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "action": "fish_record_ocr_start",
            "message": "开始OCR识别鱼信息",
        }
        add_debug_info(debug_info)

    # OCR识别
    fish_name, fish_quality, fish_weight, is_first_capture = recognize_fish_info_ocr(img)

    # 调试信息：记录OCR识别结果
    if debug_mode:
        debug_info = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "action": "fish_record_ocr_result",
            "message": "OCR识别完成",
            "fish_name": fish_name,
            "fish_quality": fish_quality,
            "fish_weight": fish_weight,
            "has_valid_data": fish_name is not None
            or fish_quality is not None
            or fish_weight is not None,
        }
        add_debug_info(debug_info)

    if fish_name is None and fish_quality is None and fish_weight is None:
        # 调试信息：记录OCR识别无有效数据
        if debug_mode:
            debug_info = {
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[
                    :-3
                ],
                "action": "fish_record_ocr_no_data",
                "message": "OCR识别未获取到有效鱼信息",
            }
            add_debug_info(debug_info)
        return None

    # 调试信息：记录开始保存记录
    if debug_mode:
        debug_info = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "action": "fish_record_save_start",
            "message": "准备保存钓鱼记录",
            "raw_fish_quality": fish_quality,
        }
        add_debug_info(debug_info)

    try:
        # 创建记录
        with fish_record_lock:
            # 合并"传奇"和"傳奇"品质，统一使用"传奇"（包含繁体）
            if fish_quality in ["传奇", "傳奇"]:
                fish_quality = "传奇"
            fish = FishRecord(fish_name, fish_quality, fish_weight)
            current_session_fish.append(fish)
            all_fish_records.append(fish)
            save_fish_record(fish)

        # 调试信息：记录保存成功
        if debug_mode:
            debug_info = {
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[
                    :-3
                ],
                "action": "fish_record_save_success",
                "message": "钓鱼记录保存成功",
                "record": {
                    "name": fish.name,
                    "quality": fish.quality,
                    "weight": fish.weight,
                    "timestamp": fish.timestamp,
                },
                "parsed_info": {
                    "鱼名": fish.name,
                    "品质": fish.quality,
                    "重量": fish.weight,
                },
            }
            add_debug_info(debug_info)

        # 终端输出
        quality_emoji = QUALITY_COLORS.get(fish.quality, "⚪")
        print(
            f"🐟 [钓到] {quality_emoji} {fish.name} | 品质: {fish.quality} | 重量: {fish.weight}"
        )

        # 传奇鱼自动截屏
        if legendary_screenshot_enabled and fish.quality in ["传奇", "傳奇"]:
            try:
                # 调试信息：记录开始传奇鱼截屏
                if debug_mode:
                    debug_info = {
                        "timestamp": datetime.datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S.%f"
                        )[:-3],
                        "action": "fish_record_screenshot_start",
                        "message": "开始传奇鱼自动截屏",
                    }
                    add_debug_info(debug_info)

                # 使用mss截取主显示器全屏
                with mss.mss() as sct:
                    # 选择主显示器 - 通常index 1是主显示器，但有些系统可能不同
                    # 主显示器通常具有最小的left和top值（0,0坐标）
                    main_monitor = None
                    for i, monitor in enumerate(
                        sct.monitors[1:]
                    ):  # 跳过index 0（所有显示器组合）
                        if monitor["left"] == 0 and monitor["top"] == 0:
                            main_monitor = monitor
                            break

                    # 如果找不到坐标0,0的显示器，使用默认的index 1
                    if main_monitor is None:
                        main_monitor = sct.monitors[1]
                        print(
                            f"📌 [调试] 未找到坐标0,0的显示器，使用默认显示器1: {main_monitor}"
                        )

                    # 强制使用确定的主显示器进行截屏
                    screenshot = sct.grab(main_monitor)

                    # 创建截图保存目录
                    screenshot_dir = os.path.join(".", "截图", "传奇")
                    os.makedirs(screenshot_dir, exist_ok=True)

                    # 生成截图文件名（包含时间戳和鱼名）
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    fish_name_clean = re.sub(r"[^\w\s]", "", fish.name)
                    screenshot_path = os.path.join(
                        screenshot_dir,
                        f"{timestamp}_{fish_name_clean}_{fish.quality}.png",
                    )

                    # 将截图转换为numpy数组，用于裁剪黑色边框
                    img = np.array(screenshot)
                    
                    # 裁剪黑色边框
                    # 转换为灰度图，用于检测边框
                    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
                    
                    # 找到非黑色区域的边界
                    non_black_pixels = np.where(gray > 10)  # 10是黑色阈值，可以调整
                    
                    if len(non_black_pixels[0]) > 0:  # 确保有非黑色像素
                        # 获取边界坐标
                        top = non_black_pixels[0].min()
                        bottom = non_black_pixels[0].max()
                        left = non_black_pixels[1].min()
                        right = non_black_pixels[1].max()
                        
                        # 裁剪图像，去除黑色边框
                        cropped_img = img[top:bottom+1, left:right+1]
                        
                        # 保存裁剪后的图像
                        Image.fromarray(cropped_img).save(screenshot_path)
                    else:
                        # 如果全黑，保存原始图像
                        mss.tools.to_png(
                            screenshot.rgb, screenshot.size, output=screenshot_path
                        )
                    print(
                        f"📸 [截屏] 传奇鱼已自动保存到主显示器截图: {screenshot_path}"
                    )

                    # 调试信息：记录传奇鱼截屏成功
                    if debug_mode:
                        debug_info = {
                            "timestamp": datetime.datetime.now().strftime(
                                "%Y-%m-%d %H:%M:%S.%f"
                            )[:-3],
                            "action": "fish_record_screenshot_success",
                            "message": "传奇鱼自动截屏成功",
                            "screenshot_path": screenshot_path,
                            "monitor_info": monitor,
                        }
                        add_debug_info(debug_info)
            except Exception as e:
                print(f"❌ [错误] 截图失败: {e}")
                # 调试信息：记录传奇鱼截屏失败
                if debug_mode:
                    debug_info = {
                        "timestamp": datetime.datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S.%f"
                        )[:-3],
                        "action": "fish_record_screenshot_failed",
                        "message": "传奇鱼自动截屏失败",
                        "error": str(e),
                        "exception_type": type(e).__name__,
                    }
                    add_debug_info(debug_info)

        # 首次捕获截图
        if first_capture_screenshot_enabled and is_first_capture:
            try:
                # 调试信息：记录开始首次捕获截屏
                if debug_mode:
                    debug_info = {
                        "timestamp": datetime.datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S.%f"
                        )[:-3],
                        "action": "first_capture_screenshot_start",
                        "message": "开始首次捕获自动截屏",
                    }
                    add_debug_info(debug_info)

                # 使用mss截取主显示器全屏
                with mss.mss() as sct:
                    # 选择主显示器
                    main_monitor = None
                    for i, monitor in enumerate(
                        sct.monitors[1:]
                    ):
                        if monitor["left"] == 0 and monitor["top"] == 0:
                            main_monitor = monitor
                            break
                    if main_monitor is None:
                        main_monitor = sct.monitors[1]

                    # 强制使用确定的主显示器进行截屏
                    screenshot = sct.grab(main_monitor)

                    # 创建截图保存目录
                    screenshot_dir = os.path.join(".", "截图", "首次")
                    os.makedirs(screenshot_dir, exist_ok=True)

                    # 生成截图文件名（包含时间戳、鱼名和品质）
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    fish_name_clean = re.sub(r"[^\w\s]", "", fish.name)
                    screenshot_path = os.path.join(
                        screenshot_dir,
                        f"{timestamp}_{fish_name_clean}_{fish.quality}_首次捕获.png",
                    )

                    # 将截图转换为numpy数组，用于裁剪黑色边框
                    img = np.array(screenshot)
                    
                    # 裁剪黑色边框
                    # 转换为灰度图，用于检测边框
                    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
                    
                    # 找到非黑色区域的边界
                    non_black_pixels = np.where(gray > 10)  # 10是黑色阈值，可以调整
                    
                    if len(non_black_pixels[0]) > 0:  # 确保有非黑色像素
                        # 获取边界坐标
                        top = non_black_pixels[0].min()
                        bottom = non_black_pixels[0].max()
                        left = non_black_pixels[1].min()
                        right = non_black_pixels[1].max()
                        
                        # 裁剪图像，去除黑色边框
                        cropped_img = img[top:bottom+1, left:right+1]
                        
                        # 保存裁剪后的图像
                        Image.fromarray(cropped_img).save(screenshot_path)
                    else:
                        # 如果全黑，保存原始图像
                        mss.tools.to_png(
                            screenshot.rgb, screenshot.size, output=screenshot_path
                        )
                    print(
                        f"📸 [截屏] 首次捕获已自动保存到主显示器截图: {screenshot_path}"
                    )

                    # 调试信息：记录首次捕获截屏成功
                    if debug_mode:
                        debug_info = {
                            "timestamp": datetime.datetime.now().strftime(
                                "%Y-%m-%d %H:%M:%S.%f"
                            )[:-3],
                            "action": "first_capture_screenshot_success",
                            "message": "首次捕获自动截屏成功",
                            "screenshot_path": screenshot_path,
                            "monitor_info": monitor,
                        }
                        add_debug_info(debug_info)
            except Exception as e:
                print(f"❌ [错误] 首次捕获截图失败: {e}")
                # 调试信息：记录首次捕获截屏失败
                if debug_mode:
                    debug_info = {
                        "timestamp": datetime.datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S.%f"
                        )[:-3],
                        "action": "first_capture_screenshot_failed",
                        "message": "首次捕获自动截屏失败",
                        "error": str(e),
                        "exception_type": type(e).__name__,
                    }
                    add_debug_info(debug_info)
        
        # 鼠标左键收起 - 截图完成后再收起
        print("🐠 [操作] 执行鼠标左键收起")
        
        try:
            # 直接在屏幕中心执行收起操作
            screen_width, screen_height = get_current_screen_resolution()
            center_x = screen_width // 2
            center_y = screen_height // 2
            
            # 执行点击
            mouse_controller.position = (center_x, center_y)
            time.sleep(0.3)
            mouse_controller.click(mouse.Button.left, 1)
            time.sleep(0.5)  # 增加延迟，确保左键点击完成
            print("🐠 [操作] 在屏幕中心执行收起操作")
        except Exception as e:
            print(f"🐠 [操作] 执行收起操作失败: {str(e)}")
            

        # 放生判断和执行
        if release_fish_enabled:  # 先检查全局开关是否开启
            if should_release_fish(fish.quality, fish.name):  # 再检查鱼的稀有度
                print(f"🐠 [放生] 开始放生 {fish.quality}品质的 {fish.name}")
                # 执行放生操作
                success = release_fish()
                if success:
                    print(f"🐠 [放生] {fish.quality}品质的 {fish.name} 放生成功")
                else:
                    print(f"🐠 [放生] {fish.quality}品质的 {fish.name} 放生失败")
        else:
            print(f"⏹️ [放生] 放生功能已禁用，跳过放生判断")
        # 通知GUI更新
        if gui_fish_update_callback:
            try:
                gui_fish_update_callback()
                # 调试信息：记录GUI更新成功
                if debug_mode:
                    debug_info = {
                        "timestamp": datetime.datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S.%f"
                        )[:-3],
                        "action": "fish_record_gui_update",
                        "message": "钓鱼记录GUI更新成功",
                    }
                    add_debug_info(debug_info)
            except Exception as e:
                # 调试信息：记录GUI更新失败
                if debug_mode:
                    debug_info = {
                        "timestamp": datetime.datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S.%f"
                        )[:-3],
                        "action": "fish_record_gui_update_failed",
                        "message": "钓鱼记录GUI更新失败",
                        "error": str(e),
                        "exception_type": type(e).__name__,
                    }
                    add_debug_info(debug_info)

        return fish
    except Exception as e:
        # 调试信息：记录记录保存失败
        if debug_mode:
            debug_info = {
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[
                    :-3
                ],
                "action": "fish_record_save_failed",
                "message": "钓鱼记录保存失败",
                "error": str(e),
                "exception_type": type(e).__name__,
                "fish_name": fish_name,
                "fish_quality": fish_quality,
                "fish_weight": fish_weight,
            }
            add_debug_info(debug_info)
        return None


def play_fish_bucket_warning_sound():
    """播放鱼桶满/没鱼饵警告!音效"""
    if not fish_bucket_sound_enabled:
        return

    try:
        # 双击关闭警告窗口
        DoubleClickCloseWarningWindow()
    except Exception as e:
        print(f"⚠️[警告] 播放鱼桶满了/没鱼饵警告音效失败: {e}")
        # 备选方案：播放单次声音
        try:
            winsound.MessageBeep(0x00000030)
            # 备选方案：使用print输出控制台铃声
            print("\a")  # 控制台铃声
        except:
            pass


class DoubleClickCloseWarningWindow:
    """鼠标双击关闭的警告窗口"""

    _active_window = None

    def __new__(cls, *args, **kwargs):
        if cls._active_window is not None:
            try:
                cls._active_window.on_close()
            except:
                pass

        instance = super(DoubleClickCloseWarningWindow, cls).__new__(cls)
        cls._active_window = instance
        return instance

    def __init__(self):
        if hasattr(self, "initialized") and self.initialized:
            return

        self.last_click_time = 0
        self.click_count = 0
        self.double_click_threshold = 0.3

        self.mouse_listener = None
        self.sound_playing = True
        self.sound_thread = None

        self.create_window()
        self.start_mouse_listener()
        self.start_sound_playback()

        self.initialized = True

    def start_mouse_listener(self):
        """启动鼠标双击监听器"""

        def on_click(x, y, button, pressed):
            if pressed and button == mouse.Button.left:
                current_time = time.time()
                if current_time - self.last_click_time < self.double_click_threshold:
                    # 双击检测成功
                    self.click_count += 1
                    if self.click_count >= 2:
                        print(f"🖱️ [双击] 检测到鼠标双击，关闭警告窗口")
                        self.on_close()
                        return False  # 停止监听器
                else:
                    # 重置计数
                    self.click_count = 1
                    self.last_click_time = current_time
            return True

        self.mouse_listener = mouse.Listener(on_click=on_click)
        self.mouse_listener.daemon = True
        self.mouse_listener.start()

    def create_window(self):
        """创建窗口"""
        self.window = tk.Toplevel()
        self.window.title("⚠️鱼桶满了/没鱼饵警告！")
        self.window.geometry("400x250")
        self.window.resizable(False, False)
        self.window.attributes("-topmost", True)

        # 创建UI
        main_frame = ttkb.Frame(self.window, padding=20)
        main_frame.pack(fill=BOTH, expand=YES)

        # 标题
        title_label = ttkb.Label(
            main_frame,
            text="⚠️鱼桶满/没鱼饵警告!",
            font=("Segoe UI", 16, "bold"),
            bootstyle="danger",
        )
        title_label.pack(pady=(10, 15))

        # 信息
        info_label = ttkb.Label(
            main_frame,
            text="检测到鱼桶已满/没鱼饵！请及时处理。",
            font=("Segoe UI", 12),
            bootstyle="info",
        )
        info_label.pack(pady=(0, 20))

        # 操作提示
        hint_label = ttkb.Label(
            main_frame,
            text="🖱️ 操作提示：\n• 双击鼠标左键关闭警告\n• 或点击下方按钮关闭",
            font=("Segoe UI", 10),
            bootstyle="warning",
            justify="left",
        )
        hint_label.pack(pady=(0, 20))

        # 关闭按钮
        close_btn = ttkb.Button(
            main_frame,
            text="关闭警告",
            command=self.on_close,
            bootstyle="danger",
            width=20,
        )
        close_btn.pack()

        # 调整布局，确保所有控件都能完整显示
        main_frame.update_idletasks()

        # 确保窗口大小足够容纳所有控件
        self.window.geometry(
            f"{main_frame.winfo_reqwidth() + 40}x{main_frame.winfo_reqheight() + 40}"
        )

        # 窗口关闭事件
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

    def start_sound_playback(self):
        """启动声音播放"""

        def play_sound():
            while self.sound_playing:
                try:
                    winsound.Beep(1000, 300)
                    time.sleep(0.1)
                    winsound.Beep(800, 500)
                    time.sleep(1)
                except:
                    print("\a", end="", flush=True)
                    time.sleep(1.5)

        self.sound_thread = threading.Thread(target=play_sound, daemon=True)
        self.sound_thread.start()

    def on_close(self):
        """关闭窗口"""
        self.sound_playing = False

        if self.sound_thread:
            self.sound_thread.join(timeout=1)

        self.stop_mouse_listener()

        if self.window:
            self.window.destroy()

        # 重置实例
        DoubleClickCloseWarningWindow._active_window = None

    def stop_mouse_listener(self):
        """停止鼠标监听器"""
        if self.mouse_listener:
            self.mouse_listener.stop()
            self.mouse_listener = None


def handle_fish_bucket_full():
    """处理鱼桶满的情况"""
    global fish_bucket_full_detected, bucket_full_by_interval

    # 在运行日志中提示
    print(f"🪣  [警告] 检测到: {FISH_BUCKET_FULL_TEXT}")

    # 根据不同模式执行不同操作
    if bucket_detection_mode == "mode1":
        # 模式1：自动暂停
        # 播放警告音效
        play_fish_bucket_warning_sound()

        # 停止脚本
        if run_event.is_set():
            toggle_run()
            print("🛑 [状态] 脚本已自动停止 (鱼桶已满/没鱼饵/没鱼饵)")
        # 保持检测状态为True，避免重复触发
        fish_bucket_full_detected = True
    elif bucket_detection_mode == "mode2":
        # 模式2：F键+定期鼠标点击模式 - 按下一次F键然后每隔一段时间点击屏幕，遇到键盘活动自动停止
        play_fish_bucket_warning_sound()

        try:
            # 按下一次F键
            keyboard_controller.press(keyboard.KeyCode.from_char("f"))
            time.sleep(0.1)
            keyboard_controller.release(keyboard.KeyCode.from_char("f"))
            print("⌨️  [操作] 已按下F键")

            # 键盘活动标志
            keyboard_activity = [False]

            # 键盘按下事件处理
            def on_key_press(key):
                """键盘按下事件处理"""
                try:
                    # 只响应实际的键盘按键，忽略程序模拟的按键
                    print("⌨️  [检测] 键盘活动，停止鼠标点击")
                    keyboard_activity[0] = True
                    return False  # 停止监听器
                except Exception as e:
                    return True  # 继续监听

            # 启动键盘监听器
            keyboard_listener = keyboard.Listener(on_press=on_key_press, suppress=False)
            keyboard_listener.start()

            print("🖱️  [操作] 开始定期鼠标点击，5秒/次，直到检测到键盘活动")

            # 一直循环点击屏幕，直到检测到键盘活动
            while not keyboard_activity[0]:
                # 获取屏幕中心位置
                screen_width, screen_height = get_current_screen_resolution()
                click_x = screen_width // 2
                click_y = screen_height // 2

                # 执行鼠标点击
                mouse_controller.position = (click_x, click_y)
                mouse_controller.click(mouse.Button.left, 1)
                print(f"🖱️  [操作] 已点击屏幕中心: ({click_x}, {click_y})")

                # 等待一段时间，同时检查键盘活动
                for _ in range(50):  # 5秒 = 50 * 0.1秒
                    if keyboard_activity[0]:
                        break
                    time.sleep(0.1)  # 每0.1秒检查一次键盘活动

                if keyboard_activity[0]:
                    break

            print("🖱️  [操作] 已停止鼠标点击")

            # 停止键盘监听器
            try:
                if (
                    keyboard_listener
                    and hasattr(keyboard_listener, "is_alive")
                    and keyboard_listener.is_alive()
                ):
                    keyboard_listener.stop()
                    keyboard_listener.join(timeout=0.5)  # 等待监听器线程结束
            except Exception as e:
                print(f"⚠️  [警告] 停止键盘监听器时出错: {e}")
        except Exception as e:
            print(f"❌ [错误] 执行F键+鼠标点击模式时出错: {e}")
        # 模式2不自动暂停，重置检测状态
        reset_fish_bucket_full_detection()
    elif bucket_detection_mode == "mode3":
        # 模式3：仅F键模式 - 不会自动暂停，只会按下一次F键
        play_fish_bucket_warning_sound()

        try:
            # 按下一次F键
            keyboard_controller.press(keyboard.KeyCode.from_char("f"))
            time.sleep(0.1)
            keyboard_controller.release(keyboard.KeyCode.from_char("f"))
            print("⌨️  [操作] 已按下F键")
        except Exception as e:
            print(f"❌ [错误] 执行仅F键模式时出错: {e}")
        # 模式3不自动暂停，重置检测状态
        reset_fish_bucket_full_detection()


def reset_fish_bucket_full_detection():
    """重置鱼桶满检测状态"""
    global fish_bucket_full_detected, bucket_full_by_interval
    fish_bucket_full_detected = False
    bucket_full_by_interval = False
    with casting_interval_lock:
        casting_timestamps.clear()  # 清空时间戳


def bucket_full_detection_thread():
    """鱼桶满独立检测线程 - 修复版
    检测完整钓鱼循环的时长，而不是抛竿间隔
    """
    global fish_bucket_full_detected, bucket_full_by_interval, paogantime

    short_cycle_count = 0  # 短循环计数器
    last_reset_time = time.time()  # 上次重置计数器的时间

    while True:
        if not run_event.is_set():
            # 脚本未运行时，重置检测状态
            short_cycle_count = 0
            with casting_interval_lock:
                casting_timestamps.clear()
            time.sleep(0.5)
            continue

        try:
            # 定期重置计数器（防止累积误判）
            current_time = time.time()
            if current_time - last_reset_time > 30:  # 每30秒重置一次
                if short_cycle_count > 0:
                    print(f"🔄 [检测] 定期重置短循环计数器: {short_cycle_count}次")
                    short_cycle_count = 0
                last_reset_time = current_time

            with casting_interval_lock:
                # 复制时间戳列表，避免在计算过程中被修改
                timestamps = casting_timestamps.copy()

            # 需要至少2个时间戳来计算1个间隔
            if len(timestamps) < 2:
                time.sleep(0.5)
                continue

            # 计算最近一次完整钓鱼循环的时长
            last_interval = timestamps[-1] - timestamps[-2]

            # 【核心判断逻辑】
            # 正常钓鱼循环应该至少包含：
            # - 抛竿动画（0.5秒）
            # - 等待上钩（随机，通常3-10秒）
            # - 收放线（3-10秒）
            # - 识别鱼信息（0.5秒）
            # 总计：正常至少7-20秒

            # 鱼桶满/没鱼饵时的特征：循环异常短
            # 动态阈值计算：基于当前抛竿时间，确保正常循环不会被误判
            # - 基于当前抛竿时间的1.0倍
            # 基数+当前抛竿时间的动态阈值
            base_value = 0.8  # 基数
            dynamic_threshold = base_value + paogantime
            if last_interval < dynamic_threshold:
                short_cycle_count += 1
                print(
                    f"⚠️  [检测] 检测到短循环 #{short_cycle_count}: {last_interval:.2f}秒 (<{dynamic_threshold:.2f}秒)"
                )

                # 连续3次短循环才判定为鱼桶满
                REQUIRED_SHORT_CYCLES = 3
                if (
                    short_cycle_count >= REQUIRED_SHORT_CYCLES
                    and not fish_bucket_full_detected
                    and not bucket_full_by_interval
                ):
                    # 额外验证：检查最近的REQUIRED_SHORT_CYCLES个循环是否都异常短
                    recent_short_cycles = 0
                    check_count = min(REQUIRED_SHORT_CYCLES, len(timestamps) - 1)

                    for i in range(len(timestamps) - check_count, len(timestamps)):
                        interval = timestamps[i] - timestamps[i - 1]
                        if interval < dynamic_threshold:
                            recent_short_cycles += 1

                    # 如果最近的check_count个循环都是短循环，或者记录很少，就判定
                    if recent_short_cycles >= check_count or len(timestamps) <= 5:
                        print(
                            f"🪣  [警告] 连续{short_cycle_count}次短循环，判定为鱼桶满/没鱼饵！"
                        )
                        print(
                            f"   最近{len(timestamps)}次循环时长: {[round(timestamps[i]-timestamps[i-1], 2) for i in range(1, len(timestamps))]}"
                        )

                        bucket_full_by_interval = True
                        fish_bucket_full_detected = True
                        handle_fish_bucket_full()
            else:
                # 正常循环，重置计数器
                if short_cycle_count > 0:
                    # 当检测到符合动态阈值的正常循环时重置计数器
                    print(
                        f"✅ [检测] 恢复正常循环: {last_interval:.2f}秒，重置短循环计数器"
                    )
                    short_cycle_count = 0

            time.sleep(0.5)  # 每0.5秒检查一次

        except Exception as e:
            print(f"⚠️  [警告] 鱼桶满检测线程出错: {e}")
            time.sleep(1)


def get_session_fish_list():
    """获取当前会话的钓鱼记录"""
    with fish_record_lock:
        return list(current_session_fish)


def get_all_fish_list():
    """获取所有钓鱼记录"""
    with fish_record_lock:
        return list(all_fish_records)


def search_fish_records(keyword="", quality_filter="全部", use_session=True):
    """搜索钓鱼记录"""
    with fish_record_lock:
        records = current_session_fish if use_session else all_fish_records

        filtered = []
        for record in records:
            # 品质筛选 - 合并"传奇"和"传奇"，以及"标准"和"標準"
            if quality_filter != "全部":
                if quality_filter == "传奇":
                    # 筛选传奇时也包含传奇
                    if record.quality not in ["传奇", "傳奇"]:
                        continue
                elif quality_filter == "标准":
                    # 筛选标准时也包含繁体標準
                    if record.quality not in ["标准", "標準"]:
                        continue
                elif quality_filter == "史诗":
                    if record.quality not in ["史詩", "史诗"]:
                        continue
                else:
                    # 其他品质正常筛选
                    if record.quality != quality_filter:
                        continue
            # 关键词搜索
            if keyword and keyword.lower() not in record.name.lower():
                continue
            filtered.append(record)

        return filtered


# 定义区域的坐标 (x, y, w, h) - 基于2K分辨率的基准值
# 使用与update_region_coords函数相同的缩放方式，确保与模板缩放一致
region3_coords = scale_coords_top_center(1172, 165, 34, 34)  # 上鱼星星
region4_coords = scale_coords_bottom_anchored(1100, 1329, 10, 19)  # F1位置
region5_coords = scale_coords_bottom_anchored(1212, 1329, 10, 19)  # F2位置
region6_coords = scale_coords_bottom_anchored(1146, 1316, 17, 21)  # 上鱼右键

# 鱼饵数量区域（基准值）
BAIT_REGION_BASE = (2318, 1296, 2348, 1318)
# 加时界面检测区域（基准值）
JIASHI_REGION_BASE = (1244, 674, 29, 29)
# 点击按钮位置（基准值）
BTN_NO_JIASHI_BASE = (1175, 778)  # 不加时按钮
BTN_YES_JIASHI_BASE = (1390, 778)  # 加时按钮
# 加时相关坐标缓存（用于分辨率变化时自动更新）
jiashi_region_coords = None  # 加时检测区域
btn_no_jiashi_coords = None  # 不加时按钮
btn_yes_jiashi_coords = None  # 加时按钮
previous_result = None  # 上次识别的结果
current_result = 0  # 当前识别的数字
# 模板加载一次
templates = None
star_template = None
f1 = None
f2 = None
shangyule = None
jiashi = None
tiao_template = None  # UNO条模板
jiashi_var = 0
# 模板缩放后的缓存（用于分辨率切换时重新加载）
_cached_scale_x = None
_cached_scale_y = None
run_event = threading.Event()
begin_event = threading.Event()
user32 = ctypes.WinDLL("user32")
listener = None  # 监听
hotkey_name = "F2"  # 默认热键显示名称
hotkey_modifiers = set()  # 修饰键集合 (ctrl, alt, shift)
hotkey_main_key = keyboard.Key.f2  # 主按键对象

# UNO功能热键
uno_hotkey_name = "F3"  # 默认UNO热键显示名称
uno_hotkey_modifiers = set()  # UNO热键修饰键集合
uno_hotkey_main_key = keyboard.Key.f3  # UNO热键主按键对象
# UNO卡计数变量
global uno_input1_var, uno_input2_var  # 当前牌数和抽取牌数变量
uno_input1_var = None
uno_input2_var = None

# UNO持续识别相关变量
uno_recognition_running = False  # 持续识别状态
uno_recognition_thread = None  # 持续识别线程
uno_popup_shown = False  # 弹窗显示标志，防止重复弹窗

# 全局root变量声明
root = None


# 获取当前系统分辨率
def get_current_screen_resolution():
    """
    获取当前系统的屏幕分辨率
    返回: (width, height) 元组
    """
    try:
        # 尝试使用EnumDisplaySettings获取实际物理分辨率（不受DPI缩放影响）
        # 定义DEVMODE结构体
        class DEVMODE(ctypes.Structure):
            _fields_ = [
                ("dmDeviceName", ctypes.c_wchar * 32),
                ("dmSpecVersion", ctypes.c_short),
                ("dmDriverVersion", ctypes.c_short),
                ("dmSize", ctypes.c_short),
                ("dmDriverExtra", ctypes.c_short),
                ("dmFields", ctypes.c_ulong),
                ("dmOrientation", ctypes.c_short),
                ("dmPaperSize", ctypes.c_short),
                ("dmPaperLength", ctypes.c_short),
                ("dmPaperWidth", ctypes.c_short),
                ("dmScale", ctypes.c_short),
                ("dmCopies", ctypes.c_short),
                ("dmDefaultSource", ctypes.c_short),
                ("dmPrintQuality", ctypes.c_short),
                ("dmColor", ctypes.c_short),
                ("dmDuplex", ctypes.c_short),
                ("dmYResolution", ctypes.c_short),
                ("dmTTOption", ctypes.c_short),
                ("dmCollate", ctypes.c_short),
                ("dmFormName", ctypes.c_wchar * 32),
                ("dmLogPixels", ctypes.c_short),
                ("dmBitsPerPel", ctypes.c_ulong),
                ("dmPelsWidth", ctypes.c_ulong),
                ("dmPelsHeight", ctypes.c_ulong),
                ("dmDisplayFlags", ctypes.c_ulong),
                ("dmDisplayFrequency", ctypes.c_ulong),
                ("dmICMMethod", ctypes.c_ulong),
                ("dmICMIntent", ctypes.c_ulong),
                ("dmMediaType", ctypes.c_ulong),
                ("dmDitherType", ctypes.c_ulong),
                ("dmReserved1", ctypes.c_ulong),
                ("dmReserved2", ctypes.c_ulong),
                ("dmPanningWidth", ctypes.c_ulong),
                ("dmPanningHeight", ctypes.c_ulong),
            ]

        # 创建DEVMODE实例
        devmode = DEVMODE()
        devmode.dmSize = ctypes.sizeof(DEVMODE)

        # 获取当前显示设置
        if user32.EnumDisplaySettingsW(None, -1, ctypes.byref(devmode)):
            # 使用实际物理分辨率
            actual_width = devmode.dmPelsWidth
            actual_height = devmode.dmPelsHeight
            return actual_width, actual_height

        # 备选方案：使用GetSystemMetrics
        width = user32.GetSystemMetrics(0)  # SM_CXSCREEN = 0
        height = user32.GetSystemMetrics(1)  # SM_CYSCREEN = 1
        return width, height
    except Exception as e:
        print(f"❌ [错误] 获取屏幕分辨率失败: {e}")
        return TARGET_WIDTH, TARGET_HEIGHT


# 注意：CURRENT_SCREEN_WIDTH 和 CURRENT_SCREEN_HEIGHT 会在 load_parameters() 函数中被正确初始化
# 这里不再提前初始化，避免DPI缩放影响

# 分辨率初始值，会在 load_parameters() 中被覆盖
CURRENT_SCREEN_WIDTH = TARGET_WIDTH
CURRENT_SCREEN_HEIGHT = TARGET_HEIGHT

# 当前按下的修饰键状态
current_modifiers = set()

# 修饰键映射
MODIFIER_KEYS = {
    keyboard.Key.ctrl_l: "ctrl",
    keyboard.Key.ctrl_r: "ctrl",
    keyboard.Key.alt_l: "alt",
    keyboard.Key.alt_r: "alt",
    keyboard.Key.alt_gr: "alt",
    keyboard.Key.shift_l: "shift",
    keyboard.Key.shift_r: "shift",
}

# 特殊键名称映射（用于显示和解析）
SPECIAL_KEY_NAMES = {
    keyboard.Key.f1: "F1",
    keyboard.Key.f2: "F2",
    keyboard.Key.f3: "F3",
    keyboard.Key.f4: "F4",
    keyboard.Key.f5: "F5",
    keyboard.Key.f6: "F6",
    keyboard.Key.f7: "F7",
    keyboard.Key.f8: "F8",
    keyboard.Key.f9: "F9",
    keyboard.Key.f10: "F10",
    keyboard.Key.f11: "F11",
    keyboard.Key.f12: "F12",
    keyboard.Key.space: "Space",
    keyboard.Key.enter: "Enter",
    keyboard.Key.tab: "Tab",
    keyboard.Key.backspace: "Backspace",
    keyboard.Key.delete: "Delete",
    keyboard.Key.insert: "Insert",
    keyboard.Key.home: "Home",
    keyboard.Key.end: "End",
    keyboard.Key.page_up: "PageUp",
    keyboard.Key.page_down: "PageDown",
    keyboard.Key.up: "↑",
    keyboard.Key.down: "↓",
    keyboard.Key.left: "←",
    keyboard.Key.right: "→",
    keyboard.Key.esc: "Esc",
    keyboard.Key.pause: "Pause",
    keyboard.Key.print_screen: "PrintScreen",
    keyboard.Key.scroll_lock: "ScrollLock",
    keyboard.Key.caps_lock: "CapsLock",
    keyboard.Key.num_lock: "NumLock",
    # 鼠标侧键支持
    mouse.Button.x1: "Mouse4",  # 鼠标前进键
    mouse.Button.x2: "Mouse5",  # 鼠标后退键
}

# 反向映射：名称 -> 按键对象
NAME_TO_KEY = {v: k for k, v in SPECIAL_KEY_NAMES.items()}


def parse_hotkey_string(hotkey_str):
    """
    解析热键字符串，返回 (修饰键集合, 主按键对象, 主按键名称)
    例如: "Ctrl+Shift+A" -> ({'ctrl', 'shift'}, KeyCode(char='a'), 'A')
    支持鼠标侧键: "Mouse4" -> (set(), mouse.Button.x1, "Mouse4")
    """
    parts = [p.strip() for p in hotkey_str.split("+")]
    modifiers = set()
    main_key = None
    main_key_name = ""

    for part in parts:
        part_lower = part.lower()
        if part_lower == "ctrl":
            modifiers.add("ctrl")
        elif part_lower == "alt":
            modifiers.add("alt")
        elif part_lower == "shift":
            modifiers.add("shift")
        else:
            # 这是主按键
            main_key_name = part
            # 检查是否是特殊键
            if part in NAME_TO_KEY:
                main_key = NAME_TO_KEY[part]
            # 检查是否是数字小键盘按键
            elif part.startswith("Num"):
                num_part = part[3:]
                if num_part.isdigit():
                    # 数字小键盘数字键（0-9）
                    num = int(num_part)
                    if 0 <= num <= 9:
                        main_key = keyboard.KeyCode(vk=96 + num)
                elif num_part == ".":
                    # 数字小键盘小数点
                    main_key = keyboard.KeyCode(vk=110)
                elif num_part == "*":
                    # 数字小键盘乘号
                    main_key = keyboard.KeyCode(vk=106)
                elif num_part == "+":
                    # 数字小键盘加号
                    main_key = keyboard.KeyCode(vk=107)
                elif num_part == "-":
                    # 数字小键盘减号
                    main_key = keyboard.KeyCode(vk=109)
                elif num_part == "/":
                    # 数字小键盘除号
                    main_key = keyboard.KeyCode(vk=111)
            elif len(part) == 1:
                # 单个字符键
                main_key = keyboard.KeyCode.from_char(part.lower())
            else:
                # 尝试作为特殊键名称
                try:
                    main_key = getattr(keyboard.Key, part.lower())
                except AttributeError:
                    # 检查是否是鼠标侧键
                    if part == "Mouse4":
                        main_key = mouse.Button.x1
                    elif part == "Mouse5":
                        main_key = mouse.Button.x2
                    else:
                        main_key = keyboard.KeyCode.from_char(part[0].lower())

    return modifiers, main_key, main_key_name


def format_hotkey_display(modifiers, main_key_name):
    """格式化热键显示字符串"""
    parts = []
    if "ctrl" in modifiers:
        parts.append("Ctrl")
    if "alt" in modifiers:
        parts.append("Alt")
    if "shift" in modifiers:
        parts.append("Shift")
    parts.append(main_key_name)
    return "+".join(parts)


def key_to_name(key):
    """将按键对象转换为显示名称"""
    # 检查是否为鼠标按键
    if key in SPECIAL_KEY_NAMES:
        return SPECIAL_KEY_NAMES[key]
    # 处理键盘按键
    elif hasattr(key, "vk") and key.vk is not None:
        # 通过虚拟键码识别按键（解决Ctrl+字母时char为控制字符的问题）
        vk = key.vk
        # 字母键 A-Z (vk: 65-90)
        if 65 <= vk <= 90:
            return chr(vk)  # 返回大写字母
        # 数字键 0-9 (vk: 48-57)
        elif 48 <= vk <= 57:
            return chr(vk)
        # 数字小键盘 0-9 (vk: 96-105)
        elif 96 <= vk <= 105:
            return f"Num{vk - 96}"
        # 其他有vk但没有可打印char的键
        elif hasattr(key, "char") and key.char and key.char.isprintable():
            return key.char.upper()
        else:
            return f"Key{vk}"
    elif hasattr(key, "char") and key.char and key.char.isprintable():
        return key.char.upper()
    return str(key)


a = 0
region1 = 0
region2 = 0
result_val_is = None
scr = None


# =========================
# 模板加载
# =========================
def scale_template(template, scale_x, scale_y):
    """根据缩放比例缩放模板图片"""
    if scale_x == 1.0 and scale_y == 1.0:
        return template
    h, w = template.shape[:2]
    new_w = max(1, int(w * scale_x))
    new_h = max(1, int(h * scale_y))
    return cv2.resize(template, (new_w, new_h), interpolation=cv2.INTER_LINEAR)


def reload_templates_if_scale_changed():
    """如果缩放比例变化，重新加载所有模板"""
    global templates, star_template, f1, f2, shangyule, jiashi
    global _cached_scale_x, _cached_scale_y

    # 只有当缓存的缩放比例存在且发生变化时，才重新加载模板
    if (_cached_scale_x is not None and _cached_scale_y is not None) and (
        _cached_scale_x != SCALE_X or _cached_scale_y != SCALE_Y
    ):
        # 缩放比例变化，需要重新加载所有模板
        _cached_scale_x = SCALE_X
        _cached_scale_y = SCALE_Y
        print(
            f"🔄 [模板] 分辨率变化，重新加载模板 (缩放: X={SCALE_X:.2f}, Y={SCALE_Y:.2f})"
        )

        # 重新加载所有模板（强制重新加载）
        try:
            # 使用统一缩放比例避免模板变形
            scale = SCALE_UNIFORM

            # 数字模板
            templates = []
            for i in range(10):
                template_path = os.path.join(template_folder_path, f"{i}_grayscale.png")
                img = Image.open(template_path)
                template = np.array(img)
                template = scale_template(template, scale, scale)
                templates.append(template)

            # 星星模板
            star_template_path = os.path.join(
                template_folder_path, "star_grayscale.png"
            )
            img = Image.open(star_template_path)
            star_template = scale_template(np.array(img), scale, scale)

            # F1模板
            f1_path = os.path.join(template_folder_path, "F1_grayscale.png")
            img = Image.open(f1_path)
            f1 = scale_template(np.array(img), scale, scale)

            # F2模板
            f2_path = os.path.join(template_folder_path, "F2_grayscale.png")
            img = Image.open(f2_path)
            f2 = scale_template(np.array(img), scale, scale)

            # 上鱼模板
            shangyule_path = os.path.join(template_folder_path, "shangyu_grayscale.png")
            img = Image.open(shangyule_path)
            shangyule = scale_template(np.array(img), scale, scale)

            # 加时模板
            jiashi_path = os.path.join(template_folder_path, "chang_grayscale.png")
            img = Image.open(jiashi_path)
            jiashi = scale_template(np.array(img), scale, scale)

            # UNO条模板
            try:
                tiao_path = os.path.join(template_folder_path, "tiao_gray.png")
                img = Image.open(tiao_path)
                tiao_template = scale_template(np.array(img), scale, scale)
            except Exception as e:
                print(f"⚠️ [模板] 加载UNO条模板失败: {e}")
                tiao_template = None

            print(
                f"✅ [模板] 所有模板重新加载完成，共 {len(templates)} 个数字模板 (统一缩放: {scale:.2f})"
            )
        except Exception as e:
            print(f"❌ [错误] 重新加载模板失败: {e}")
    elif _cached_scale_x is None and _cached_scale_y is None:
        # 第一次运行，初始化缓存
        _cached_scale_x = SCALE_X
        _cached_scale_y = SCALE_Y


# 加载模板（0.png到9.png）
def load_templates():
    global templates, template_folder_path
    if templates is None:
        templates = []
        scale = SCALE_UNIFORM  # 使用统一缩放比例
        for i in range(10):
            template_path = os.path.join(template_folder_path, f"{i}_grayscale.png")
            img = Image.open(template_path)
            template = np.array(img)
            # 根据当前缩放比例缩放模板
            template = scale_template(template, scale, scale)
            templates.append(template)
    return templates


# 加载模板
def load_star_template():
    global star_template, template_folder_path
    if star_template is None:
        star_template_path = os.path.join(template_folder_path, "star_grayscale.png")
        img = Image.open(star_template_path)
        template = np.array(img)
        scale = SCALE_UNIFORM  # 使用统一缩放比例
        star_template = scale_template(template, scale, scale)
    return star_template


def load_f1():
    global f1
    if f1 is None:
        f1_path = os.path.join(template_folder_path, "F1_grayscale.png")
        img = Image.open(f1_path)
        template = np.array(img)
        scale = SCALE_UNIFORM
        f1 = scale_template(template, scale, scale)
    return f1


def load_f2():
    global f2
    if f2 is None:
        f2_path = os.path.join(template_folder_path, "F2_grayscale.png")
        img = Image.open(f2_path)
        template = np.array(img)
        scale = SCALE_UNIFORM
        f2 = scale_template(template, scale, scale)
    return f2


def load_shangyule():
    global shangyule
    shangyule_path = os.path.join(template_folder_path, "shangyu_grayscale.png")
    img = Image.open(shangyule_path)
    template = np.array(img)
    scale = SCALE_UNIFORM
    shangyule = scale_template(template, scale, scale)
    return shangyule


def load_jiashi():
    global jiashi
    jiashi_path = os.path.join(template_folder_path, "chang_grayscale.png")
    

    
    img = Image.open(jiashi_path)
    template = np.array(img)
    
    # 改进模板缩放方法，确保模板正确缩放
    # 根据当前分辨率获取正确的缩放比例
    screen_width, screen_height = get_current_screen_resolution()
    if screen_width > screen_height:
        scale = screen_width / BASE_WIDTH
    else:
        scale = screen_height / BASE_HEIGHT
    
    # 使用更精确的缩放方法
    scaled_w = int(template.shape[1] * scale)
    scaled_h = int(template.shape[0] * scale)
    jiashi = cv2.resize(template, (scaled_w, scaled_h), interpolation=cv2.INTER_AREA)
    
    return jiashi


# =========================
# 鼠标操作（使用 win32api 实现）
# =========================
mouse_lock = threading.Lock()
mouse_is_down = False


def handle_jiashi_in_action(scr):
    """
    在动作执行过程中处理加时，返回是否检测到并处理了加时
    """
    # 处理加时选择（使用锁保护读取jiashi_var）
    with param_lock:
        current_jiashi = jiashi_var

    # 确保加时按钮坐标已初始化
    if btn_no_jiashi_coords is None or btn_yes_jiashi_coords is None:
        update_region_coords()

    if current_jiashi == 0:
        if fangzhu_jiashi(scr):
            btn_x, btn_y = btn_no_jiashi_coords
            user32.SetCursorPos(btn_x, btn_y)
            time.sleep(0.05)
            user32.mouse_event(0x02, 0, 0, 0, 0)
            time.sleep(0.1)
            user32.mouse_event(0x04, 0, 0, 0, 0)
            time.sleep(0.05)
            if bait_math_val(scr):
                with param_lock:
                    previous_result = result_val_is
            return True
    elif current_jiashi == 1:
        if fangzhu_jiashi(scr):
            btn_x, btn_y = btn_yes_jiashi_coords
            user32.SetCursorPos(btn_x, btn_y)
            time.sleep(0.05)
            user32.mouse_event(0x02, 0, 0, 0, 0)
            time.sleep(0.1)
            user32.mouse_event(0x04, 0, 0, 0, 0)
            time.sleep(0.05)
            if bait_math_val(scr):
                with param_lock:
                    previous_result = result_val_is
            return True
    return False


def pressandreleasemousebutton():
    # 先检查是否需要处理加时
    with mss.mss() as temp_scr:
        if handle_jiashi_in_action(temp_scr):
            return True

        # [新增] 故障检测：检查是否断线或超时（回到待机状态）
        if f1_mached(temp_scr) or f2_mached(temp_scr):
            print("⚠️ [监测] 检测到异常，判定为断线或鱼跑了，本轮结束")
            return False

    user32.mouse_event(0x02, 0, 0, 0, 0)
    jittered_down = add_jitter(leftclickdown)
    time.sleep(jittered_down)
    print_timing_info("收线", leftclickdown, jittered_down)
    user32.mouse_event(0x04, 0, 0, 0, 0)
    jittered_up = add_jitter(leftclickup)
    time.sleep(jittered_up)
    print_timing_info("放线", leftclickup, jittered_up)
    return True


def ensure_mouse_down():
    global mouse_is_down
    with mouse_lock:
        if not mouse_is_down:
            user32.mouse_event(0x02, 0, 0, 0, 0)  # 左键按下
            mouse_is_down = True


def ensure_mouse_up():
    global mouse_is_down
    with mouse_lock:
        if mouse_is_down:
            user32.mouse_event(0x04, 0, 0, 0, 0)  # 左键释放
            mouse_is_down = False


# =========================
# 比较数字大小
# =========================
def compare_results():
    global current_result, previous_result
    if current_result is None or previous_result is None:
        return 0  # 无法比较，返回 0 作为标识
    if current_result > previous_result:
        return 1  # 当前结果较大
    elif current_result < previous_result:
        return -1  # 上次结果较大
    else:
        return 0  # 当前结果与上次相同


# =========================
# 截取屏幕区域
# =========================
# 基准裁切尺寸（2K分辨率下的像素值）
BAIT_CROP_HEIGHT_BASE = 22
BAIT_CROP_WIDTH1_BASE = 15  # 单个数字宽度


# 获取电脑屏幕最大分辨率
def get_max_screen_resolution():
    """获取电脑屏幕的最大分辨率"""
    try:
        # 定义结构体
        class DEVMODEW(ctypes.Structure):
            _fields_ = [
                ("dmDeviceName", ctypes.c_wchar * 32),
                ("dmSpecVersion", ctypes.wintypes.WORD),
                ("dmDriverVersion", ctypes.wintypes.WORD),
                ("dmSize", ctypes.wintypes.WORD),
                ("dmDriverExtra", ctypes.wintypes.WORD),
                ("dmFields", ctypes.wintypes.DWORD),
                ("dmPositionX", ctypes.wintypes.LONG),
                ("dmPositionY", ctypes.wintypes.LONG),
                ("dmDisplayOrientation", ctypes.wintypes.DWORD),
                ("dmDisplayFixedOutput", ctypes.wintypes.DWORD),
                ("dmColor", ctypes.wintypes.SHORT),
                ("dmDuplex", ctypes.wintypes.SHORT),
                ("dmYResolution", ctypes.wintypes.SHORT),
                ("dmTTOption", ctypes.wintypes.SHORT),
                ("dmCollate", ctypes.wintypes.SHORT),
                ("dmFormName", ctypes.c_wchar * 32),
                ("dmLogPixels", ctypes.wintypes.WORD),
                ("dmBitsPerPel", ctypes.wintypes.DWORD),
                ("dmPelsWidth", ctypes.wintypes.DWORD),
                ("dmPelsHeight", ctypes.wintypes.DWORD),
                ("dmDisplayFlags", ctypes.wintypes.DWORD),
                ("dmDisplayFrequency", ctypes.wintypes.DWORD),
                ("dmICMMethod", ctypes.wintypes.DWORD),
                ("dmICMIntent", ctypes.wintypes.DWORD),
                ("dmMediaType", ctypes.wintypes.DWORD),
                ("dmDitherType", ctypes.wintypes.DWORD),
                ("dmReserved1", ctypes.wintypes.DWORD),
                ("dmReserved2", ctypes.wintypes.DWORD),
                ("dmPanningWidth", ctypes.wintypes.DWORD),
                ("dmPanningHeight", ctypes.wintypes.DWORD),
            ]

        user32 = ctypes.windll.user32
        devmode = DEVMODEW()
        devmode.dmSize = ctypes.sizeof(DEVMODEW)

        # 尝试获取显示器的最大分辨率
        max_width, max_height = 0, 0
        i = 0
        while user32.EnumDisplaySettingsW(None, i, ctypes.byref(devmode)):
            if devmode.dmPelsWidth > max_width:
                max_width = devmode.dmPelsWidth
                max_height = devmode.dmPelsHeight
            i += 1

        # 如果没有获取到，回退到当前分辨率
        if max_width == 0 or max_height == 0:
            max_width = user32.GetSystemMetrics(0)
            max_height = user32.GetSystemMetrics(1)

        return max_width, max_height
    except:
        # 出错时回退到当前分辨率
        try:
            user32 = ctypes.windll.user32
            current_width = user32.GetSystemMetrics(0)
            current_height = user32.GetSystemMetrics(1)
            return current_width, current_height
        except:
            return None, None


def bait_math_val(scr):
    global region1, region2, result_val_is
    # 记录日志：开始鱼饵识别
    if debug_mode:
        debug_info = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "action": "bait_recognition_start",
            "message": "开始识别鱼饵数量",
            "algorithm": bait_recognition_algorithm,
        }
        add_debug_info(debug_info)

    # 鱼饵数量显示在屏幕右下角，使用锚定方式计算坐标
    x1, y1, x2, y2 = BAIT_REGION_BASE
    base_w = x2 - x1
    base_h = y2 - y1

    # 使用现有的scale_corner_anchored函数计算坐标，确保与其他UI元素使用相同的缩放逻辑
    actual_x1, actual_y1, actual_w, actual_h = scale_corner_anchored(
        x1, y1, base_w, base_h, anchor="bottom_right"
    )
    actual_x2 = actual_x1 + actual_w
    actual_y2 = actual_y1 + actual_h

    region = (actual_x1, actual_y1, actual_x2, actual_y2)

    # 记录日志：识别区域
    if debug_mode:
        debug_info = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "action": "bait_recognition_region",
            "message": "鱼饵识别区域",
            "region": {
                "x1": actual_x1,
                "y1": actual_y1,
                "x2": actual_x2,
                "y2": actual_y2,
            },
        }
        add_debug_info(debug_info)

    math_frame = scr.grab(region)
    # 将 mss 截取的图像转换为 NumPy 数组 (height, width, 4)，即 RGBA 图像
    if math_frame is None:
        result_val_is = None
        # 记录日志：识别失败
        if debug_mode:
            debug_info = {
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[
                    :-3
                ],
                "action": "bait_recognition_failed",
                "message": "无法获取鱼饵区域图像",
            }
            add_debug_info(debug_info)
        return None
    else:
        img = np.array(math_frame)  # screenshot 是 ScreenShot 类型，转换为 NumPy 数组
        gray_img = cv2.cvtColor(img, cv2.COLOR_RGBA2GRAY)

        # 根据统一缩放比例动态计算裁切尺寸
        scale = SCALE_UNIFORM
        crop_h = max(1, int(BAIT_CROP_HEIGHT_BASE * scale))
        crop_w = max(1, int(BAIT_CROP_WIDTH1_BASE * scale))

        # 确保不超出图像边界
        img_h, img_w = gray_img.shape[:2]
        crop_h = min(crop_h, img_h)
        crop_w = min(crop_w, img_w // 2)  # 确保单个数字宽度不超过一半

        # 初始化匹配结果
        best_match1 = None
        best_match2 = None
        best_match3 = None

        # 截取并处理区域1（第一个数字）
        if crop_w <= img_w:
            region1 = gray_img[0:crop_h, 0:crop_w]
            best_match1 = match_digit_template(region1)

        # 截取并处理区域2（第二个数字）
        if crop_w * 2 <= img_w:
            region2 = gray_img[0:crop_h, crop_w : crop_w * 2]
            best_match2 = match_digit_template(region2)

        # 单个数字居中区域 - 动态计算起始位置，适应各种分辨率
        mid_start = max(0, (img_w - crop_w) // 2)
        mid_end = min(mid_start + crop_w, img_w)
        region3 = gray_img[0:crop_h, mid_start:mid_end]
        best_match3 = match_digit_template(region3)
        if best_match1 and best_match2:
            # 从best_match中提取数字索引（i），并拼接成整数
            best_match1_val = best_match1[0]  # 提取区域1的数字索引
            best_match2_val = best_match2[0]  # 提取区域2的数字索引
            # 拼接两个匹配的数字，转换为整数
            result_val_is = int(f"{best_match1_val}{best_match2_val}")
        elif best_match3:
            result_val_is = int(f"{best_match3[0]}")
        else:
            result_val_is = None

        # 记录日志：识别结果
        if debug_mode:
            debug_info = {
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[
                    :-3
                ],
                "action": "bait_recognition_result",
                "message": "鱼饵识别完成",
                "result": result_val_is,
                "algorithm": bait_recognition_algorithm,
                "parsed_info": {
                    "鱼饵数量": result_val_is if result_val_is is not None else "未识别"
                },
            }
            add_debug_info(debug_info)
        return result_val_is


def match_digit_template(image):
    global templates
    # 确保模板已加载
    if templates is None or len(templates) == 0:
        load_templates()
    if templates is None or len(templates) == 0:
        return None
    best_match = None  # 最佳匹配信息
    best_val = 0  # 存储最佳匹配度
    h, w = image.shape[:2]  # 获取图像尺寸
    for i, template in enumerate(templates):
        t_h, t_w = template.shape[:2]  # 获取模板尺寸
        # 安全检查：确保图像尺寸大于等于模板尺寸
        if h >= t_h and w >= t_w:
            res = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
            if max_val > 0.8 and max_val > best_val:  # 找到最佳匹配
                best_val = max_val
                best_match = (i, max_loc)  # 记录最佳匹配的数字和位置
    return best_match


def capture_region(x, y, w, h, scr):
    region = (x, y, x + w, y + h)
    frame = scr.grab(region)
    if frame is None:
        return None
    img = np.array(frame)  # screenshot 是 ScreenShot 类型，转换为 NumPy 数组
    gray_img = cv2.cvtColor(img, cv2.COLOR_RGBA2GRAY)
    return gray_img


# 识别钓上鱼
def fished(scr):
    global region3_coords, star_template
    # 确保模板已加载
    if star_template is None:
        load_star_template()
    # 获取区域坐标并捕获灰度图
    region_gray = capture_region(*region3_coords, scr)  # 直接传递解包后的参数和scr
    if region_gray is None:
        return None
    # 执行模板匹配并检查最大匹配度是否大于 0.8
    h, w = region_gray.shape[:2]
    t_h, t_w = star_template.shape[:2]
    if h >= t_h and w >= t_w:
        return (
            cv2.minMaxLoc(
                cv2.matchTemplate(region_gray, star_template, cv2.TM_CCOEFF_NORMED)
            )[1]
            > 0.8
        )
    return False


def f1_mached(scr):
    global region4_coords, f1
    # 确保模板已加载
    if f1 is None:
        load_f1()
    region_gray = capture_region(*region4_coords, scr)
    if region_gray is None:
        return None
    h, w = region_gray.shape[:2]
    t_h, t_w = f1.shape[:2]
    if h >= t_h and w >= t_w:
        return (
            cv2.minMaxLoc(cv2.matchTemplate(region_gray, f1, cv2.TM_CCOEFF_NORMED))[1]
            > 0.8
        )
    return False


# 识别UNO条
def uno_recognize_tiao(scr):
    """识别UNO条模板

    Args:
        scr: 截图对象

    Returns:
        bool: 是否识别成功
    """
    global tiao_template
    # 确保模板已加载
    if tiao_template is None:
        print("⚠️ [UNO] 模板未加载，尝试重新加载...")
        load_tiao_template()

    if tiao_template is None:
        print("❌ [UNO] 模板加载失败，无法识别")
        return False

    # 2K分辨率(2560×1440)下的原始坐标
    base_x = 2242
    base_y = 1314
    base_width = 284
    base_height = 100

    # 使用与鱼饵识别相同的缩放逻辑，UI元素通常锚定在角落
    scaled_x, scaled_y, scaled_width, scaled_height = scale_position(
        base_x,
        base_y,
        base_width,
        base_height,
        anchor="bottom_right",
        coordinate_type="region",
    )

    # 捕获缩放后的区域
    region_gray = capture_region(scaled_x, scaled_y, scaled_width, scaled_height, scr)
    if region_gray is None:
        print(
            f"❌ [UNO] 区域捕获失败 (缩放后: {scaled_x}, {scaled_y}, {scaled_width}, {scaled_height})"
        )
        return False

    # 执行模板匹配
    h, w = region_gray.shape[:2]
    t_h, t_w = tiao_template.shape[:2]
    if h >= t_h and w >= t_w:
        match_result = cv2.minMaxLoc(
            cv2.matchTemplate(region_gray, tiao_template, cv2.TM_CCOEFF_NORMED)
        )[1]
        is_match = match_result > 0.8
        print(
            f"🎮 [UNO] 识别结果: {'成功' if is_match else '失败'} (匹配度: {match_result:.2f})"
        )
        return is_match
    return False


# 加载UNO条模板
def load_tiao_template():
    """加载UNO条模板

    Returns:
        numpy.ndarray: 加载的模板
    """
    global tiao_template
    if tiao_template is None:
        try:
            tiao_path = os.path.join(template_folder_path, "tiao.png")
            img = Image.open(tiao_path)

            # 无论原图是什么格式，都转换为灰度图像
            if img.mode != "L":
                img = img.convert("L")

            template = np.array(img)
            scale = SCALE_UNIFORM
            tiao_template = scale_template(template, scale, scale)

            # 确保模板是CV_8U格式（8位无符号整数）
            if tiao_template.dtype != np.uint8:
                tiao_template = tiao_template.astype(np.uint8)
                print(f"🔧 [UNO] 模板格式转换: {tiao_template.dtype} → uint8")

            # 确保模板是单通道灰度图像
            if len(tiao_template.shape) > 2:
                tiao_template = cv2.cvtColor(tiao_template, cv2.COLOR_BGR2GRAY)
                print(f"🔧 [UNO] 模板通道转换: {tiao_template.shape} → 单通道")

            print("✅ [UNO] 模板加载成功")
        except Exception as e:
            print(f"❌ [UNO] 模板加载失败: {e}")
            tiao_template = None
    return tiao_template


# 计算UNO点击位置
def calculate_click_position():
    """根据当前分辨率计算UNO点击位置

    Returns:
        tuple: (x, y) 点击位置
    """
    # 2K分辨率(2560×1440)下的原始位置
    base_x = 2381
    base_y = 1353

    # 获取当前分辨率
    current_width, current_height = get_current_screen_resolution()

    # 使用与鱼饵识别相同的缩放逻辑，UI元素通常锚定在角落
    scaled_x, scaled_y = scale_position(
        base_x, base_y, anchor="bottom_right", coordinate_type="point"
    )

    print(
        f"🎮 [UNO] 分辨率 {current_width}×{current_height}，缩放比例 X={SCALE_X:.2f}, Y={SCALE_Y:.2f}，点击位置: ({scaled_x}, {scaled_y})"
    )
    return (scaled_x, scaled_y)


# UNO主处理函数
def uno_process(scr):
    """处理UNO卡识别和计数

    Args:
        scr: 截图对象

    Returns:
        bool: 是否处理成功
    """
    global uno_input1_var, uno_input2_var

    # 检查变量是否已初始化
    if uno_input1_var is None or uno_input2_var is None:
        print("❌ [UNO] 计数变量未初始化")
        return False

    # 识别UNO条
    if uno_recognize_tiao(scr):
        # 获取当前牌数和抽取牌数
        current_cards = uno_input1_var.get()
        max_cards = uno_input2_var.get()

        print(f"🎮 [UNO] 当前牌数: {current_cards}, 抽取牌数: {max_cards}")

        # 当前牌数+1
        new_cards = current_cards + 1
        uno_input1_var.set(new_cards)
        print(f"🎮 [UNO] 牌数更新: {current_cards} → {new_cards}")

        # 检查是否达到抽取牌数且未显示过弹窗
        if new_cards >= max_cards and not uno_popup_shown:
            print(f"🎮 [UNO] 已达到抽取牌数: {new_cards}/{max_cards}")
            # 显示弹窗并获取用户选择
            continue_operation = uno_show_popup()
            # 如果用户选择暂停，返回False
            if not continue_operation:
                print(f"🎮 [UNO] 已暂停操作")
                return False

        return True
    return False


# UNO持续识别函数
def uno_continuous_recognition():
    """持续识别UNO卡并执行点击操作

    该函数在单独线程中运行，直到uno_recognition_running为False
    """
    global uno_recognition_running

    print("🎮 [UNO] 开始持续识别")

    import time
    import mss

    # 创建截图对象
    scr = mss.mss()

    try:
        while uno_recognition_running:
            # 识别UNO条
            if uno_recognize_tiao(scr):
                # 获取当前牌数和抽取牌数
                current_cards = uno_input1_var.get()
                max_cards = uno_input2_var.get()

                print(f"🎮 [UNO] 当前牌数: {current_cards}, 抽取牌数: {max_cards}")

                # 当前牌数+1并执行点击
                new_cards = current_cards + 1
                uno_input1_var.set(new_cards)
                print(f"🎮 [UNO] 牌数更新: {current_cards} → {new_cards}")

                # 计算点击位置
                click_x, click_y = calculate_click_position()

                # 执行点击操作
                mouse_controller.position = (click_x, click_y)
                mouse_controller.click(mouse.Button.left, 1)
                print(f"🎮 [UNO] 执行点击: ({click_x}, {click_y})")

                # 检查是否达到抽取牌数且未显示过弹窗
                if new_cards >= max_cards and not uno_popup_shown:
                    print(f"🎮 [UNO] 已达到抽取牌数: {new_cards}/{max_cards}")
                    # 显示弹窗并获取用户选择
                    continue_operation = uno_show_popup()
                    # 如果用户选择暂停，停止持续识别
                    if not continue_operation:
                        print(f"🎮 [UNO] 已暂停持续识别")
                        uno_recognition_running = False

            # 延迟一段时间，避免过于频繁的识别
            time.sleep(0.5)
    except Exception as e:
        print(f"❌ [UNO] 持续识别出错: {e}")
    finally:
        # 关闭截图对象
        scr.close()
        print("🎮 [UNO] 持续识别停止")


# 启动UNO持续识别
def uno_start_continuous_recognition():
    """启动UNO持续识别

    该函数负责创建和启动持续识别线程
    """
    global uno_recognition_running, uno_recognition_thread, uno_input1_var, uno_popup_shown

    if not uno_recognition_running:
        # 重置当前牌数为7
        uno_input1_var.set(7)
        print("🎮 [UNO] 当前牌数已重置为7")

        # 重置弹窗显示标志位
        uno_popup_shown = False

        # 设置识别状态为True
        uno_recognition_running = True

        # 创建并启动线程
        import threading

        uno_recognition_thread = threading.Thread(
            target=uno_continuous_recognition, daemon=True
        )
        uno_recognition_thread.start()

        print("🎮 [UNO] 持续识别已启动")
        return True
    else:
        print("🎮 [UNO] 持续识别已在运行")
        return False


# 停止UNO持续识别
def uno_stop_continuous_recognition():
    """停止UNO持续识别

    该函数负责停止持续识别线程
    """
    global uno_recognition_running, uno_recognition_thread

    if uno_recognition_running:
        # 设置识别状态为False
        uno_recognition_running = False

        # 等待线程结束
        if uno_recognition_thread is not None:
            uno_recognition_thread.join(timeout=1.0)  # 等待1秒
            uno_recognition_thread = None

        print("🎮 [UNO] 持续识别已停止")
        return True
    else:
        print("🎮 [UNO] 持续识别未在运行")
        return False


# UNO弹窗函数
def uno_show_popup():
    """显示UNO暂停/继续弹窗

    弹窗5秒后自动选择继续
    """
    # 不直接使用global root，改为检查root是否已定义
    global root, uno_popup_shown
    if root is None:
        print("⚠️ [UNO] 无法显示弹窗，root未定义")
        return

    # 弹窗显示后设置标志位为True
    uno_popup_shown = True

    # 创建弹窗
    popup = tk.Toplevel(root)
    popup.title("🎮 UNO 提示")
    popup.geometry("300x150")
    popup.resizable(False, False)
    popup.grab_set()  # 模态窗口
    popup.attributes("-topmost", True)  # 弹窗置顶显示

    # 设置样式
    popup.configure(background="#2d3748")

    # 添加标题
    title_label = ttkb.Label(
        popup,
        text="🎮 UNO 操作提示",
        font=("Segoe UI", 12, "bold"),
        bootstyle="primary",
    )
    title_label.pack(pady=15)

    # 添加提示文本
    text_label = ttkb.Label(
        popup, text="是否继续操作？", font=("Segoe UI", 10), bootstyle="light"
    )
    text_label.pack(pady=5)

    # 继续标志
    continue_flag = [False]

    # 暂停按钮回调
    def on_pause():
        continue_flag[0] = False
        print("🎮 [UNO] 用户选择暂停")
        popup.destroy()

    # 继续按钮回调
    def on_continue():
        continue_flag[0] = True
        print("🎮 [UNO] 用户选择继续")
        popup.destroy()

    # 按钮框架
    btn_frame = ttkb.Frame(popup)
    btn_frame.pack(pady=20)

    # 暂停按钮
    pause_btn = ttkb.Button(
        btn_frame, text="暂停", bootstyle="danger", width=10, command=on_pause
    )
    pause_btn.pack(side=LEFT, padx=10)

    # 继续按钮
    continue_btn = ttkb.Button(
        btn_frame, text="继续", bootstyle="success", width=10, command=on_continue
    )
    continue_btn.pack(side=RIGHT, padx=10)

    # 设置5秒自动继续
    popup.after(5000, on_continue)

    # 等待弹窗关闭
    popup.wait_window()

    return continue_flag[0]


def f2_mached(scr):
    global region5_coords, f2
    # 确保模板已加载
    if f2 is None:
        load_f2()
    region_gray = capture_region(*region5_coords, scr)
    if region_gray is None:
        return None
    h, w = region_gray.shape[:2]
    t_h, t_w = f2.shape[:2]
    if h >= t_h and w >= t_w:
        return (
            cv2.minMaxLoc(cv2.matchTemplate(region_gray, f2, cv2.TM_CCOEFF_NORMED))[1]
            > 0.8
        )
    return False


def shangyu_mached(scr):
    global region6_coords, shangyule
    # 确保模板已加载
    if shangyule is None:
        load_shangyule()
    region_gray = capture_region(*region6_coords, scr)
    if region_gray is None:
        return None
    h, w = region_gray.shape[:2]
    t_h, t_w = shangyule.shape[:2]
    if h >= t_h and w >= t_w:
        return (
            cv2.minMaxLoc(
                cv2.matchTemplate(region_gray, shangyule, cv2.TM_CCOEFF_NORMED)
            )[1]
            > 0.8
        )
    return False


def fangzhu_jiashi(scr):
    global jiashi
    # 记录日志：开始加时识别
    if debug_mode:
        debug_info = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "action": "jiashi_recognition_start",
            "message": "开始识别加时界面",
        }
        add_debug_info(debug_info)

    # 确保模板已加载
    if jiashi is None:
        jiashi = load_jiashi()
    
    # 检查模板是否成功加载
    if jiashi is None:
        return False

    # 确保加时区域坐标已初始化
    if jiashi_region_coords is None:
        update_region_coords()

    # 使用缓存的坐标
    actual_x, actual_y, actual_w, actual_h = jiashi_region_coords

    # 记录日志：识别区域
    if debug_mode:
        debug_info = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "action": "jiashi_recognition_region",
            "message": "加时识别区域",
            "region": {
                "x1": actual_x,
                "y1": actual_y,
                "x2": actual_x + actual_w,
                "y2": actual_y + actual_h,
            },
        }
        add_debug_info(debug_info)

    region_gray = capture_region(actual_x, actual_y, actual_w, actual_h, scr)
    if region_gray is None:
        # 记录日志：识别失败
        if debug_mode:
            debug_info = {
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
                "action": "jiashi_recognition_failed",
                "message": "无法获取加时区域图像",
            }
            add_debug_info(debug_info)
        return False

    # 安全检查：确保图像尺寸大于等于模板尺寸
    h, w = region_gray.shape[:2]
    t_h, t_w = jiashi.shape[:2]
    if h >= t_h and w >= t_w:
        # 降低匹配阈值，提高识别率
        match_result = cv2.matchTemplate(region_gray, jiashi, cv2.TM_CCOEFF_NORMED)
        max_val = cv2.minMaxLoc(match_result)[1]
        result = max_val > 0.8  # 降低阈值到0.8
    else:
        result = False

    # 记录日志：识别结果
    if debug_mode:
        debug_info = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "action": "jiashi_recognition_result",
            "message": "加时识别完成",
            "result": "是" if result else "否",
            "parsed_info": {"加时界面": "已识别" if result else "未识别"},
        }
        add_debug_info(debug_info)

    return result


# =========================
# 程序主循环与热键监听
# =========================
def toggle_run():
    global a, previous_result, scr
    if run_event.is_set():
        run_event.clear()  # 暂停
        a = 0
        previous_result = None
        ensure_mouse_up()  # 确保鼠标没有按下
        end_current_session()  # 结束钓鱼会话

        # 播放暂停音效
        sound_manager.play_pause()

        print("⏸️  [状态] 脚本已暂停")

    else:
        # 重置鱼桶满检测状态
        reset_fish_bucket_full_detection()

        start_new_session()  # 开始新的钓鱼会话
        if previous_result is None:
            temp_scr = None
            try:
                temp_scr = mss.mss()
                bait_result = bait_math_val(temp_scr)
                if bait_result is not None:
                    previous_result = result_val_is
                    run_event.set()  # 恢复运行

                    # 播放启动音效
                    sound_manager.play_start()

                    print("▶️  [状态] 脚本开始运行")

                else:
                    time.sleep(0.1)
                    print("⚠️  [警告] 未识别到鱼饵，请确保游戏界面正确")
            except Exception as e:
                print(f"❌ [错误] 初始化失败: {e}")
            finally:
                if temp_scr is not None:
                    try:
                        temp_scr.close()
                    except:
                        pass
                scr = None
        else:
            run_event.set()
            # 播放恢复音效
            sound_manager.play_resume()
            print("▶️  [状态] 脚本继续运行")


def on_press(key):
    global current_modifiers
    time.sleep(0.02)

    # 检查是否是修饰键
    if key in MODIFIER_KEYS:
        current_modifiers.add(MODIFIER_KEYS[key])
        return

    # 检查是否匹配热键
    check_hotkey_match(key)


def on_release(key):
    global current_modifiers
    # 释放修饰键时移除
    if key in MODIFIER_KEYS:
        current_modifiers.discard(MODIFIER_KEYS[key])


def on_mouse_press(x, y, button, pressed):
    """鼠标按下事件处理"""
    if not pressed:
        return

    # 检查是否匹配热键
    check_hotkey_match(button)


def check_hotkey_match(key):
    """检查按键是否匹配热键"""
    # 比较主按键
    main_key_match = False
    uno_key_match = False

    # 直接比较按键对象
    if key == hotkey_main_key:
        main_key_match = True
    if key == uno_hotkey_main_key:
        uno_key_match = True

    # 虚拟键码比较
    elif hasattr(key, "vk"):
        # 检查主热键
        if hasattr(hotkey_main_key, "vk") and hotkey_main_key.vk is not None:
            if key.vk is not None:
                main_key_match = key.vk == hotkey_main_key.vk
        # 检查UNO热键
        if hasattr(uno_hotkey_main_key, "vk") and uno_hotkey_main_key.vk is not None:
            if key.vk is not None:
                uno_key_match = key.vk == uno_hotkey_main_key.vk

    # 字符键比较（忽略大小写）
    elif hasattr(key, "char") and key.char:
        # 检查主热键
        if hasattr(hotkey_main_key, "char") and hotkey_main_key.char:
            main_key_match = key.char.lower() == hotkey_main_key.char.lower()
        # 检查UNO热键
        if hasattr(uno_hotkey_main_key, "char") and uno_hotkey_main_key.char:
            uno_key_match = key.char.lower() == uno_hotkey_main_key.char.lower()

    # 鼠标按键比较
    elif isinstance(key, mouse.Button):
        # 检查主热键
        if isinstance(hotkey_main_key, mouse.Button):
            main_key_match = key == hotkey_main_key
        # 检查UNO热键
        if isinstance(uno_hotkey_main_key, mouse.Button):
            uno_key_match = key == uno_hotkey_main_key

    # 处理主热键匹配
    if main_key_match:
        # 检查修饰键是否匹配
        if current_modifiers == hotkey_modifiers:
            toggle_run()  # 暂停或恢复程序
            return

    # 处理UNO热键匹配
    if uno_key_match:
        # 检查修饰键是否匹配
        if current_modifiers == uno_hotkey_modifiers:
            print(f"🎮 [UNO] 热键 {uno_hotkey_name} 被触发")
            # 切换持续识别状态
            global uno_recognition_running
            if uno_recognition_running:
                # 如果正在识别，停止识别
                uno_stop_continuous_recognition()
                print("🎮 [UNO] 已停止持续识别")
            else:
                # 如果未在识别，启动识别
                uno_start_continuous_recognition()
                print("🎮 [UNO] 已启动持续识别")
            return


def start_hotkey_listener():
    global listener, mouse_listener
    # 启动键盘监听器，设置suppress=False允许事件传递，确保全局监听
    if listener is None or not listener.running:
        listener = keyboard.Listener(
            on_press=on_press,
            on_release=on_release,
            suppress=False,  # 不抑制事件，允许其他应用程序接收按键
        )
        listener.daemon = True
        listener.start()

    # 启动鼠标监听器
    if (
        "mouse_listener" not in globals()
        or mouse_listener is None
        or not mouse_listener.running
    ):
        mouse_listener = mouse.Listener(
            on_click=on_mouse_press,
            suppress=False,  # 不抑制事件，允许其他应用程序接收鼠标事件
        )
        mouse_listener.daemon = True
        mouse_listener.start()


# =========================
# 主函数
# =========================
# 主函数：定时识别并比较数字
def handle_jiashi_thread():
    global run_event, previous_result, result_val_is
    while True:
        if run_event.is_set():
            try:
                # 为每个线程创建独立的mss对象
                scr = mss.mss()

                # 确保scr对象和_handles属性正确初始化
                if (
                    hasattr(scr, "_handles")
                    and hasattr(scr._handles, "srcdc")
                    and scr._handles.srcdc is not None
                ):
                    # 处理加时选择（使用锁保护读取jiashi_var）
                    with param_lock:
                        current_jiashi = jiashi_var

                    if current_jiashi == 0:
                        if fangzhu_jiashi(scr):
                            # 确保按钮坐标已初始化
                            if btn_no_jiashi_coords is None:
                                update_region_coords()
                            btn_x, btn_y = btn_no_jiashi_coords
                            user32.SetCursorPos(btn_x, btn_y)
                            time.sleep(0.05)
                            user32.mouse_event(0x02, 0, 0, 0, 0)
                            time.sleep(0.1)
                            user32.mouse_event(0x04, 0, 0, 0, 0)
                            time.sleep(0.05)
                            if bait_math_val(scr):
                                with param_lock:
                                    previous_result = result_val_is
                    elif current_jiashi == 1:
                        if fangzhu_jiashi(scr):
                            # 确保按钮坐标已初始化
                            if btn_yes_jiashi_coords is None:
                                update_region_coords()
                            btn_x, btn_y = btn_yes_jiashi_coords
                            user32.SetCursorPos(btn_x, btn_y)
                            time.sleep(0.05)
                            user32.mouse_event(0x02, 0, 0, 0, 0)
                            time.sleep(0.1)
                            user32.mouse_event(0x04, 0, 0, 0, 0)
                            time.sleep(0.05)
                            if bait_math_val(scr):
                                with param_lock:
                                    previous_result = result_val_is

                # 确保资源被正确释放
                scr.close()
            except Exception as e:
                print(f"❌ [错误] 加时线程异常: {e}")
                # 确保即使发生异常也能释放资源
                try:
                    if "scr" in locals() and scr is not None:
                        scr.close()
                except:
                    pass
        time.sleep(0.05)


def main():
    global templates, template_folder_path, current_result, previous_result, times, a, region1, region2, result_val_is, scr, jiashi_var

    # 启动加时处理线程
    jiashi_thread = threading.Thread(target=handle_jiashi_thread, daemon=True)
    jiashi_thread.start()

    # 启动鱼桶满独立检测线程
    bucket_full_thread = threading.Thread(
        target=bucket_full_detection_thread, daemon=True
    )
    bucket_full_thread.start()

    while True:
        if run_event.is_set():
            scr = None
            try:
                # 创建新的截图对象，确保每次都是新鲜的
                scr = mss.mss()

                # 检查截图对象是否有效
                if scr is None:
                    print("⚠️  [警告] 截图对象创建失败")
                    time.sleep(0.1)
                    continue

                # 先检查是否需要处理加时
                if handle_jiashi_in_action(scr):
                    # 确保释放截图对象
                    try:
                        scr.close()
                    except:
                        pass
                    scr = None
                    continue

                # 检测F1/F2抛竿
                if f1_mached(scr) or f2_mached(scr):
                    # 检查是否正在放生，如果是则等待
                    with operation_lock:
                        if is_releasing:
                            print("⏳ [提示] 正在放生，等待放生完成后再抛杆")
                            time.sleep(0.5)
                            continue
                        # 设置抛杆状态
                        is_casting = True
                    
                    try:
                        # 在这里记录抛竿时间
                        current_time = time.time()
                        with casting_interval_lock:
                            casting_timestamps.append(current_time)
                            # 保持队列长度，防止内存泄露
                            if len(casting_timestamps) > 20:
                                casting_timestamps.pop(0)
                        user32.mouse_event(0x02, 0, 0, 0, 0)
                        jittered_pao = add_jitter(paogantime)
                        time.sleep(jittered_pao)
                        print_timing_info("抛竿", paogantime, jittered_pao)
                        user32.mouse_event(0x04, 0, 0, 0, 0)
                        time.sleep(0.15)
                    finally:
                        # 无论是否异常，都要重置抛杆状态
                        with operation_lock:
                            is_casting = False
                elif shangyu_mached(scr):
                    user32.mouse_event(0x02, 0, 0, 0, 0)
                    time.sleep(0.1)
                    user32.mouse_event(0x04, 0, 0, 0, 0)

                time.sleep(0.05)

                # 获取当前结果
                bait_result = bait_math_val(scr)
                if bait_result is not None:
                    current_result = result_val_is
                else:
                    current_result = previous_result  # 将当前数字设为上次的数字
                    time.sleep(0.1)
                    # 确保释放截图对象
                    try:
                        scr.close()
                    except:
                        pass
                    scr = None
                    continue

                # 比较并执行操作
                comparison_result = compare_results()
                time.sleep(0.01)

                if comparison_result == -1:  # 当前结果小于上次结果
                    previous_result = current_result  # 更新上次识别的结果
                    while not fished(scr) and run_event.is_set():
                        # 使用锁保护读取times
                        with param_lock:
                            current_times = times
                        if a <= current_times:
                            a += 1
                            # 调用优化后的点击循环函数，如果返回False表示遇到异常需中断
                            if not pressandreleasemousebutton():
                                a = 0
                                break
                        else:
                            a = 0
                            print("🎣 [提示] 达到最大拉杆次数，本轮结束")
                            break
                    ensure_mouse_up()
                    a = 0

                    # 钓到鱼后，识别并记录鱼的信息
                    if OCR_AVAILABLE and record_fish_enabled:
                        try:
                            record_caught_fish()
                        except Exception as e:
                            print(f"⚠️  [警告] 记录鱼信息失败: {e}")
                elif comparison_result == 1:
                    previous_result = current_result
                    # continue会在finally中关闭scr
            except Exception as e:
                print(f"❌ [错误] 主循环异常: {e}")
                # 记录更详细的错误信息
                import traceback

                traceback.print_exc()
            finally:
                # 确保mss资源被正确释放
                if scr is not None:
                    try:
                        scr.close()
                    except:
                        pass
                    scr = None
        time.sleep(0.1)


# =========================
# 程序入口
# =========================
if __name__ == "__main__":
    # 卡密验证 - 在所有初始化之前执行
    verify_card_key()
    
    # 先加载参数以获取热键设置
    load_parameters()

    print()
    print("╔" + "═" * 50 + "╗")
    print("║" + " " * 50 + "║")
    print("║     🎣  PartyFish 自动钓鱼助手  v.2.12".ljust(44) + "║")
    print("║" + " " * 50 + "║")
    print("╠" + "═" * 50 + "╣")
    print(
        f"║  📺 当前分辨率: {CURRENT_SCREEN_WIDTH}×{CURRENT_SCREEN_HEIGHT}".ljust(45)
        + "║"
    )
    print(f"║  ⌨️ 快捷键: {hotkey_name}启动/暂停脚本".ljust(43) + "║")
    print(f"║  🎲 时间抖动: ±{JITTER_RANGE}%".ljust(46) + "║")
    print(
        f"║  🪣 鱼桶满检测: {'✅ 已启用' if OCR_AVAILABLE else '❌ 未启用'}".ljust(46)
        + "║"
    )
    print(
        f"║  🎯 鱼饵识别算法: {bait_recognition_algorithms[bait_recognition_algorithm]}".ljust(
            47
        )
        + "║"
    )
    print("║  🔧 开发者: FadedTUMI/PeiXiaoXiao/MaiDong".ljust(47) + "║")
    print("╚" + "═" * 50 + "╝")
    print()

    # 加载参数和模板
    print("📦 [初始化] 配置加载完成")

    # 加载历史钓鱼记录
    print("📊 [初始化] 正在加载钓鱼记录...")
    load_all_fish_records()

    print("🖼️  [初始化] 正在加载图像模板...")
    load_templates()
    load_star_template()
    load_f1()
    load_f2()
    load_shangyule()
    load_jiashi()
    print("✅ [初始化] 模板加载完成")

    # 启动热键监听
    print("🎮 [初始化] 正在启动热键监听...")
    start_hotkey_listener()
    print("✅ [初始化] 热键监听已启动")

    print()
    print("┌" + "─" * 48 + "┐")
    print(f"│  🚀 程序已就绪，按 {hotkey_name} 开始自动钓鱼！".ljust(34) + "│")
    print("└" + "─" * 48 + "┘")
    print()

    # 将main()放在后台线程运行（daemon=True确保主线程退出时自动结束）
    main_thread = threading.Thread(target=main, daemon=True)
    main_thread.start()

    # GUI必须在主线程运行（Tkinter要求）
    # 这样可以确保GUI正常工作且不会崩溃
    try:
        create_gui()
    except KeyboardInterrupt:
        # 优雅处理Ctrl+C中断，确保程序能够正常退出
        print("\n\n┌" + "─" * 48 + "┐")
        print("│  🛑  程序已通过Ctrl+C中断                      │")
        print("└" + "─" * 48 + "┘")
        # 确保所有资源都能正确释放
        pass
