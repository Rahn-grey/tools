#!/usr/bin/env python3
"""
校园网认证工具 v2.0
适用于 aaa.gxmzu.edu.cn 认证系统
TUI 风格：随机 ASCII 艺术 + 登录框 + 心跳日志界面
"""

import requests
import sys
import time
import json
import threading
import getpass
import os
import random
from urllib.parse import urlencode, urlparse, parse_qs
from datetime import datetime

# GUI support (tkinter built-in, win32gui + Pillow need install)
try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext, messagebox
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False

try:
    import win32gui
    import win32con
    WIN_TRAY_AVAILABLE = True
except ImportError:
    WIN_TRAY_AVAILABLE = False

VERSION = "2.1"
BASE_URL = "https://aaa.gxmzu.edu.cn"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/146.0.0.0 Safari/537.36"
)

STATIC_PARAMS = {
    "wlanacip": "10.240.192.33",
    "wlanacname": "gxmzu",
    "mac": "00:00:00:00:00:00",
    "vlan": "0",
}

HIDDEN_FIELDS = {
    "scheme": "https",
    "serverIp": "tomcat_server1:443",
    "hostIp": "http://127.0.0.1:8443/",
    "loginType": "",
    "auth_type": "0",
    "isBindMac1": "0",
    "pageid": "1",
    "templatetype": "1",
    "listbindmac": "0",
    "recordmac": "0",
    "isRemind": "1",
    "loginTimes": "",
    "groupId": "",
    "distoken": "",
    "echostr": "",
    "isautoauth": "",
    "mobile": "",
    "notice_pic_loop1": "/portal/uploads/pc/demo3/images/logo.jpg",
    "notice_pic_loop2": "/portal/uploads/pc/demo3/images/rrs_bg.jpg",
    "remInfo": "on",
    "desc_lb": "on",
}

# ══════════════════════════════════════════════════════
#  随机 ASCII 艺术图案集
# ══════════════════════════════════════════════════════

ASCII_ARTS = [
    # 龙
    r'''
                    +-------+
                    | DRAGON |
                    +-------+
        __====-_  _-====___
  _--^^^#####//      \\#####^^^--_
 -^##########// (    ) \\##########^-
_##########// ((    )) \\##########_
-##########\\  ))  ((  //##########-
 -##########\\ ((    )) //##########^
  -^^^#######\\\\  \\// //#######^^^-
       ^^##~~~~~~,,,,
    ''',
    # 猫头鹰
    r'''
          +--------+
          |  OWL   |
          +--------+
        .--. .--.
       / ((  )) \\
      /  \\ '' /  \\
     /    \\ '' /   \\
    (______\/\/_____)
     | ||  |  || |
     | ||  |  || |
    ''',
    # 狼
    r'''
        +--------+
        |  WOLF  |
        +--------+
        ____
       / __ \\
      / /  \\ \\
     / /    \\ \\
    / /      \\ \\
    \\/   __   \\/
    |   /  \\   |
    |   \\__/   |
     \\________/
    ''',
    # 凤凰
    r'''
          +---------+
          | PHOENIX |
          +---------+
        _,-""-,
     _-"   __  `-_
   ,'    /  \\    `.
  /     / /\\ \\     \\
 |     / /__\\ \\     |
 |     \\/    \\/     |
  \\               /
   `-_         _-'
      `--___--`
    ''',
    # 狮子
    r'''
        +---------+
        |  LION   |
        +---------+
       /          \\
      |   -- --   |
      |   -- --   |
       \\   **    /
        \\       /
    ====\\=====/====
    ''',
    # 鲨鱼
    r'''
        +------------+
        |  SHARK     |
        +------------+
         /""-._
        /      `-.
       /   ,'     \\
      /  ,'        \\
     /  /           \\
    /  (        `---'
   /    `--.__
  /         `\\
 /            \\
/              \\
    ''',
    # 鹰
    r'''
          +----------+
          |  EAGLE   |
          +----------+
        __...--..
    _.-"      -.
 .-`    ,'      \\
(      /   \\     |
 \\    /     \\   /
  `--`      `--`
    ''',
    # 机器人
    r'''
        +-------------+
        |   ROBOT     |
        +-------------+
       ##############
       ##  O    O  ##
       ##    ##    ##
       ##  ####   ##
       ##    ##    ##
       ##  #  #   ##
       ## #    #  ##
       ##############
         ##    ##
        ####  ####
    ''',
    # 独角兽
    r'''
         +------------+
         |  UNICORN   |
         +------------+
           \\`-.
           /  |
          /  /
        _/ _/
      ,"   /
     (    /
      \\  /
       \\/
    ''',
    # 龙2
    r'''
        +--------+
        |DRAGON2 |
        +--------+
       .-~~~-.
  .- ~ ~-(       )_ _
 /      (  90    )   \\
|   (   |        )    )
 \\    ~-_         ~   /
   ~-_-_~-_____-__~_-_
    ''',
    # 鱼
    r'''
       +--------+
       |  FISH  |
       +--------+
    o
     o   o
      o   o
   <`)))><  o
      o   o
     o   o
    o
    ''',
    # 螃蟹
    r'''
      +----------+
      |   CRAB   |
      +----------+
    (?) (?)  (?)
      \\  \\/  /
       \\    /
    <( (.) )>
       /    \\
      /  /\\  \\
    (?) (?)  (?)
    ''',
    # 蝴蝶
    r'''
       +------------+
       | BUTTERFLY  |
       +------------+
     .==.    .==.
    (    )  (    )
     \\  /    \\  /
      )(      )(
     /  \\    /  \\
    (    )  (    )
     `==`    `==`
    ''',
]

