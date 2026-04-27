from playwright.sync_api import sync_playwright

PROFILE = r"C:\LinkedInSchedulerV4\profile"

with sync_playwright() as p:
    browser = p.chromium.launch_persistent_context(
        user_data_dir=PROFILE,
        headless=False
    )

    page = browser.new_page()
    page.goto("https://www.linkedin.com/login")

    input("Login to LinkedIn manually, then press Enter...")

    browser.close()