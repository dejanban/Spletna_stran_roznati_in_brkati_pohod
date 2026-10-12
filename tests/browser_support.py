"""Allow browser checks on Edge installations and portable Chromium setups."""
import os


def launch_browser(playwright):
    executable = os.environ.get('BROWSER_EXECUTABLE')
    if executable:
        return playwright.chromium.launch(executable_path=executable, headless=True)
    return playwright.chromium.launch(channel='msedge', headless=True)