# ══════════════════════════════════════════════════════
#  工具函数
# ══════════════════════════════════════════════════════

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def timestamp():
    return datetime.now().strftime("%H:%M:%S")


def detect_wlanuserip():
    url = "http://edge-http.microsoft.com/captiveportal/generate_204"
    try:
        r = requests.get(url, allow_redirects=True, timeout=5,
                         headers={"User-Agent": UA})
        if "aaa.gxmzu.edu.cn" in r.url:
            qs = parse_qs(urlparse(r.url).query)
            return qs.get("wlanuserip", [None])[0]
    except requests.RequestException:
        pass
    return None


# ══════════════════════════════════════════════════════
#  认证客户端
# ══════════════════════════════════════════════════════

class AuthClient:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers["User-Agent"] = UA
        self.session.headers["Accept-Language"] = "zh-CN,zh;q=0.9"
        self.session.headers["Accept"] = (
            "text/html,application/xhtml+xml,application/xml;"
            "q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
        )
        self.wlanuserip = ""
        self.user_id = None
        self.authenticated = False
        self.hb_interval = 60
        self._hb_stop = threading.Event()
        self._hb_thread = None
        self._log = []
        self._hb_count = 0

    def _build_url(self, path, extra_params=None):
        params = {
            "wlanacip": STATIC_PARAMS["wlanacip"],
            "wlanacname": STATIC_PARAMS["wlanacname"],
            "wlanuserip": self.wlanuserip,
            "mac": STATIC_PARAMS["mac"],
            "vlan": STATIC_PARAMS["vlan"],
        }
        if extra_params:
            params.update(extra_params)
        return f"{BASE_URL}{path}?{urlencode(params)}"

    def _build_form_data(self, password=""):
        data = dict(HIDDEN_FIELDS)
        data["url"] = "http://edge-http.microsoft.com/captiveportal/generate_204"
        if self.user_id:
            data["userId"] = self.user_id
        if password:
            data["passwd"] = password
        return data

    @staticmethod
    def _form_headers(referer):
        return {
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": BASE_URL,
            "Referer": referer,
        }

    # ── 登录 ──

    def login(self, user_id, password):
        self.user_id = user_id.strip()
        if not self.wlanuserip:
            ip = detect_wlanuserip()
            if ip:
                self.wlanuserip = ip

        if not self.wlanuserip:
            self.wlanuserip = "10.1.154.17"

        # Step 1: GET 登录页面获取 JSESSIONID
        ts = timestamp()
        url = self._build_url("/webauth.do")
        try:
            r1 = self.session.get(url, timeout=10)
            self._log.append(f"[*]  {ts}  GET  /webauth.do → {r1.status_code}")
            c = dict(r1.cookies)
            if c:
                self._log.append(f"     ← cookies: {'; '.join(f'{k}={v[:20]}' for k, v in c.items())}")
            if r1.status_code != 200:
                return False, "获取登录页面失败"
        except requests.RequestException as e:
            self._log.append(f"[!]  {ts}  GET  /webauth.do → ERR: {e}")
            return False, str(e)

        # Step 2: POST 登录信息
        ts = timestamp()
        login_url = self._build_url("/webauth.do")
        data = self._build_form_data(password)
        headers = self._form_headers(login_url)

        post_body_preview = urlencode({k: (v[:8] + '...' if k == 'passwd' else v)
                                        for k, v in data.items()})
        self._log.append(f"[*]  {ts}  POST /webauth.do")
        self._log.append(f"     → body: userId={self.user_id}, passwd=******"
                         f", pageid={data.get('pageid','')}, url={data.get('url','')[:30]}...")

        try:
            r2 = self.session.post(login_url, data=data, headers=headers,
                                   timeout=10)
            self._log.append(f"     ← HTTP {r2.status_code}")
            c = dict(self.session.cookies)
            relevant = {k: v for k, v in c.items()
                        if k in ('portal_token', 'remeberMeCookie', 'JSESSIONID-BOSS-0')}
            if relevant:
                self._log.append(f"     ← cookies: {'; '.join(f'{k}={v[:24]}...' for k, v in relevant.items())}")
        except requests.RequestException as e:
            self._log.append(f"[!]  {ts}  POST /webauth.do → ERR: {e}")
            return False, str(e)

        if "portal_token" in self.session.cookies:
            self.authenticated = True
            self._log.append(f"[✓]  {timestamp()}  登录成功")
            return True, "登录成功"
        for kw in ["密码错误", "密码有误", "账号不存在", "帐号不存在",
                    "认证失败", "用户名或密码"]:
            if kw in r2.text:
                self._log.append(f"[✗]  {timestamp()}  登录失败: {kw}")
                return False, kw
        self._log.append(f"[✗]  {timestamp()}  登录失败: 未知错误")
        return False, "登录失败，请检查账号密码"

    # ── 心跳 ──

    def heartbeat(self):
        if not self.authenticated or not self.user_id:
            return None
        data = {
            "pageid": "1",
            "userId": self.user_id,
            "wlanuserip": self.wlanuserip,
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": BASE_URL,
            "Referer": self._build_url("/webauth.do"),
        }
        try:
            r = self.session.post(
                f"{BASE_URL}/httpservice/updateSession.do",
                data=data, headers=headers, timeout=10,
            )
            body_preview = ""
            if r.text:
                try:
                    j = r.json()
                    body_preview = json.dumps(j, ensure_ascii=False)[:80]
                except Exception:
                    body_preview = r.text[:80]
            return {
                "ok": r.status_code == 200 and r.json().get("errcode") == "0",
                "status": r.status_code,
                "body": body_preview,
                "sent": f"pageid=1&userId={self.user_id}&wlanuserip={self.wlanuserip}",
            }
        except Exception as e:
            return {
                "ok": False,
                "status": 0,
                "body": str(e),
                "sent": f"pageid=1&userId={self.user_id}&wlanuserip={self.wlanuserip}",
            }

    def start_heartbeat(self):
        if self._hb_thread and self._hb_thread.is_alive():
            return
        if not self.authenticated:
            return
        self._hb_stop.clear()
        self._hb_thread = threading.Thread(
            target=self._heartbeat_loop, args=(), daemon=True,
        )
        self._hb_thread.start()

    def stop_heartbeat(self):
        self._hb_stop.set()
        if self._hb_thread:
            self._hb_thread.join(timeout=3)
            self._hb_thread = None

    def _heartbeat_loop(self):
        fail_count = 0
        while not self._hb_stop.wait(self.hb_interval):
            if self._hb_stop.is_set():
                break
            result = self.heartbeat()
            self._hb_count += 1
            ts = timestamp()
            sid = f"# {self._hb_count:>4d}"
            if result and result["ok"]:
                self._log.append(
                    f"[{sid}]  {ts}  POST /httpservice/updateSession.do"
                )
                self._log.append(
                    f"     → {result['sent']}"
                )
                self._log.append(
                    f"     ← HTTP {result['status']}  {result['body']}  ✓"
                )
                fail_count = 0
            else:
                status = result["status"] if result else 0
                body = result["body"][:40] if result and result["body"] else ""
                self._log.append(
                    f"[{sid}]  {ts}  POST /httpservice/updateSession.do"
                )
                self._log.append(
                    f"     → {result['sent']}" if result else "     → (unknown)"
                )
                self._log.append(
                    f"     ← HTTP {status}  {body}  ✗"
                )
                fail_count += 1
                if fail_count >= 3:
                    self._log.append(f"[!]  {timestamp()}  心跳连续失败，标记离线")
                    self.authenticated = False
                    break
            if len(self._log) > 200:
                self._log = self._log[-150:]

    # ── 下线 ──

    def logout(self):
        if not self.authenticated:
            return False
        self.stop_heartbeat()
        url = self._build_url("/webdisconn.do",
                              {"url": "http://1.1.1.1/"})
        data = self._build_form_data()
        headers = self._form_headers(url)
        try:
            r = self.session.post(url, data=data, headers=headers,
                                  timeout=10)
            if r.status_code == 200:
                self.authenticated = False
                return True
        except requests.RequestException:
            pass
        return False


