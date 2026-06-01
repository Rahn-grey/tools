# PyPrint 项目上下文

## 基本信息
- **项目**: PyPrint - LAN Print Server
- **技术栈**: Flask (Python) + HTML/CSS/JavaScript
- **平台**: Windows (win32print/pywin32)
- **端口**: 5000 (默认)，可通过 `PORT` 环境变量修改

## 项目结构
```
print_web/
├── app.py                    # Flask 主应用
├── templates/
│   └── index.html           # 主页面 (打印对话框)
├── static/css/style.css    # 样式 (Windows 打印对话框风格)
└── utils/
    ├── printers.py          # 打印机检测与打印
    ├── file_handler.py      # 文件类型验证
    ├── auth.py              # 用户认证
    ├── db_activation_codes.py  # 激活码管理
    ├── db_print_jobs.py     # 打印记录
    └── db_users.py          # 用户管理
```

## 启动方式
```bash
set SECRET_KEY=<你的密钥>
set PORT=5001
python app.py
```

## 核心功能
1. **打印机检测** - 使用 `win32print.EnumPrinters(2)` 枚举本地打印机
2. **文件打印** - 支持 PDF (SumatraPDF)、Office (LibreOffice)、图片 (Pillow+ReportLab)
3. **打印预览** - 前端 Blob URL 即时预览
4. **用户系统** - 注册需要激活码，管理员可生成激活码

## 当前已修复的问题
1. ✅ `api_preview` finally 块中 `result` 未定义的 bug
2. ✅ `triggerPreview` 函数作用域问题（从 initFileUpload 内部移到外部）
3. ✅ 预览加载指示器超时兜底（2秒）
4. ✅ 打印机 API 添加缓存控制头
5. ✅ 打印机列表返回 `status` 字段
6. ✅ HTML 转义防止 XSS
7. ✅ 打印机列表无法显示（login_required 对 API 返回 HTML 重定向）
8. ✅ `resetFileInput` 未定义导致 JS 报错
9. ✅ 图片横向打印二次旋转问题
10. ✅ 图片直接 SumatraPDF 打印失败（改为先转 PDF 再打印）
11. ✅ 打印记录未持久化到数据库
12. ✅ 打印预览功能已移除
13. ✅ 所有用户可见全部打印记录

## 关键 API 端点
| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/printers` | GET | 获取打印机列表 |
| `/api/print` | POST | 提交打印任务 |
| `/api/activation-codes` | GET/POST | 管理激活码 (admin) |
| `/api/users` | GET | 用户列表 (admin) |
| `/api/change-password` | POST | 修改当前用户密码 |
| `/api/admin-reset-password` | POST | 管理员重置用户密码 (admin) |
| `/api/print-history` | GET | 打印历史（所有用户可见） |
| `/api/print-stats` | GET | 打印统计 (admin) |

## 前端关键函数
- `loadPrinters()` - 页面加载时获取打印机列表
- `loadPrinterStatuses()` - 打印机状态标签页
- `triggerPreview()` - 方向/缩放变化时刷新预览（外部函数）
- `refreshPreview()` - 执行预览刷新（Blob URL 方式）
- `initFileUpload()` - 文件上传拖放处理
- `initPageRange()` - 页码范围初始化（绑定 triggerPreview）

## JavaScript 结构 (index.html)
```javascript
// 外部函数（在 DOMContentLoaded 之前定义）
var _previewDebounceTimer = null;
function triggerPreview() { ... }
function formatFileSize(bytes) { ... }

// DOMContentLoaded 事件中调用
document.addEventListener('DOMContentLoaded', function() {
    initFileUpload();
    initCopiesControl();
    initPageRange();    // 这里调用 triggerPreview
    initPrintButton();
    initPrinterTabs();
});
```

## 环境变量
| 变量 | 必填 | 说明 |
|------|------|------|
| `SECRET_KEY` | 是 | Flask session 密钥 |
| `PORT` | 否 | 服务器端口，默认 5000 |
| `SOFFICE_PATH` | 否 | LibreOffice 可执行文件路径 |
| `SUMATRA_PDF_PATH` | 否 | SumatraPDF 可执行文件路径 |

## 第三方依赖
- `pywin32` - Windows 打印机 API
- `Pillow` - 图片处理（图片转 PDF）
- `reportlab` - PDF 生成（图片转 PDF 备选方案）
- `win32print` / `win32api` - Windows 打印