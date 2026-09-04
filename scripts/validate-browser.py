#!/usr/bin/env python3
"""Headless Chromium regression for every Search-eligible route plus contained UX."""
from __future__ import annotations
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "final-2026-09-04" / "screenshots"
REPORT.mkdir(parents=True, exist_ok=True)
routes = json.loads((ROOT / "content/index-allowlist.json").read_text())["routes"]
failures: list[str] = []
warnings: list[str] = []


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_server(base: str) -> None:
    for _ in range(80):
        try:
            with urllib.request.urlopen(base + "/", timeout=1) as response:
                if response.status == 200:
                    return
        except Exception:
            time.sleep(.1)
    raise RuntimeError("local BRYME server did not start")


port = free_port()
env = {**os.environ, "PORT": str(port), "HOST": "127.0.0.1", "WATCHDOG": "off", "TELEGRAM_ENABLED": "0"}
proc = subprocess.Popen(["node", "server/server.js"], cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
base = f"http://127.0.0.1:{port}"
driver = None
try:
    wait_server(base)
    options = Options()
    for arg in ("--headless=new", "--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu", "--hide-scrollbars", "--force-color-profile=srgb"):
        options.add_argument(arg)
    options.page_load_strategy = "eager"
    options.set_capability("goog:loggingPrefs", {"browser": "ALL"})
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(18)

    viewports = [(390, 844, "mobile"), (1440, 1000, "desktop")]
    screenshot_routes = {"/", "/jobs/verified-2026-09-04/", "/article/why-prison-break-season-1-is-still-one-of-the-best-tv-seasons/"}
    checked = 0
    for width, height, label in viewports:
        driver.set_window_size(width, height)
        for route in routes:
            try:
                driver.get(base + route)
                WebDriverWait(driver, 8).until(lambda d: d.execute_script("return document.readyState") in ("interactive", "complete"))
                result = driver.execute_script("""
                  const q = s => [...document.querySelectorAll(s)];
                  const canonical = document.querySelector('link[rel="canonical"]');
                  const robots = document.querySelector('meta[name="robots"]');
                  const styles = q('link[rel="stylesheet"]').map(x => new URL(x.href).pathname);
                  const scripts = q('script[src]').map(x => new URL(x.src).pathname);
                  const skip = document.querySelector('a.skip-link[href="#main"]');
                  return {
                    title: document.title,
                    h1: q('h1').length,
                    main: !!document.querySelector('main#main'),
                    skip: !!skip,
                    robots: robots ? robots.content : '',
                    canonical: canonical ? new URL(canonical.href).pathname : '',
                    styles, scripts,
                    viewport: window.innerWidth,
                    scrollWidth: document.documentElement.scrollWidth,
                    textLength: (document.querySelector('main')?.innerText || '').trim().length,
                    bodyColor: getComputedStyle(document.body).color,
                    bodyBg: getComputedStyle(document.body).backgroundColor,
                    nav: q('nav a[href]').length,
                    unloadedLocalImages: q('img').filter(img => img.src.startsWith(location.origin) && img.complete && !img.naturalWidth).map(img => img.src)
                  };
                """)
                expected = route
                if result["h1"] != 1: failures.append(f"{label} {route}: {result['h1']} H1 elements")
                if not result["main"]: failures.append(f"{label} {route}: no main#main")
                if not result["skip"]: failures.append(f"{label} {route}: no skip link")
                if "noindex" in result["robots"].lower(): failures.append(f"{label} {route}: rendered noindex")
                if result["canonical"].rstrip("/") != expected.rstrip("/"): failures.append(f"{label} {route}: canonical {result['canonical']}")
                if result["scrollWidth"] > result["viewport"] + 2: failures.append(f"{label} {route}: horizontal overflow {result['scrollWidth']} > {result['viewport']}")
                if result["textLength"] < 120: failures.append(f"{label} {route}: thin rendered main ({result['textLength']} chars)")
                if result["nav"] < 3: failures.append(f"{label} {route}: primary navigation missing")
                if any(x.endswith("/assets/site.css") for x in result["styles"]): failures.append(f"{label} {route}: rendered legacy CSS")
                if not any(x.endswith(("/assets/bryme-v2.css", "/assets/content-v2.css")) for x in result["styles"]): failures.append(f"{label} {route}: focused stylesheet missing")
                if result["scripts"]: failures.append(f"{label} {route}: client scripts present {result['scripts']}")
                if result["unloadedLocalImages"]: failures.append(f"{label} {route}: broken local images {result['unloadedLocalImages'][:2]}")
                severe = [x for x in driver.get_log("browser") if x.get("level") == "SEVERE" and "favicon" not in x.get("message", "").lower()]
                if severe: warnings.append(f"{label} {route}: browser console {severe[0]['message'][:180]}")
                if route in screenshot_routes:
                    slug = "home" if route == "/" else route.strip("/").replace("/", "-")
                    driver.save_screenshot(str(REPORT / f"{slug}-{label}.png"))
                checked += 1
            except (TimeoutException, WebDriverException, Exception) as exc:
                failures.append(f"{label} {route}: browser error {type(exc).__name__}: {str(exc)[:180]}")

    # Containment UX: a trailer must not create an iframe until explicit input.
    driver.set_window_size(390, 844)
    driver.get(base + "/movie/the-invite/")
    before = len(driver.find_elements(By.CSS_SELECTOR, "iframe"))
    try:
        play_button = WebDriverWait(driver, 6).until(lambda d: d.find_element(By.CSS_SELECTOR, ".trailer-play"))
    except TimeoutException:
        play_button = None
    if before:
        failures.append("title containment: trailer iframe exists before interaction")
    elif not play_button:
        failures.append("title containment: explicit trailer control missing")
    else:
        driver.execute_script("arguments[0].click()", play_button)
        try:
            WebDriverWait(driver, 6).until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "iframe")) > 0)
            src = driver.find_element(By.CSS_SELECTOR, "iframe").get_attribute("src") or ""
            if "youtube-nocookie.com/embed/" not in src:
                failures.append(f"title containment: unexpected embed URL {src}")
        except TimeoutException:
            failures.append("title containment: trailer did not load after explicit interaction")
    title_state = driver.execute_script("return {robots:document.querySelector('meta[name=robots]')?.content||'', controls:document.querySelectorAll('[data-nm-my-list],[data-nm-rate],.nm-trailer').length, notice:!!document.querySelector('.nm-source-note,.source-note')}")
    if "noindex" not in title_state["robots"].lower(): failures.append("title containment: title route is indexable")
    if title_state["controls"]: failures.append("title containment: unsupported controls remain")
    driver.save_screenshot(str(REPORT / "movie-the-invite-mobile.png"))

    driver.get(base + "/sports/football/")
    sports = driver.execute_script("return {robots:document.querySelector('meta[name=robots]')?.content||'', paused:document.body.innerText.includes('Sports data paused.')}")
    if "noindex" not in sports["robots"].lower() or not sports["paused"]:
        failures.append("sports containment: noindex or visible pause warning missing")

finally:
    if driver:
        driver.quit()
    proc.terminate()
    try:
        proc.wait(timeout=4)
    except subprocess.TimeoutExpired:
        proc.kill()

summary = {"ok": not failures, "routes": len(routes), "renderedCases": locals().get("checked", 0), "viewports": ["390x844", "1440x1000"], "warnings": len(warnings), "screenshots": str(REPORT.relative_to(ROOT))}
if warnings:
    print("WARNINGS")
    for item in warnings[:20]: print("  -", item)
if failures:
    print(f"FAIL ({len(failures)})", file=sys.stderr)
    for item in failures[:80]: print("  -", item, file=sys.stderr)
    print(json.dumps(summary, indent=2))
    raise SystemExit(1)
print(json.dumps(summary, indent=2))