# ══════════════════════════════════════════════════════
#  TUI 界面
# ══════════════════════════════════════════════════════

def render_login_screen(art):
    clear_screen()
    print()
    print(f"{art}")
    print()
    print("  ╔══════════════════════════════════╗")
    print("  ║        校园网认证登录            ║")
    print("  ╚══════════════════════════════════╝")
    print()


def render_log_screen(art, client):
    clear_screen()
    print()
    print(f"{art}")
    print()
    info = (
        f"  账号: {client.user_id}  "
        f"IP: {client.wlanuserip}  "
        f"状态: {'已认证' if client.authenticated else '已离线'}  "
        f"心跳间隔: {client.hb_interval}s"
    )
    print(f"  {info}")
    print(f"  {'─' * len(info)}")
    print()
    print("  ── 日志信息 ──")
    if not client._log:
        print("     (等待日志...)")
    else:
        for entry in client._log[-20:]:
            print(f"  {entry}")
    print()
    print("  ────────────────────────────────────")
    print("  [1] 修改心跳间隔  [2] 下线  [3] 刷新  [0] 退出")
    print()


def show_logout_result(msg):
    print()
    print(f"  {msg}")
    time.sleep(1.5)


# ══════════════════════════════════════════════════════
#  GUI 界面（tkinter + 系统托盘）
# ══════════════════════════════════════════════════════


