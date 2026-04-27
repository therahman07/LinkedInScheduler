from playwright.sync_api import sync_playwright
import os

# =====================================================
# SETTINGS
# =====================================================

# Uses local project folder automatically
PROFILE = "profile"

CHROME_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]

# =====================================================
# FIND CHROME
# =====================================================
def get_chrome_path():
    for path in CHROME_PATHS:
        if os.path.exists(path):
            return path
    raise Exception("Google Chrome not found. Please install Chrome.")

# =====================================================
# LINKEDIN POSTER
# =====================================================
def post_linkedin(caption, image_path):
    chrome_path = get_chrome_path()

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE,
            executable_path=chrome_path,
            headless=False,
            args=["--start-maximized"]
        )

        page = browser.new_page()
        page.goto("https://www.linkedin.com/feed/")
        page.wait_for_timeout(6000)

        try:
            page.locator("button").filter(has_text="Start a post").first.click()
        except:
            page.locator("button").filter(has_text="Create a post").first.click()

        page.wait_for_timeout(3000)

        editor = page.locator("[role='textbox']").first
        editor.fill(caption)

        if image_path and os.path.exists(image_path):
            try:
                page.locator("input[type='file']").first.set_input_files(image_path)
                page.wait_for_timeout(6000)
            except:
                pass

        page.locator("button").filter(has_text="Post").last.click()
        page.wait_for_timeout(8000)

        browser.close()