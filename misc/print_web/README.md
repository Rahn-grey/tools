# PyPrint — LAN Print Server

基于 Flask 的局域网打印服务器，Windows 平台运行，支持 PDF / Word / Excel / 图片等多格式文件打印。

## 功能

- **打印机管理** — 自动检测 Windows 本地打印机，支持状态查看
- **多格式打印** — PDF（SumatraPDF）、Office（LibreOffice）、图片（Pillow + ReportLab）
- **打印选项** — 份数 / 页面范围 / 纸张大小 / 方向 / 缩放 / 灰度 / 双面
- **用户系统** — 激活码注册，管理员生成激活码
- **打印记录** — 所有打印持久化到 SQLite，全员可查
- **管理后台** — Web 界面管理用户、密码、激活码、打印统计

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 设置密钥
set SECRET_KEY=<生成一个长随机串>
# 或: $env:SECRET_KEY="your-key"  (PowerShell)

# 3. 启动
python app.py
# 访问 http://localhost:5000
```

默认管理员: `admin` / `admin`（**部署后立即修改**）

## 命令行管理

```bash
python manage.py adduser    zhangsan 123456       # 添加普通用户
python manage.py adduser    admin2   secret admin # 添加管理员
python manage.py listusers                         # 列出所有用户
python manage.py resetpass  admin                 # 强制重置密码
python manage.py deluser    zhangsan              # 删除用户
```

## 环境变量

| 变量 | 说明 |
|------|------|
| `SECRET_KEY` | Flask 密钥（**必填**） |
| `PORT` | 端口，默认 5000 |
| `SUMATRA_PDF_PATH` | SumatraPDF 路径，自动检测失败时指定 |
| `SOFFICE_PATH` | LibreOffice 路径，打印 Office 文件需要 |

## 生产部署

```bash
pip install waitress
```

```python
# wsgi.py
from app import app
from waitress import serve
serve(app, host='0.0.0.0', port=5000)
```

```bash
python wsgi.py
```

## 技术栈

Flask / SQLite / pywin32 / Pillow / ReportLab
