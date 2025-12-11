# 🎣 PartyFish - 自动钓鱼助手

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)
![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)

**PartyFish** 是一款基于图像识别的游戏自动钓鱼工具，支持多分辨率适配、钓鱼记录统计和现代化GUI界面。

</div>

---

## ✨ 功能特性

- 🖥️ **多分辨率支持** - 支持 1080P、2K、4K 及自定义分辨率
- 🎯 **智能图像识别** - 基于 OpenCV 模板匹配，精准识别游戏状态
- 📊 **钓鱼记录系统** - 自动记录钓鱼成果，支持按品质筛选和搜索
- 🔤 **OCR 识别** - 使用 RapidOCR 识别鱼的名称、品质和重量
- 💾 **参数持久化** - 自动保存配置参数，下次启动自动加载
- 🎨 **现代化界面** - 基于 ttkbootstrap 的深色主题 GUI
- ⌨️ **热键控制** - F2 一键启动/暂停

---

## 📦 环境要求

### 系统要求
- **操作系统**: Windows 10/11
- **Python 版本**: 3.8+

### 依赖库

```bash
pip install pyautogui opencv-python numpy pillow pynput ttkbootstrap mss rapidocr-onnxruntime
```

| 依赖库 | 用途 |
|--------|------|
| `pyautogui` | 鼠标键盘自动化控制 |
| `opencv-python` | 图像处理与模板匹配 |
| `numpy` | 数组计算 |
| `pillow` | 图像加载处理 |
| `pynput` | 全局键盘监听 |
| `ttkbootstrap` | 现代化 GUI 界面 |
| `mss` | 高速屏幕截图 |
| `rapidocr-onnxruntime` | OCR 文字识别（可选） |

---

## 🚀 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/FADEDTUMI/PartyFish.git
cd PartyFish
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

或手动安装：

```bash
pip install pyautogui opencv-python numpy pillow pynput ttkbootstrap mss rapidocr-onnxruntime
```

### 3. 运行程序

```bash
python PartyFish.py
```

### 4. 使用方法

1. 启动程序后，会显示 GUI 配置界面
2. 根据游戏调整参数（或使用默认值）
3. 切换到游戏窗口，确保钓鱼界面可见
4. 按 **F2** 键启动自动钓鱼
5. 再次按 **F2** 键暂停

---

## ⚙️ 参数配置说明

### 钓鱼参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| 循环间隔 | 0.3 秒 | 主循环检测间隔时间 |
| 收线时间 | 2.5 秒 | 鼠标左键按下持续时间 |
| 放线时间 | 2.0 秒 | 鼠标左键释放后等待时间 |
| 最大拉杆次数 | 15 次 | 单次钓鱼最大拉杆循环次数 |
| 抛竿时间 | 0.5 秒 | 抛竿时鼠标按下持续时间 |

### 分辨率设置

程序默认以 **2K (2560×1440)** 为基准分辨率设计，支持以下预设：

- **1080P**:  1920 × 1080
- **2K**:  2560 × 1440
- **4K**:  3840 × 2160
- **自定义**: 手动输入宽高

### 加时选项

- **是**:  自动点击加时按钮
- **否**: 自动点击不加时按钮

---

## 📁 项目结构

```
PartyFish/
├── PartyFish.py          # 主程序文件
├── parameters.json       # 参数配置文件（自动生成）
├── fish_records. txt      # 钓鱼记录文件（自动生成）
├── resources/            # 模板图像资源目录
│   ├── 0-9_grayscale.png # 数字识别模板
│   ├── F1_grayscale.png  # F1 按键模板
│   ├── F2_grayscale. png  # F2 按键模板
│   ├── star_grayscale. png # 星星（上鱼）模板
│   ├── shangyu_grayscale.png # 上鱼图标模板
│   └── chang_grayscale. png   # 加时界面模板
├── LICENSE               # Apache 2.0 许可证
└── README.md             # 说明文档
```

---

## 🐟 钓鱼记录系统

程序集成了完整的钓鱼记录功能：

### 品质等级

| 品质 | 图标 | 显示颜色 |
|------|------|----------|
| 标准 | ⚪ | 白色背景 |
| 非凡 | 🟢 | 绿色背景 |
| 稀有 | 🔵 | 蓝色背景 |
| 史诗 | 🟣 | 紫色背景 |
| 传说 | 🟡 | 橙色背景 |

### 记录功能

- **本次钓鱼**: 查看当前会话的钓鱼成果
- **历史总览**: 查看所有历史记录
- **搜索功能**:  按鱼名关键词搜索
- **品质筛选**: 按品质等级筛选记录

> ⚠️ **注意**: OCR 功能需要安装 `rapidocr-onnxruntime`，未安装时钓鱼记录功能将不可用。

---

## 🔧 工作原理

1. **鱼饵数量检测**: 通过模板匹配识别屏幕上的鱼饵数量
2. **状态变化检测**: 当鱼饵数量减少时，判断为有鱼上钩
3. **自动拉杆**: 执行收线/放线循环操作
4. **上鱼检测**: 识别星星图标判断钓鱼成功
5. **OCR 识别**:  识别捕获的鱼的信息并记录

---

## ⚠️ 注意事项

1. **管理员权限**:  某些游戏可能需要以管理员身份运行程序
2. **窗口模式**: 建议游戏使用窗口化或无边框窗口模式
3. **分辨率匹配**: 请确保选择与游戏实际分辨率匹配的设置
4. **模板图像**: 如识别不准确，可能需要重新截取模板图像

---

## 🛠️ 故障排除

| 问题 | 解决方案 |
|------|----------|
| 未识别到鱼饵 | 检查分辨率设置是否正确 |
| 无法抛竿 | 确保游戏窗口处于前台 |
| OCR 不工作 | 安装 rapidocr-onnxruntime |
| GUI 无响应 | 检查 ttkbootstrap 是否正确安装 |

---

## 📝 许可证

本项目采用 [Apache License 2.0](LICENSE) 许可证。

---

## 👤 开发者

**FadedTUMI** - [GitHub](https://github.com/FADEDTUMI)

---

<div align="center">

⭐ 如果这个项目对你有帮助，请给一个 Star！

</div>
