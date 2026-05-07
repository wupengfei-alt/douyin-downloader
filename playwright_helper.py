#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音 Cookie 自动获取模块
依赖: pip install playwright && playwright install chromium
"""

import time
import sys
from playwright.sync_api import sync_playwright


# 需要提取的 Cookie 名称列表
KEY_COOKIES = [
    "ttwid",
    "odin_tt",
    "passport_csrf_token",
    "__ac_nonce",
    "__ac_signature",
    "s_v_web_id",
    "UIFID",
    "fpk1",
    "fpk2",
]

# 抖音目标域名
DOUYIN_URL = "https://www.douyin.com/"


def build_cookie_str(cookies: list) -> str:
    """从 cookies 列表构建 Cookie 字符串"""
    cookie_map = {c["name"]: c["value"] for c in cookies}
    parts = [f"{name}={cookie_map.get(name, '')}" for name in KEY_COOKIES if name in cookie_map]
    return "; ".join(parts)


def fetch_cookies_auto(
    on_log=None,
    timeout: int = 60,
    headless: bool = False,
) -> str | None:
    """
    自动获取抖音 Cookie。

    参数:
        on_log:     日志回调函数，接收字符串参数
        timeout:    最大等待时间（秒），超时后返回 None
        headless:   是否无头模式（True=不显示浏览器窗口）

    返回:
        Cookie 字符串（成功）或 None（失败）
    """

    def log(msg: str):
        if on_log:
            on_log(msg)

    log("🔄 启动浏览器...")

    playwright = None
    browser = None
    try:
        playwright = sync_playwright().start()

        browser_args = [
            "--disable-blink-features=AutomationControlled",
            "--no-first-run",
            "--no-service-initialize",
            "--disable-background-networking",
        ]

        # 尝试方式 1：使用系统已安装的 Chrome
        system_chrome_found = False
        for channel in ["chromium", "chrome", "msedge"]:
            try:
                browser = playwright.chromium.launch(
                    channel=channel,
                    headless=headless,
                    args=browser_args,
                )
                log(f"✅ 启动 {channel}")
                system_chrome_found = True
                break
            except Exception:
                continue

        # 方式 1 失败 → 方式 2：启动 Playwright 自带的 chromium（干净环境）
        if not system_chrome_found:
            browser = playwright.chromium.launch(
                headless=headless,
                args=browser_args,
            )
            log("✅ 启动 Playwright 内置 Chromium")

        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
            extra_http_headers={
                "Accept-Language": "zh-CN,zh;q=0.9",
            },
        )

        page = context.new_page()

        log(f"🌐 打开抖音网页: {DOUYIN_URL}")
        try:
            response = page.goto(DOUYIN_URL, wait_until="domcontentloaded", timeout=30000)
            log(f"📡 页面状态: {response.status if response else '无响应'}")
        except Exception as e:
            log(f"⚠️ 页面加载超时: {e}")

        time.sleep(2)

        # 检查是否已登录
        try:
            page.wait_for_selector('[data-e2e="user-avatar"], [class*="login"]', timeout=5)
            log("✅ 检测到已登录状态")
        except Exception:
            log("⚠️ 未检测到登录状态...")

        log("⏳ 等待页面稳定...")
        time.sleep(3)

        # 尝试获取 Cookie
        cookies = context.cookies([DOUYIN_URL, "https://www.douyin.com"])
        cookie_str = build_cookie_str(cookies)

        # 验证 Cookie 是否有效
        if cookie_str and "ttwid=" in cookie_str:
            log(f"✅ 成功提取 {len(cookies)} 个 Cookie")
            return cookie_str

        # 重试机制
        for i in range(10):
            time.sleep(2)
            cookies = context.cookies([DOUYIN_URL, "https://www.douyin.com"])
            cookie_str = build_cookie_str(cookies)
            if cookie_str and "ttwid=" in cookie_str:
                log(f"✅ 延迟等待后成功提取 {len(cookies)} 个 Cookie")
                return cookie_str
            log(f"   等待中... ({i+1}/10)")

        log("❌ Cookie 提取失败，可能未登录")
        return None

    except Exception as e:
        log(f"❌ 发生异常: {e}")
        return None

    finally:
        if browser:
            browser.close()
        if playwright:
            try:
                playwright.stop()
            except Exception:
                pass


# ── 调试入口 ──────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 50)
    print("抖音 Cookie 自动获取工具（调试模式）")
    print("=" * 50)
    print()

    result = fetch_cookies_auto(
        on_log=print,
        timeout=60,
        headless=False,
    )

    print()
    if result:
        print("=" * 50)
        print("✅ 获取成功！Cookie 字符串：")
        print("=" * 50)
        print(result[:200] + "..." if len(result) > 200 else result)
    else:
        print("❌ 获取失败")