class AuthGUI:
    """校园网认证 GUI 界面"""

    def __init__(self, client):
        self.client = client
        self.root = tk.Tk()
        self.root.title(f"校园网认证 v{VERSION}")
        self.root.geometry("740x560")
        self.root.minsize(600, 420)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.logged_in = False
        self._update_job = None
        self._last_log_len = 0

        # tray icon state (win32gui native)
        self._tray_hwnd = None
        self._tray_nid = None
        self._tray_hicon = None

        # window icon
        if WIN_TRAY_AVAILABLE:
            try:
                from PIL import ImageTk
                self.root.iconphoto(True, ImageTk.PhotoImage(self._make_pil_icon(32, True)))
            except Exception:
                pass

        self._setup_login()
        self._setup_tray()

        # center window
        self.root.update_idletasks()
        w, h = 740, 560
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    # ── icon helpers ──

    @staticmethod
    def _make_pil_icon(size, connected=True):
        from PIL import Image, ImageDraw
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        color = "#27AE60" if connected else "#E74C3C"
        draw.ellipse([2, 2, size - 2, size - 2], fill=color)
        cx = size // 2
        draw.rectangle([cx - 4, size // 4, cx + 4, 3 * size // 4], fill="white")
        return img

    def _make_hicon(self, connected):
        try:
            from PIL import Image, ImageDraw
            import tempfile
            size = 32
            color = "#27AE60" if connected else "#E74C3C"
            img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.ellipse([2, 2, size - 2, size - 2], fill=color)
            cx = size // 2
            draw.rectangle([cx - 4, size // 4, cx + 4, 3 * size // 4], fill="white")
            ico_path = os.path.join(tempfile.gettempdir(), "auth_tray_temp.ico")
            try:
                img.save(ico_path, format="ICO", sizes=[(size, size)])
                return win32gui.LoadImage(
                    0, ico_path, win32con.IMAGE_ICON, size, size,
                    win32con.LR_LOADFROMFILE,
                )
            finally:
                try:
                    os.unlink(ico_path)
                except Exception:
                    pass
        except ImportError:
            # PIL not available — fall back to a default system icon
            return win32gui.LoadIcon(0, win32con.IDI_APPLICATION)

    # ── login screen ──

    def _setup_login(self):
        for w in self.root.winfo_children():
            w.destroy()
        self.root.title(f"校园网认证 v{VERSION}")

        main = ttk.Frame(self.root, padding=30)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="校园网认证登录",
                  font=("微软雅黑", 18, "bold")).pack(pady=(0, 5))
        ttk.Label(main, text=f"v{VERSION}  |  aaa.gxmzu.edu.cn",
                  foreground="#888").pack(pady=(0, 30))

        form = ttk.Frame(main)
        form.pack()

        ttk.Label(form, text="账号:", font=("微软雅黑", 11)).grid(
            row=0, column=0, sticky="e", padx=(0, 8), pady=6)
        self._user_var = tk.StringVar()
        ue = ttk.Entry(form, textvariable=self._user_var, width=28, font=("微软雅黑", 11))
        ue.grid(row=0, column=1, pady=6)
        ue.focus()

        ttk.Label(form, text="密码:", font=("微软雅黑", 11)).grid(
            row=1, column=0, sticky="e", padx=(0, 8), pady=6)
        self._pwd_var = tk.StringVar()
        ttk.Entry(form, textvariable=self._pwd_var, width=28,
                  font=("微软雅黑", 11), show="*").grid(row=1, column=1, pady=6)

        btn_frame = ttk.Frame(main)
        btn_frame.pack(pady=(25, 10))
        self._login_btn = ttk.Button(btn_frame, text="登  录",
                                     command=self._on_login, width=20)
        self._login_btn.pack()

        self._login_status = ttk.Label(main, text="",
                                       foreground="#666", font=("微软雅黑", 10))
        self._login_status.pack()

        self.root.bind("<Return>", lambda e: self._on_login())

    def _on_login(self):
        uid = self._user_var.get().strip()
        pwd = self._pwd_var.get()
        if not uid or not pwd:
            messagebox.showwarning("提示", "请输入账号和密码", parent=self.root)
            return

        self._login_btn.config(state=tk.DISABLED, text="认证中...")
        self._login_status.config(text="正在连接认证服务器...", foreground="#666")

        def _work():
            ok, msg = self.client.login(uid, pwd)
            self.root.after(0, lambda: self._login_result(ok, msg))

        threading.Thread(target=_work, daemon=True).start()

    def _login_result(self, ok, msg):
        self._login_btn.config(state=tk.NORMAL, text="登  录")
        if ok:
            self.logged_in = True
            self.client.start_heartbeat()
            self._setup_dashboard()
        else:
            self._login_status.config(text=f"认证失败: {msg}", foreground="#E74C3C")

    # ── dashboard ──

    def _setup_dashboard(self):
        for w in self.root.winfo_children():
            w.destroy()
        self.root.title(f"校园网认证 v{VERSION}  -  {self.client.user_id}")

        # top status bar
        top = ttk.Frame(self.root, padding=(12, 8))
        top.pack(fill=tk.X)
        self._status_label = ttk.Label(top, font=("微软雅黑", 10))
        self._status_label.pack(side=tk.LEFT)

        self._status_dot = tk.Canvas(top, width=16, height=16, highlightthickness=0)
        self._status_dot.pack(side=tk.RIGHT, padx=(0, 4))
        self._dot_id = self._status_dot.create_oval(2, 2, 14, 14, fill="#27AE60", outline="")

        ttk.Separator(self.root, orient=tk.HORIZONTAL).pack(fill=tk.X)

        # log area
        log_frame = ttk.Frame(self.root, padding=(12, 8))
        log_frame.pack(fill=tk.BOTH, expand=True)

        hdr = ttk.Frame(log_frame)
        hdr.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(hdr, text="日志信息", font=("微软雅黑", 10, "bold")).pack(side=tk.LEFT)

        text_frame = ttk.Frame(log_frame, borderwidth=1, relief=tk.SUNKEN)
        text_frame.pack(fill=tk.BOTH, expand=True)

        self._log_text = tk.Text(text_frame, font=("Consolas", 9), wrap=tk.WORD,
                                  bg="#1E1E1E", fg="#D4D4D4", padx=8, pady=6,
                                  relief=tk.FLAT, borderwidth=0)
        self._log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scroll = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self._log_text.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._log_text.config(yscrollcommand=scroll.set)

        self._log_text.tag_config("ok", foreground="#4EC9B0")
        self._log_text.tag_config("err", foreground="#F44747")
        self._log_text.tag_config("info", foreground="#569CD6")

        # control bar
        ctrl = ttk.Frame(self.root, padding=(12, 8))
        ctrl.pack(fill=tk.X)

        ttk.Button(ctrl, text="修改间隔", command=self._change_interval).pack(side=tk.LEFT, padx=2)
        ttk.Button(ctrl, text="下线", command=self._do_logout).pack(side=tk.LEFT, padx=2)
        ttk.Separator(ctrl, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=8)
        ttk.Button(ctrl, text="隐藏到托盘", command=self._minimize_to_tray).pack(side=tk.LEFT, padx=2)
        ttk.Button(ctrl, text="退出", command=self.on_quit).pack(side=tk.RIGHT, padx=2)

        self._last_log_len = 0
        self._update_dashboard()

    def _update_dashboard(self):
        if not self.logged_in or not hasattr(self, "_status_label"):
            return

        # status dot
        dot_color = "#27AE60" if self.client.authenticated else "#E74C3C"
        self._status_dot.itemconfig(self._dot_id, fill=dot_color)

        sta = (
            f"账号: {self.client.user_id}  |  "
            f"IP: {self.client.wlanuserip}  |  "
            f"状态: {'已认证' if self.client.authenticated else '已离线'}  |  "
            f"心跳: {self.client.hb_interval}s  |  "
            f"次数: {self.client._hb_count}"
        )
        self._status_label.config(text=sta)

        # log — incremental update only when new entries arrive
        if len(self.client._log) != self._last_log_len:
            self._log_text.delete("1.0", tk.END)
            for entry in self.client._log[-100:]:
                if entry.startswith("[✓") or entry.startswith("[#"):
                    tag = "ok"
                elif entry.startswith("[✗") or entry.startswith("[!"):
                    tag = "err"
                elif entry.startswith("[*"):
                    tag = "info"
                else:
                    tag = None
                self._log_text.insert(tk.END, entry + "\n", tag) if tag else self._log_text.insert(tk.END, entry + "\n")
            self._log_text.see(tk.END)
            self._last_log_len = len(self.client._log)

        # tray icon colour
        if WIN_TRAY_AVAILABLE:
            try:
                self._update_tray_icon(self.client.authenticated)
            except Exception:
                pass

        self._update_job = self.root.after(1000, self._update_dashboard)

    # ── interval dialog ──

    def _change_interval(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("修改心跳间隔")
        dlg.geometry("300x140")
        dlg.resizable(False, False)
        dlg.transient(self.root)
        dlg.grab_set()

        ttk.Label(dlg, text=f"当前间隔: {self.client.hb_interval} 秒",
                  font=("微软雅黑", 10)).pack(pady=(15, 5))
        ttk.Label(dlg, text="新间隔 (秒, 最小 5):",
                  font=("微软雅黑", 9)).pack()
        var = tk.StringVar()
        entry = ttk.Entry(dlg, textvariable=var, width=10, font=("微软雅黑", 11))
        entry.pack(pady=5)
        entry.focus()
        entry.select_range(0, tk.END)

        def apply():
            try:
                v = int(var.get())
                if v < 5:
                    v = 5
                self.client.hb_interval = v
                self.client._log.append(f"[*]  {timestamp()}  心跳间隔已改为 {v}s")
                dlg.destroy()
            except ValueError:
                messagebox.showwarning("错误", "请输入有效数字", parent=dlg)

        bf = ttk.Frame(dlg)
        bf.pack(pady=10)
        ttk.Button(bf, text="确定", command=apply).pack(side=tk.LEFT, padx=5)
        ttk.Button(bf, text="取消", command=dlg.destroy).pack(side=tk.LEFT, padx=5)
        dlg.bind("<Return>", lambda e: apply())

    # ── logout ──

    def _do_logout(self):
        if not messagebox.askyesno("确认下线", "确定要断开网络连接吗？", parent=self.root):
            return
        if self.client.logout():
            self.logged_in = False
            if self._update_job:
                self.root.after_cancel(self._update_job)
                self._update_job = None
            self._setup_login()

    # ── native tray icon (win32gui) ──

    def _setup_tray(self):
        self._tray_ok = False
        if not WIN_TRAY_AVAILABLE:
            return

        ready = threading.Event()

        def _tray_thread():
            try:
                wc = win32gui.WNDCLASS()
                wc.hInstance = win32gui.GetModuleHandle(None)
                wc.lpfnWndProc = self._tray_wnd_proc
                wc.lpszClassName = "AuthToolTrayWindow"
                try:
                    win32gui.RegisterClass(wc)
                except Exception:
                    pass
                hwnd = win32gui.CreateWindow(
                    "AuthToolTrayWindow", "AuthTool", 0,
                    0, 0, 0, 0, 0, 0, wc.hInstance, None,
                )
                self._tray_hwnd = hwnd

                hicon = self._make_hicon(True)
                nid = (
                    hwnd, 0,
                    win32gui.NIF_ICON | win32gui.NIF_TIP | win32gui.NIF_MESSAGE,
                    win32con.WM_USER + 100, hicon,
                    f"校园网认证 v{VERSION}",
                )
                win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, nid)
                self._tray_nid = nid
                self._tray_hicon = hicon
                self._tray_ok = True
                ready.set()
                win32gui.PumpMessages()
            except Exception:
                ready.set()

        t = threading.Thread(target=_tray_thread, daemon=True)
        t.start()
        ready.wait(timeout=3)

    def _tray_wnd_proc(self, hwnd, msg, wparam, lparam):
        if msg == win32con.WM_DESTROY:
            win32gui.PostQuitMessage(0)
            return 0
        if msg == win32con.WM_USER + 100:
            if lparam == win32con.WM_LBUTTONDBLCLK:
                self.root.after(0, self._show_window)
            elif lparam == win32con.WM_RBUTTONUP:
                self._show_tray_menu(hwnd)
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    def _show_tray_menu(self, hwnd):
        menu = win32gui.CreatePopupMenu()
        win32gui.AppendMenu(menu, win32con.MF_STRING, 1, "显示主窗口")
        win32gui.AppendMenu(menu, win32con.MF_STRING, 2, "下线")
        win32gui.AppendMenu(menu, win32con.MF_SEPARATOR, 0, "")
        win32gui.AppendMenu(menu, win32con.MF_STRING, 3, "退出")
        pos = win32gui.GetCursorPos()
        win32gui.SetForegroundWindow(hwnd)
        cmd = win32gui.TrackPopupMenu(
            menu,
            win32con.TPM_LEFTALIGN | win32con.TPM_BOTTOMALIGN
            | win32con.TPM_RETURNCMD,
            pos[0], pos[1], 0, hwnd, None,
        )
        win32gui.PostMessage(hwnd, win32con.WM_NULL, 0, 0)
        win32gui.DestroyMenu(menu)
        if cmd == 1:
            self.root.after(0, self._show_window)
        elif cmd == 2:
            self.root.after(0, self._do_logout)
        elif cmd == 3:
            self.root.after(0, self.on_quit)

    def _update_tray_icon(self, connected):
        if not WIN_TRAY_AVAILABLE or not self._tray_nid:
            return
        hicon = self._make_hicon(connected)
        hwnd, uid, flags, msg, _, tip = self._tray_nid
        new_nid = (hwnd, uid, flags, msg, hicon, tip)
        win32gui.Shell_NotifyIcon(win32gui.NIM_MODIFY, new_nid)
        old = self._tray_hicon
        self._tray_hicon = hicon
        self._tray_nid = new_nid
        if old:
            try:
                win32gui.DestroyIcon(old)
            except Exception:
                pass

    def _minimize_to_tray(self):
        self.root.withdraw()

    def _show_window(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    # ── lifecycle ──

    def on_close(self):
        if WIN_TRAY_AVAILABLE and self._tray_ok:
            self._minimize_to_tray()
        else:
            if messagebox.askokcancel("退出", "确定要退出吗？", parent=self.root):
                self.on_quit()

    def on_quit(self):
        if self._update_job:
            self.root.after_cancel(self._update_job)
            self._update_job = None
        self.client.stop_heartbeat()
        if WIN_TRAY_AVAILABLE and self._tray_hwnd:
            try:
                win32gui.PostMessage(self._tray_hwnd, win32con.WM_QUIT, 0, 0)
            except Exception:
                pass
        try:
            self.root.quit()
            self.root.destroy()
        except Exception:
            pass

    def run(self):
        self.root.mainloop()
        self.client.stop_heartbeat()


# ══════════════════════════════════════════════════════
#  主程序
# ══════════════════════════════════════════════════════

def main():
    client = AuthClient()
    art = random.choice(ASCII_ARTS)

    # ── 登录阶段 ──
    render_login_screen(art)
    user_id = input("  账号: ").strip()
    if not user_id:
        print("\n  账号不能为空。")
        time.sleep(1.5)
        return

    password = getpass.getpass("  密码: ").strip()
    if not password:
        print("\n  密码不能为空。")
        time.sleep(1.5)
        return

    print()
    print("  正在认证...")
    ok, msg = client.login(user_id, password)

    if not ok:
        print(f"\n  认证失败: {msg}")
        time.sleep(2)
        return

    # ── 登录成功 → 启动心跳 → 日志界面 ──
    client.start_heartbeat()

    while True:
        render_log_screen(art, client)
        cmd = input("  > ").strip()

        if cmd == "0":
            if client.authenticated:
                client.stop_heartbeat()
            clear_screen()
            print("\n  再见!\n")
            break

        elif cmd == "1":
            render_log_screen(art, client)
            try:
                val = input("  心跳间隔(秒, 最小5): ").strip()
                new_iv = int(val)
                if new_iv < 5:
                    print("  间隔太短，设为 5 秒")
                    new_iv = 5
                client.hb_interval = new_iv
                client._log.append(f"[*]  {timestamp()}  心跳间隔已改为 {new_iv}s")
            except ValueError:
                client._log.append(f"[!]  {timestamp()}  修改间隔失败: 无效数字")
                time.sleep(1)

        elif cmd == "2":
            render_log_screen(art, client)
            sure = input("  确认下线? (y/N): ").strip().lower()
            if sure == "y":
                ok = client.logout()
                show_logout_result("下线成功" if ok else "下线失败")
                if ok:
                    break
            else:
                client._log.append(f"[*]  {timestamp()}  已取消下线")
                continue

        elif cmd == "3":
            continue

        else:
            client._log.append(f"[!]  {timestamp()}  未知命令: {cmd}")
            time.sleep(0.5)
            continue


if __name__ == "__main__":
    # 打包成 exe 时默认启动 GUI 模式
    if getattr(sys, 'frozen', False):
        if '--tui' not in sys.argv and '--daemon' not in sys.argv:
            sys.argv.append('--gui')

    import argparse

    parser = argparse.ArgumentParser(description="校园网认证工具")
    parser.add_argument("--gui", action="store_true",
                        help="启动 GUI 界面（打包 exe 默认）")
    parser.add_argument("--tui", action="store_true",
                        help="启动 TUI 界面（仅 exe 时使用）")
    parser.add_argument("--daemon", action="store_true",
                        help="后台模式：静默登录并持续心跳，无交互界面")
    parser.add_argument("-u", "--user", help="账号（配合 --daemon 使用）")
    parser.add_argument("-p", "--password", help="密码（配合 --daemon 使用）")
    parser.add_argument("--interval", type=int, default=60,
                        help="心跳间隔秒数（默认 60，配合 --daemon）")
    parser.add_argument("--pidfile",
                        default="C:/Users/rahnl/auth_tool.pid",
                        help="PID 文件路径（配合 --daemon）")
    args = parser.parse_args()

    if args.daemon:
        uid = args.user or input("  账号: ").strip()
        pwd = args.password or getpass.getpass("  密码: ").strip()
        if not uid or not pwd:
            print("[-] 账号或密码不能为空")
            sys.exit(1)

        client = AuthClient()
        import os as _os
        with open(args.pidfile, "w") as f:
            f.write(str(_os.getpid()))
        print(f"[*] PID: {_os.getpid()}  已写入 {args.pidfile}")

        ok, msg = client.login(uid, pwd)
        if not ok:
            print(f"[-] 认证失败: {msg}")
            _os.remove(args.pidfile)
            sys.exit(1)

        client.hb_interval = args.interval
        client.start_heartbeat()
        print(f"[*] 后台心跳已启动 (间隔 {args.interval}s)")
        print(f"[*] 停止命令: 删除 {args.pidfile} 或结束进程")
        print(f"[*] 查看日志: {args.pidfile.replace('.pid','.log')}")

        log_path = args.pidfile.replace(".pid", ".log")
        try:
            while True:
                time.sleep(5)
                if not _os.path.exists(args.pidfile):
                    print("[*] PID 文件已删除，停止心跳")
                    break
                if not client.authenticated:
                    print("[!] 已离线，退出")
                    break
                # 每分钟写一次日志
                if int(time.time()) % 60 < 5:
                    ts = timestamp()
                    last = client._log[-1] if client._log else ""
                    with open(log_path, "a", encoding="utf-8") as lf:
                        lf.write(f"{ts}  {'在线' if client.authenticated else '离线'}  {last}\n")
                    time.sleep(10)
        except KeyboardInterrupt:
            pass
        finally:
            client.stop_heartbeat()
            if _os.path.exists(args.pidfile):
                _os.remove(args.pidfile)
            print("[*] 已停止")
        sys.exit(0)

    if args.gui:
        if not GUI_AVAILABLE:
            print("[-] tkinter 不可用，无法启动 GUI")
            sys.exit(1)
        client = AuthClient()
        app = AuthGUI(client)
        app.run()
        sys.exit(0)

    try:
        main()
    except KeyboardInterrupt:
        clear_screen()
        print("\n  再见!\n")
        sys.exit(0)
