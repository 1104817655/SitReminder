# SitReminder 使用说明（v1.2）

SitReminder 是一个 Windows 桌面久坐提醒工具（托盘常驻），帮助你在工作时保持规律活动，减少长时间久坐。

## 当前实现（v1.2）
- 久坐计时提醒，支持自定义间隔。
- 支持两种模式：
  - 智能提醒模式（按提醒间隔触发）
  - 节律模式（工作 X 分钟 -> 休息 Y 分钟自动循环）
- 双阶段提醒：预提醒 + 正式提醒。
- 正式提醒弹窗：`开始休息`、`稍后提醒`、`本次自定义稍后`、`跳过本次`。
- 预提醒可切换为右下角小弹窗（自动消失）或托盘消息。
- 连续延期上限控制，达到上限后进入强提醒（禁用“稍后提醒”）。
- 工作时段与午休免打扰。
- 键鼠空闲超过阈值后自动重置计时。
- 全屏或会议应用前台时自动静默，结束后补发提醒。
- 托盘菜单：开启/关闭、暂停 30 分钟、今日不提醒、立即休息、今日统计、设置、退出。
- 托盘支持双击直接打开设置，首次启动会自动弹出设置引导。
- 托盘 tooltip 实时显示状态（运行/暂停/静默）与下次提醒时间。
- 今日统计面板：提醒次数、休息次数、延期次数、跳过次数、静默补发次数、空闲重置次数、执行率。
- 系统长暂停或唤醒后会自动重算计时，减少误提醒。
- 设置保存前会校验关键参数（如预提醒必须小于提醒间隔）。
- 节律模式下休息结束会弹提示，并自动进入下一轮工作。
- 开机自启开关（Windows 注册表 `HKCU\...\Run`）。
- 配置持久化（本地 JSON）与日志文件。

## 默认配置
- 提醒间隔：60 分钟
- 预提醒：提前 2 分钟
- 休息时长：3 分钟
- 稍后提醒选项：5/10/15 分钟
- 连续延期上限：3 次
- 空闲重置阈值：5 分钟
- 工作时段：09:00-18:00
- 午休免打扰：12:00-13:30

## 参数自定义范围（v1.2）
- 提醒间隔：15-240 分钟
- 节律工作时长：15-240 分钟
- 节律休息时长：1-60 分钟
- 预提醒提前：0-30 分钟（0 表示关闭）
- 预提醒弹窗停留：3-60 秒
- 休息时长：1-60 分钟
- 稍后提醒选项：1-240 分钟（支持自定义列表）
- 默认稍后：1-240 分钟
- 连续延期上限：1-20 次
- 空闲重置阈值：1-180 分钟

## 运行环境
- Windows 10/11
- Python 3.10+

## 本地运行
1. 安装依赖：
```bash
pip install -r requirements.txt
```
2. 启动程序：
```bash
python main.py
```
或直接双击 `run.bat`。

## 打包为 EXE
1. 双击 `build_exe.bat`。
2. 打包完成后，程序位于：
`dist\SitReminder\SitReminder.exe`

说明：
- 已配置应用图标：`resources\icon.ico`
- 打包脚本会自动把 `resources` 目录打进产物
- 这是目录版（onedir），分发时需要整个 `dist\SitReminder\` 文件夹一起拷贝

## EXE 构建模式
- 目录便携版（推荐稳定性）：
  - 脚本：`build_exe_portable.bat`
  - 产物：`dist\SitReminder\SitReminder.exe`
  - 分发方式：打包整个 `dist\SitReminder\` 文件夹
- 单文件版（便于分发）：
  - 脚本：`build_exe_single.bat`
  - 产物：`dist\SitReminder.exe`
  - 分发方式：可直接发送单个 exe（首次启动稍慢是正常现象）

## 生成安装包（Inno Setup）
1. 先执行 `build_exe.bat`。
2. 安装 Inno Setup 6，并确保 `iscc` 可在命令行使用。
3. 双击 `build_installer.bat`。
4. 安装包输出路径：
`dist\installer\SitReminder-Setup.exe`

## 一键构建（推荐）
- 直接双击 `build_all.bat`。
- 它会自动按顺序执行：
  - 生成 EXE
  - 生成安装包
- 成功后产物路径：
  - `dist\SitReminder\SitReminder.exe`
  - `dist\installer\SitReminder-Setup.exe`

## 卸载流程
1. 打开 Windows 设置 -> 应用 -> 已安装的应用。
2. 找到 `SitReminder`，点击卸载。
3. 卸载程序会移除安装目录与快捷方式。

用户配置与日志默认保留（便于重装恢复）：
- 配置：`%LOCALAPPDATA%\SitReminder\config.json`
- 统计：`%LOCALAPPDATA%\SitReminder\stats.json`
- 日志：`%LOCALAPPDATA%\SitReminder\logs\sitreminder.log`

如需彻底清理，可手动删除 `%LOCALAPPDATA%\SitReminder` 目录。

## 托盘菜单说明
- 启用提醒：总开关。
- 暂停 30 分钟：临时免打扰。
- 今日不提醒：当天剩余时间停止提醒。
- 立即开始休息：立即进入休息状态。
- 今日统计：查看当天提醒与执行数据。
- 打开设置：修改时间与行为参数。
- 退出：关闭程序。

## 常见问题
### 为什么没有提醒？
- 不在工作时段内。
- 处于午休免打扰时段。
- 你在托盘中关闭了提醒或选择了“今日不提醒”。
- 当前处于全屏/会议应用前台，提醒被静默并延后。

### 为什么计时会重置？
- 键鼠空闲超过设定阈值（默认 5 分钟）会自动重置，视为你已离开工位。

### 配置会丢失吗？
- 不会。程序会把设置写入本地配置文件，重启后自动生效。

## 项目结构
```text
SitReminder/
├─ main.py                 # 根入口（用于本地运行与打包）
├─ src/
│  ├─ main.py              # 主程序入口与调度逻辑
│  ├─ config.py            # 配置模型与持久化
│  ├─ reminder_dialog.py   # 正式提醒弹窗
│  ├─ pre_reminder_popup.py # 预提醒小弹窗
│  ├─ rest_finished_popup.py # 休息结束小弹窗
│  ├─ settings_dialog.py   # 设置窗口
│  ├─ stats_store.py       # 今日统计数据存储
│  ├─ stats_dialog.py      # 今日统计面板
│  ├─ windows_state.py     # Windows 空闲/全屏/前台进程检测
│  ├─ windows_startup.py   # 开机自启设置
│  └─ logging_setup.py     # 日志初始化
├─ resources/
│  └─ icon.ico
├─ installer/
│  └─ SitReminder.iss      # Inno Setup 脚本
├─ requirements.txt
├─ run.bat
├─ build_exe.bat
├─ build_exe_portable.bat
├─ build_exe_single.bat
├─ build_installer.bat
├─ build_all.bat
├─ SitReminder.md
└─ README.md
```
