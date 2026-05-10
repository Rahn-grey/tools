# 为什么写这个工具
在进几个学期学校引入了一个登录认证系统，有线接入的网络需要强制进行portal认证。 但是会话的存活时间很短占，需要保留登录界面使用js访问特定链接发送心跳报文，
这个方法并不优雅，而且在还有远程登录的需求，edge和chrome有自动页面休眠功能会中断心跳报文的发送。

# 编辑环境
DeepSeek  python 
python需要的库环境会在文件中给出，使用opencode编写的时候也会自动给出这里不赘述

# 实现步骤
## Portal 原理
sequenceDiagram
    participant 客户端 as 客户端 (Client)
    participant 接入设备 as 接入设备 (NAS/AC)
    participant Portal as Portal 服务器
    participant RADIUS as RADIUS 认证服务器
    participant 互联网 as 互联网

    Note over 客户端,互联网: 阶段一: DHCP 获取 IP 地址
    客户端->>接入设备: DHCP Discover
    接入设备->>客户端: DHCP Offer (含 IP 地址)
    客户端->>接入设备: DHCP Request
    接入设备->>客户端: DHCP ACK
    
    Note over 客户端,互联网: 阶段二: 未认证 → HTTP 重定向
    客户端->>接入设备: HTTP GET (访问任意网站)
    接入设备-->>客户端: HTTP 302 重定向 → Portal 登录页
    客户端->>Portal: HTTP GET (登录页面)
    Portal-->>客户端: 返回 HTML 登录表单

    Note over 客户端,互联网: 阶段三: 用户提交凭证
    客户端->>Portal: HTTP POST (用户名 + 密码)
    Portal->>RADIUS: RADIUS Access-Request
    RADIUS->>RADIUS: 验证用户身份
    RADIUS-->>Portal: RADIUS Access-Accept ✓

    Note over 客户端,互联网: 阶段四: 接入设备授权
    Portal->>接入设备: 授权请求 (Client IP/MAC, 用户信息)
    接入设备->>接入设备: 修改 ACL / 放行规则
    接入设备-->>Portal: 授权成功确认
    Portal-->>客户端: HTTP 200 (认证成功页面)

    Note over 客户端,互联网: 阶段五: 正常访问互联网
    客户端->>接入设备: HTTP GET (目标网站)
    接入设备->>互联网: 放行转发
    互联网-->>客户端: 返回正常内容


基于这个流转图我们可以使用burpsite抓取到5个报文（包括下线），具体的报文请自己进行嗅探获取
这里我说一下大概有哪些报文和他们的作用是什么
首次请求报文 -> 发送一个正常的请求
            <- 页面被重定向到一个认证登录界面，并给你一个JSESSIONID-BOSS的挑战值，在后续的认证中需要使用懂啊（本质为一个cookie）

登录请求     -> 发送一个认证请求，然后需要关注的值为 JSESSIONID-BOSS  和 填写表单中账号密码字段（可以从网页的html分析出）
            <- 认证通过后，会发下身份凭证 remeberMeCookie portal_token。否则为认证失败， 此时你的网路会直接认证上线，需要客户端确认

心跳维持阶段 -> 浏览器的页面js脚本会定时访问一个特定的网址接口并使用身份凭据和挑战值来鉴权 同时需要提供ip和登录的账号
            <- 返回 errcode 和 errmsg success来判断状态  0   操作操作成功  true  这个排列为刷新成功的返回。


知道这个流程之后直接和ai对话让他编写一个脚本即可。具体的实现是基于python request库来模拟这个登录流程 然后定时重复发送心跳报文。
当然你也可以直接编写一个shell脚本通过curl来实现这个功能。 也可以简单的使用无头浏览器模拟。需要注意的是，认证系统会识别UA标识符
需要伪装成浏览器的UA否则会返回失败。


# 校园网认证工具

---

## 运行方式

