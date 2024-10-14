from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


import time,os,sys
def find_chrome_binary():
    """Locate the Chrome binary on the system."""
    # TODO env
    # You can find it from "chrome://version/"
    if sys.platform.startswith('win'):
        paths = [
            os.path.expanduser('~') + r'\AppData\Local\Google\Chrome\Application\chrome.exe',
            r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
            r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        ]
    elif sys.platform.startswith('linux'):
        paths = [
            '/app/extra/chrome',
            '/usr/bin/google-chrome',
            '/usr/bin/chrome',
            '/usr/bin/chromium-browser',
        ]
    elif sys.platform.startswith('darwin'):  # macOS
        paths = [
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            '~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        ]
    else:
        raise ValueError(f"Unsupported operating system: {sys.platform}")

    for path in paths:
        if os.path.exists(path):
            return path
    
    return None


def setup_gemini_web():
    user_profile = os.environ.get('CHROME_USER_PROFILE','/home/rsong/.var/app/com.google.Chrome/config/google-chrome')
    options = webdriver.ChromeOptions()
    options.add_argument(f"user-data-dir={user_profile}")

    # Default Chrome profile location for different operating systems
    '''
    if user_data_dir:
            chrome_options.add_argument(f"user-data-dir={user_data_dir}")
        else:
            # Default Chrome profile location for different operating systems
            if os.name == 'nt':  # Windows
                user_data_dir = os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'Google', 'Chrome', 'User Data')
            elif os.name == 'posix':  # macOS and Linux
                if os.uname().sysname == 'Darwin':  # macOS
                    user_data_dir = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', 'Google', 'Chrome')
                else:  # Linux
                    user_data_dir = os.path.join(os.path.expanduser('~'), '.config', 'google-chrome')
            chrome_options.add_argument(f"user-data-dir={user_data_dir}")
  
    '''
    options.add_argument("--profile-directory=Default")  # Use the default profile
    #options.add_argument('--headless=new')  # Use '--headless' for older Chrome versions
    #options.add_argument("--no-sandbox")
    options.add_argument("--profile-directory=Default")  # Use the default profile
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    options.add_argument("--window-size=1920,1080")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
        
    print(f"Using Chrome profile: {user_profile}")

    #chrome_binary = find_chrome_binary()
    chrome_binary = '/var/lib/flatpak/app/com.google.Chrome/current/active/files/bin/chrome'
    if chrome_binary:
        options.binary_location = chrome_binary
    else:
        print("Chrome binary not found. Please ensure Chrome is installed and try again.")
        sys.exit(1)
   
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=options)
    # Alternative Gemini Gem Link: https://gemini.google.com/gem/9e32bbf9b9df
    # TODO - load this from env
    driver.get("https://gemini.google.com/app")
    if not is_logged_in(driver):
            print("Not logged in. Please log in manually.")
            input("Press Enter when you have logged in...")

    return driver

def is_logged_in(driver):
    try:
        # Check for an element that's only present when logged in
        driver.find_element(By.XPATH, "//button[contains(., 'New chat')]")
        print("Successfully logged in.")
        return True
    except NoSuchElementException:
        print("Not logged in.")
        return False

system_prompt  = ''' 
Purpose and Goals:


* Watch the Youtube video provided in the video link.

* Clearly and concisely summarize the key stock market changes, influencing factors, market responses, and company-specific news discussed in the video.

* Ensure the summary is easy to understand, focuses on relevant information, and is presented objectively. 



Behaviors and Rules:



1. Video Analysis:

a) Watch the entire video carefully, paying close attention to the discussion of stock market changes, influencing factors, market reactions, and company-specific news.

b) Identify the most significant market shifts or trends mentioned in the video.

c) Clearly explain the factors that contributed to each market change and, if discussed in the video, how the market reacted to these changes.

d) List all companies mentioned in the video and provide a summary of any relevant news or developments related to each company.



2. Summary Creation:

a) Craft a clear, concise, and easy-to-understand summary of the key points from the video.

b) Prioritize the most significant market changes and interesting recent changes while ensuring a balanced overview.

c) For company-specific news, provide more details if available in the video.

d) Present the information in a neutral and unbiased manner, avoiding personal opinions or speculation.



Overall Tone:

* Use clear, simple, and professional language.

* Maintain objectivity and avoid any bias in the summary.

* Ensure the summary is informative and valuable to the user.

Video Link: 
'''

def interact_with_gemini_web(driver, prompt):
    
    # TODO input box is, rich-textarea
    # TODO Gems is  #app-root > main > side-navigation-v2 > bard-sidenav-container > bard-sidenav > div > div > div.chat-history > bot-list > div.bots-list-container.ng-tns-c2356764211-14.ng-star-inserted > bot-list-item.ng-tns-c2356764211-14.bot-list-item--expanded.ng-star-inserted.bot-list-item--selected > div > button.mat-mdc-tooltip-trigger.bot-new-conversation-button
    
    # TODO wait the response till there is message-content, or no data exchange
    #  WebDriverWait(driver, 10).until(no_pending_requests)
    try:
        # Wait for the input field to be visible
        input_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "textarea[placeholder='Enter a prompt here']"))
        )
        input_field.send_keys(prompt)
        input_field.send_keys(Keys.RETURN)

        # Wait for the response to appear
        response_selector = "div[data-model-response='true']"
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, response_selector))
        )
        
        # Give a moment for the full response to load
        time.sleep(2)

        # Get the response text
        response_element = driver.find_element(By.CSS_SELECTOR, response_selector)
        return response_element.text
    except TimeoutException:
        return "Timeout waiting for Gemini response"


def main():
    # Set up Gemini web interface
    driver = setup_gemini_web()

    # Interact with Gemini
    prompt = system_prompt + " https://www.youtube.com/watch?v=vXj4XBhRjQs"
    response = interact_with_gemini_web(driver, prompt)
    print(f"Gemini response: {response}")

    # Close the browser
    driver.quit()


if __name__ == '__main__':
    main()