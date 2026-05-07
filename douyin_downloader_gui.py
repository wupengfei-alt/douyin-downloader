#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音视频无水印下载器 - Windows GUI 版（支持浏览器自动获取 Cookie）
依赖: pip install f2 requests playwright && playwright install chromium
打包: pyinstaller --onefile --windowed --name "抖音下载器" douyin_downloader_gui.py
"""

import os
import sys
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from datetime import datetime

# 尝试导入 playwright_helper
try:
    from playwright_helper import fetch_cookies_auto
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


# ── 全局配置 ──────────────────────────────────────────
F2_MODULE = "f2"          # pip install f2
DOWNLOAD_MODE = "one"      # one=单视频, post=主页作品


# ── Python 路径查找器（兼容 PyInstaller 打包后环境）──────
import shutil as _shutil

def _find_python_executable() -> str:
    """
    查找本机 Python 解释器路径。
    兼容 PyInstaller 打包后的 exe 环境（此时 sys.executable 指向 exe 本身）。
    """
    # 1. 如果不是打包 exe（未 frozen），直接用 sys.executable
    if not getattr(sys, "frozen", False):
        return sys.executable

    # 2. 打包 exe 场景：从 exe 同目录查找 Python
    exe_dir = os.path.dirname(sys.executable)
    bundled_python = os.path.join(exe_dir, "python.exe")
    if os.path.isfile(bundled_python):
        return bundled_python

    # 3. 尝试 common Python 安装路径
    common_paths = [
        r"D:\Python\Python311\python.exe",
        r"D:\Python\Python310\python.exe",
        r"D:\Python\Python39\python.exe",
        r"C:\Python311\python.exe",
        r"C:\Python310\python.exe",
        r"C:\Python39\python.exe",
        r"D:\Python\Python312\python.exe",
        r"D:\Python\Python38\python.exe",
    ]
    for p in common_paths:
        if os.path.isfile(p):
            return p

    # 4. 从系统 PATH 搜索
    which_python = _shutil.which("python") or _shutil.which("python3")
    if which_python:
        return which_python

    # 找不到就报错
    raise FileNotFoundError("未找到 Python 解释器，请确保已安装 Python 并在系统 PATH 中")


# ── URL 转换器：精选/话题/搜索页 → 视频页 ────────────────
from urllib.parse import urlparse, parse_qs

def _normalize_douyin_url(url: str) -> str:
    """
    将各种格式的抖音链接转换为视频页链接。
    支持:
      - https://www.douyin.com/jingxuan?modal_id=xxx
      - https://www.douyin.com/discovery?modal_id=xxx
      - https://www.douyin.com/video/xxx（直接返回）
      - https://v.douyin.com/xxx（直接返回）
    """
    url = url.strip()
    parsed = urlparse(url)

    # 如果路径已经是 /video/xxx，直接返回
    if "/video/" in parsed.path:
        return url

    # 如果是 v.douyin.com 短链，直接返回（f2 自己会处理）
    if "v.douyin.com" in parsed.hostname:
        return url

    # 如果路径是 /jingxuan、/discovery 等带 modal_id 的
    if "modal_id" in parsed.query:
        modal_id = parse_qs(parsed.query).get("modal_id", [None])[0]
        if modal_id:
            normalized = f"https://www.douyin.com/video/{modal_id}"
            return normalized

    # 让 f2 自己处理
    return url


# ── 工具函数 ──────────────────────────────────────────
def log(widget: scrolledtext.ScrolledText, msg: str):
    """线程安全地向日志框追加一行"""
    def _append():
        ts = datetime.now().strftime("%H:%M:%S")
        widget.insert(tk.END, f"[{ts}] {msg}\n")
        widget.see(tk.END)
    widget.after(0, _append)


def run_f2_download(video_url: str, cookie_str: str, save_path: str,
                    log_widget: scrolledtext.ScrolledText,
                    on_finish=None):
    """调用 f2 下载视频（在新线程中运行）"""
    log(log_widget, f"开始下载: {video_url}")
    log(log_widget, f"保存目录: {save_path}")

    os.makedirs(save_path, exist_ok=True)

    python_exe = _find_python_executable()
    cmd = [
        python_exe, "-m", F2_MODULE,
        "dy", "-M", DOWNLOAD_MODE,
        "-u", video_url,
        "-k", cookie_str,
        "-p", save_path,
    ]

    log(log_widget, f"执行命令: {python_exe} -m {F2_MODULE} dy ...")

    try:
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding="utf-8",
            errors="replace",
            env=env,
            cwd=save_path,
        )

        for line in proc.stdout:
            line = line.strip()
            if line:
                log(log_widget, line)

        proc.wait()

        if proc.returncode == 0:
            log(log_widget, "✅ 下载完成！")
            messagebox.showinfo("完成", "视频下载完成！")
        else:
            log(log_widget, f"❌ 下载失败，退出码: {proc.returncode}")
            messagebox.showerror("错误", f"下载失败，退出码: {proc.returncode}")

    except FileNotFoundError:
        log(log_widget, "❌ 未找到 f2，请先执行: pip install f2")
        messagebox.showerror(
            "缺少依赖",
            "未找到 f2 工具！\n\n请先安装：\n  pip install f2\n\n然后重新运行本程序。"
        )
    except Exception as e:
        log(log_widget, f"❌ 发生异常: {e}")
        messagebox.showerror("异常", str(e))
    finally:
        if on_finish:
            on_finish()


# ── GUI 主窗口 ────────────────────────────────────────
class DouyinDownloaderApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("抖音视频无水印下载器  v1.0")
        self.geometry("750x620")
        self.resizable(True, True)

        self.video_url = tk.StringVar()
        self.cookie_str = tk.StringVar()
        self.save_path = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Downloads", "DouyinVideos"))
        self.is_downloading = False
        self.is_fetching_cookie = False

        self._build_widgets()

    def _build_widgets(self):
        container = ttk.Frame(self, padding=12)
        container.pack(fill=tk.BOTH, expand=True)

        # 1. 视频链接
        frm_url = ttk.LabelFrame(container, text="① 视频链接", padding=8)
        frm_url.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(frm_url, text="支持完整链接或短链接（v.douyin.com/xxx）：").pack(anchor=tk.W)
        ent_url = ttk.Entry(frm_url, textvariable=self.video_url, font=("Consolas", 10))
        ent_url.pack(fill=tk.X, pady=(4, 0))
        ent_url.insert(0, "https://v.douyin.com/")

        # 2. Cookie 输入
        frm_cookie = ttk.LabelFrame(container, text="② Cookie（必填）", padding=8)
        frm_cookie.pack(fill=tk.X, pady=(0, 8))

        btn_row = ttk.Frame(frm_cookie)
        btn_row.pack(fill=tk.X, pady=(0, 4))

        self.btn_auto_cookie = ttk.Button(
            btn_row, text="🔄  自动获取 Cookie（推荐）",
            command=self._auto_fetch_cookie,
        )
        self.btn_auto_cookie.pack(side=tk.LEFT, padx=(0, 8))

        btn_cookie_help = ttk.Button(
            btn_row, text="📋  手动获取教程",
            command=self._show_cookie_help,
        )
        btn_cookie_help.pack(side=tk.LEFT)

        self.lbl_cookie_status = ttk.Label(frm_cookie, text="", foreground="#888", font=("", 8))
        self.lbl_cookie_status.pack(anchor=tk.W)

        self.txt_cookie = tk.Text(frm_cookie, height=4, font=("Consolas", 9))
        self.txt_cookie.pack(fill=tk.X)

        # 3. 保存路径
        frm_path = ttk.LabelFrame(container, text="③ 保存路径", padding=8)
        frm_path.pack(fill=tk.X, pady=(0, 8))

        path_frame = ttk.Frame(frm_path)
        path_frame.pack(fill=tk.X)

        ent_path = ttk.Entry(path_frame, textvariable=self.save_path, font=("Consolas", 10))
        ent_path.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))

        ttk.Button(path_frame, text="浏览...", command=self._browse_path).pack(side=tk.LEFT)

        # 4. 操作按钮
        frm_btn = ttk.Frame(container)
        frm_btn.pack(fill=tk.X, pady=(0, 8))

        self.btn_download = ttk.Button(
            frm_btn, text="⬇  开始下载",
            command=self._start_download,
        )
        self.btn_download.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(frm_btn, text="清空日志", command=self._clear_log).pack(side=tk.LEFT)

        # 5. 日志输出
        frm_log = ttk.LabelFrame(container, text="④ 运行日志", padding=8)
        frm_log.pack(fill=tk.BOTH, expand=True)

        self.txt_log = scrolledtext.ScrolledText(
            frm_log, height=12, font=("Consolas", 9),
            bg="#1e1e1e", fg="#d4d4d4", insertbackground="#fff",
        )
        self.txt_log.pack(fill=tk.BOTH, expand=True)

        self.status_bar = ttk.Label(self, text="就绪", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self._log("欢迎使用抖音视频无水印下载器！")
        if PLAYWRIGHT_AVAILABLE:
            self._log("💡 点击「自动获取 Cookie」即可一键获取，无需手动操作")
        else:
            self._log("💡 建议安装 playwright：pip install playwright && playwright install chromium")

    def _log(self, msg: str):
        log(self.txt_log, msg)

    def _browse_path(self):
        path = filedialog.askdirectory(initialdir=self.save_path.get())
        if path:
            self.save_path.set(path)

    def _show_cookie_help(self):
        help_text = (
            "【手动获取 Cookie 步骤】\n\n"
            "1. 用 Chrome/Edge 打开 https://www.douyin.com/ 并登录\n"
            "2. 按 F12 打开开发者工具\n"
            "3. 切换到 Application（应用程序）标签\n"
            "4. 左侧找到 Cookies → https://www.douyin.com\n"
            "5. 找到以下关键 Cookie 并复制值：\n"
            "   • ttwid（最重要）\n"
            "   • odin_tt\n"
            "   • passport_csrf_token\n"
            "   • __ac_nonce\n"
            "   • __ac_signature\n\n"
            "6. 拼成这样一行：\n"
            "   ttwid=值1; odin_tt=值2; passport_csrf_token=值3; ...\n\n"
            "💡 更简单：直接点上方「自动获取 Cookie」按钮！"
        )
        messagebox.showinfo("手动获取 Cookie 教程", help_text)

    def _auto_fetch_cookie(self):
        if self.is_fetching_cookie:
            messagebox.showinfo("提示", "正在获取 Cookie 中，请稍候...")
            return

        if not PLAYWRIGHT_AVAILABLE:
            result = messagebox.askyesno(
                "缺少依赖",
                "检测到未安装 Playwright，自动获取功能需要此依赖。\n\n"
                "是否现在安装？（需要几分钟）\n\n"
                "安装命令：\n"
                "pip install playwright && playwright install chromium"
            )
            if result:
                self._install_playwright_and_fetch()
            return

        self.is_fetching_cookie = True
        self.btn_auto_cookie.config(state=tk.DISABLED, text="🔄 获取中...")
        self.lbl_cookie_status.config(text="⏳ 正在打开浏览器，请稍候...", foreground="#e67e22")

        def _fetch():
            try:
                cookie_str = fetch_cookies_auto(
                    on_log=lambda msg: self._log(msg),
                    timeout=90, headless=False,
                )
            except Exception:
                cookie_str = None

            def _on_done():
                self.is_fetching_cookie = False
                self.btn_auto_cookie.config(state=tk.NORMAL, text="🔄  自动获取 Cookie（推荐）")
                if cookie_str:
                    self.txt_cookie.delete("1.0", tk.END)
                    self.txt_cookie.insert("1.0", cookie_str)
                    self.lbl_cookie_status.config(text="✅ Cookie 获取成功！", foreground="#27ae60")
                    self._log(f"✅ Cookie 已填入，共 {cookie_str.count('=')} 个字段")
                    messagebox.showinfo("成功", "Cookie 获取成功！可以开始下载了。")
                else:
                    self.lbl_cookie_status.config(text="❌ 获取失败，请尝试手动获取 Cookie", foreground="#e74c3c")
                    self._log("⚠️ Cookie 获取失败，请手动复制 Cookie 后继续")

            self.after(0, _on_done)

        threading.Thread(target=_fetch, daemon=True).start()

    def _install_playwright_and_fetch(self):
        self.btn_auto_cookie.config(state=tk.DISABLED, text="⏳  安装中...")
        self.lbl_cookie_status.config(text="⏳ 正在安装 Playwright，请稍候...", foreground="#e67e22")
        self._log("🔧 开始安装 playwright...")

        def _install():
            success = False
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", "playwright"],
                               capture_output=True, timeout=120)
                subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"],
                               capture_output=True, timeout=300)
                global PLAYWRIGHT_AVAILABLE
                from playwright_helper import fetch_cookies_auto
                PLAYWRIGHT_AVAILABLE = True
                success = True
            except Exception:
                pass

            def _on_done():
                if success:
                    self.lbl_cookie_status.config(text="✅ Playwright 安装成功！", foreground="#27ae60")
                    self._log("✅ playwright 安装成功！")
                    self.after(100, self._auto_fetch_cookie)
                else:
                    self.btn_auto_cookie.config(state=tk.NORMAL, text="🔄  自动获取 Cookie（推荐）")
                    self.lbl_cookie_status.config(text="❌ 安装失败，请手动安装 playwright", foreground="#e74c3c")

            self.after(0, _on_done)

        threading.Thread(target=_install, daemon=True).start()

    def _clear_log(self):
        self.txt_log.delete("1.0", tk.END)
        self._log("日志已清空。")

    def _start_download(self):
        if self.is_downloading:
            messagebox.showwarning("提示", "正在下载中，请稍候...")
            return

        url = self.video_url.get().strip()
        if not url:
            messagebox.showwarning("警告", "请填写视频链接！")
            return
        if "douyin" not in url and "v.douyin" not in url:
            messagebox.showwarning("警告", "链接看起来不是抖音视频链接！")
            return

        # 转换精选页/话题页链接为视频页链接
        original_url = url
        url = _normalize_douyin_url(url)
        if url != original_url:
            self._log(f"🔗 链接格式转换: {original_url}")
            self._log(f"   → {url}")

        cookie_raw = self.txt_cookie.get("1.0", tk.END).strip()
        if not cookie_raw or cookie_raw == "ttwid=; odin_tt=; ":
            messagebox.showwarning("警告", "请填写 Cookie 字符串！")
            return

        save_path = self.save_path.get().strip()
        if not save_path:
            messagebox.showwarning("警告", "请选择保存路径！")
            return

        self.is_downloading = True
        self.btn_download.config(state=tk.DISABLED)
        self.status_bar.config(text="下载中...")

        def _on_finish():
            self.is_downloading = False
            self.btn_download.config(state=tk.NORMAL)
            self.status_bar.config(text="就绪")

        threading.Thread(
            target=run_f2_download,
            args=(url, cookie_raw, save_path, self.txt_log, _on_finish),
            daemon=True,
        ).start()

    def on_closing(self):
        if self.is_downloading:
            if not messagebox.askokcancel("确认", "正在下载中，确定要退出吗？"):
                return
        self.destroy()


# ── 入口 ──────────────────────────────────────────────
if __name__ == "__main__":
    app = DouyinDownloaderApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