### 方式一：exe 直接运行（推荐）

```
校园网认证.exe
```

双击即可。无 Python 依赖。

### 方式二：源码运行

```bash
pip install -r requirements.txt
python auth_tool.py --gui
```

### 方式三：启动脚本

- `启动_GUI模式.vbs` — 双击启动，完全无命令行窗口
- `启动_GUI模式(通用).bat` — 自动查找 pythonw，适用于不同 conda/Python 路径

---

## 命令行参数

| 参数 | 说明 |
|------|------|
| `--gui` | 启动 GUI 界面（exe 默认模式） |
| `--tui` | 启动终端界面（仅 exe 时使用） |
| `--daemon` | 后台模式：静默登录，持续心跳，无界面 |
| `-u / --user` | 账号（配合 `--daemon`） |
| `-p / --password` | 密码（配合 `--daemon`） |
| `--interval` | 心跳间隔秒数，默认 60（配合 `--daemon`） |

### 示例

```bash
# TUI 模式
校园网认证.exe --tui

# 后台模式
校园网认证.exe --daemon -u 2021001 -p 123456 --interval 30

# 源码启动 GUI
python auth_tool.py --gui
```

---

## 功能说明

### 登录
打开程序后输入账号和密码。认证通过后自动进入仪表盘。

### 仪表盘
- **状态栏** — 显示账号、IP、认证状态、心跳间隔、心跳次数
- **状态圆点** — 绿色 = 在线，红色 = 已离线
- **日志区域** — 实时显示认证和心跳日志（深色主题）
- **控制按钮** — 修改心跳间隔 / 下线 / 隐藏到托盘 / 退出

### 系统托盘
- 关闭窗口自动隐藏到系统托盘，不会退出
- 右键托盘图标菜单：**显示主窗口 / 下线 / 退出**
- 双击托盘图标快速显示窗口
- 托盘图标颜色随连接状态变化（绿色 = 在线，红色 = 离线）

### 心跳保活
登录成功后自动启动心跳，定期向认证服务器发送保活请求。默认间隔 60 秒，可随时修改（最短 5 秒）。心跳连续失败 3 次自动标记离线。

### 后台模式
适用于服务器或无头环境。通过 PID 文件管理进程：

```bash
# 启动
python auth_tool.py --daemon -u 账号 -p 密码

# 停止
rm C:/Users/rahnl/auth_tool.pid
```

---

## 开发说明

### 打包为 exe

```bash
pip install pyinstaller
pyinstaller --noconsole --onefile --name "校园网认证" --icon auth_tool.ico ^
  --add-binary "C:\ProgramData\miniconda3\Library\bin\tcl86t.dll;." ^
  --add-binary "C:\ProgramData\miniconda3\Library\bin\tk86t.dll;." ^
  --add-binary "C:\ProgramData\miniconda3\Library\bin\ffi.dll;." ^
  --add-binary "C:\ProgramData\miniconda3\Library\bin\libexpat.dll;." ^
  --add-binary "C:\ProgramData\miniconda3\Library\bin\liblzma.dll;." ^
  --add-binary "C:\ProgramData\miniconda3\Library\bin\LIBBZ2.dll;." ^
  --add-binary "C:\ProgramData\miniconda3\Library\bin\libmpdec-4.dll;." ^
  --hidden-import tkinter --hidden-import win32gui ^
  --hidden-import PIL --hidden-import PIL.Image --hidden-import PIL.ImageDraw ^
  --hidden-import requests auth_tool.py
```

---

## 文件列表

```
校园网认证.exe          ← 单文件 exe（23MB，双击即运行）
auth_tool.py            ← Python 源码
auth_tool.ico           ← 程序图标
requirements.txt        ← Python 依赖
启动_GUI模式.vbs        ← 源码启动脚本（无窗口）
启动_GUI模式(通用).bat  ← 源码启动脚本（通用）
README.md               ← 本说明文件
```
