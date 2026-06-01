# PyPrint - 部署文档

## 环境要求

- Windows 10/11 或 Windows Server 2016+
- Python 3.10+
- SumatraPDF (打印 PDF / 图片所需)

## 安装步骤

### 1. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 2. 安装 SumatraPDF

从 https://www.sumatrapdfreader.org/download-free-pdf-viewer 下载并安装。

### 3. 配置环境变量

创建 `.env` 文件（或直接设置系统环境变量）：

```
SECRET_KEY=<生成一个长随机字符串>
PORT=5000
```

生成安全密钥：
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 4. 初始化数据库

首次启动时自动创建 SQLite 数据库和默认管理员账户：
- 用户名: `admin`
- 密码: `admin`

**部署后请立即修改默认密码！**

### 5. 用户管理

#### 使用命令行工具

```bash
# 添加普通用户
python manage.py adduser zhangsan mypass123

# 添加管理员
python manage.py adduser admin2 mypass123 admin

# 列出所有用户
python manage.py listusers

# 修改管理员密码
python manage.py resetpass admin

# 删除用户
python manage.py deluser zhangsan
```

#### 使用 Web 管理后台

管理员登录后访问 `/admin` 页面：
- **修改密码**: 在"修改密码"区域输入旧密码和新密码
- **重置用户密码**: 在"用户管理"区域点击对应用户的"重置密码"按钮
- **生成激活码**: 在"激活码管理"区域设置有效期并生成，用户凭激活码在 `/register` 注册

## 启动服务

### 开发环境

```bash
$env:SECRET_KEY="your-secret-key"
python app.py
```

### 生产环境（使用 Waitress）

```bash
pip install waitress
```

创建 `wsgi.py`：
```python
from app import app
if __name__ == '__main__':
    from waitress import serve
    serve(app, host='0.0.0.0', port=5000)
```

```bash
$env:SECRET_KEY="your-secret-key"
python wsgi.py
```

### 作为 Windows 服务运行

使用 NSSM (Non-Sucking Service Manager)：

```bash
# 下载 nssm.exe 放到 PATH
nssm install PyPrint "C:\path\to\python.exe" "C:\path\to\print_web\wsgi.py"
nssm set PyPrint AppDirectory "C:\path\to\print_web"
nssm set PyPrint AppEnvironmentExtra "SECRET_KEY=your-secret-key"
nssm start PyPrint
```

## 可选环境变量

| 变量 | 必填 | 说明 |
|------|------|------|
| `SECRET_KEY` | 是 | Flask session 加密密钥 |
| `PORT` | 否 | 服务端口，默认 5000 |
| `SUMATRA_PDF_PATH` | 否 | SumatraPDF 可执行文件路径（自动检测失败时使用） |
| `SOFFICE_PATH` | 否 | LibreOffice 可执行文件路径（Office 文件打印） |

## 安全建议

1. 部署后立即修改默认管理员密码
2. `SECRET_KEY` 使用足够长的随机字符串（64 字符以上）
3. 如仅局域网使用，建议 Windows 防火墙限制端口 5000 仅内网访问
4. 生产环境使用 Waitress 或 Gunicorn，不要用 Flask 内置服务器
5. 定期备份 `pyprint.db` 数据库文件

## 文件结构

```
print_web/
├── app.py                  # Flask 主应用
├── manage.py               # 命令行管理工具
├── wsgi.py                 # 生产环境入口（需自行创建）
├── requirements.txt        # Python 依赖
├── templates/              # HTML 模板
├── static/css/             # 样式文件
├── utils/                  # 后端工具模块
│   ├── printers.py         # 打印机检测与打印
│   ├── file_handler.py     # 文件类型验证
│   ├── auth.py             # 用户认证
│   ├── database.py         # 数据库初始化
│   ├── db_users.py         # 用户管理
│   ├── db_activation_codes.py  # 激活码管理
│   └── db_print_jobs.py    # 打印记录
└── pyprint.db              # SQLite 数据库（自动创建）
```

## 故障排除

| 问题 | 解决方案 |
|------|----------|
| 打印机列表为空 | 确认 Print Spooler 服务已启动，已登录 Web 界面 |
| 图片打印为空白 | 确认已安装 SumatraPDF |
| Office 文件无法打印 | 安装 LibreOffice 或设置 `SOFFICE_PATH` 环境变量 |
| 端口占用 | 修改 `PORT` 环境变量 |
