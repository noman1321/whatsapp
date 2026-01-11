"""
WhatsApp Web Bulk Message Sender (Simplified Version)
Works better on Windows - uses simpler ChromeDriver setup
"""

import csv
import time
import random
import os
import sys
from typing import List, Dict

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
except ImportError:
    print("ERROR: Selenium not installed. Run: pip install selenium")
    sys.exit(1)

# Configuration
CSV_FILE = "sample.csv"
MIN_DELAY = 5
MAX_DELAY = 10
QR_SCAN_TIMEOUT = 120

def print_colored(message: str, color: str = "white"):
    """Print colored text"""
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "white": "\033[0m"
    }
    print(f"{colors.get(color, colors['white'])}{message}\033[0m")

def read_csv(file_path: str) -> List[Dict[str, str]]:
    """Read CSV file"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"CSV file not found: {file_path}")
    
    contacts = []
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row.get('name') and row.get('phone') and row.get('message'):
                contacts.append({
                    'name': row['name'].strip(),
                    'phone': row['phone'].strip().replace(' ', ''),
                    'message': row['message'].strip()
                })
    return contacts

def setup_driver():
    """Set up Chrome driver - simplified version"""
    print_colored("Setting up Chrome browser...", "blue")
    
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.notifications": 2
    })
    
    try:
        # Try method 1: Let Selenium find ChromeDriver automatically
        print_colored("  → Attempting automatic setup...", "blue")
        driver = webdriver.Chrome(options=chrome_options)
        print_colored("✓ Browser setup complete!", "green")
        return driver
        
    except Exception as e1:
        print_colored(f"  ✗ Automatic setup failed: {str(e1)[:100]}", "yellow")
        
        # Try method 2: Using webdriver-manager
        try:
            print_colored("  → Trying webdriver-manager...", "blue")
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager
            
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            print_colored("✓ Browser setup complete!", "green")
            return driver
            
        except Exception as e2:
            print_colored(f"\n✗ Both methods failed!", "red")
            print_colored("\n📌 Manual Setup Required:", "yellow")
            print_colored("\nOption 1: Install ChromeDriver manually", "white")
            print_colored("1. Check your Chrome version: chrome://version/", "white")
            print_colored("2. Download matching ChromeDriver from:", "white")
            print_colored("   https://googlechromelabs.github.io/chrome-for-testing/", "white")
            print_colored("3. Extract chromedriver.exe to this folder", "white")
            print_colored("4. Run script again", "white")
            print_colored("\nOption 2: Update Chrome browser", "white")
            print_colored("1. Open Chrome", "white")
            print_colored("2. Go to chrome://settings/help", "white")
            print_colored("3. Update to latest version", "white")
            print_colored("4. Run script again", "white")
            raise Exception("Could not setup Chrome driver")

def send_message(driver, wait, phone: str, message: str) -> bool:
    """Send a message"""
    try:
        url = f"https://web.whatsapp.com/send?phone={phone}&text={message}"
        driver.get(url)
        time.sleep(5)
        
        # Wait for message input
        selectors = [
            '//div[@contenteditable="true"][@data-tab="10"]',
            '//div[@contenteditable="true"][@role="textbox"]',
        ]
        
        for selector in selectors:
            try:
                wait.until(EC.presence_of_element_located((By.XPATH, selector)))
                break
            except:
                continue
        
        time.sleep(3)
        
        # Find and click send button
        try:
            send_btn = driver.find_element(By.XPATH, '//button[@data-testid="send"]')
        except:
            try:
                send_btn = driver.find_element(By.XPATH, '//button[.//span[@data-icon="send"]]')
            except:
                send_btn = driver.find_element(By.XPATH, '//button[contains(@aria-label, "Send")]')
        
        send_btn.click()
        time.sleep(2)
        return True
        
    except Exception as e:
        print_colored(f"Error: {str(e)[:100]}", "red")
        return False

def main():
    """Main function"""
    print("=" * 60)
    print("   WhatsApp Web Bulk Message Sender (Simple Version)")
    print("=" * 60)
    print()
    
    try:
        # Read CSV
        print_colored(f"Reading CSV file: {CSV_FILE}", "blue")
        contacts = read_csv(CSV_FILE)
        print_colored(f"✓ Found {len(contacts)} contacts", "green")
        
        print("\nContacts:")
        for i, c in enumerate(contacts, 1):
            print(f"  {i}. {c['name']} - {c['phone']}")
        
        response = input("\nProceed? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            print("Cancelled.")
            return
        
        # Setup browser
        driver = setup_driver()
        driver.maximize_window()
        wait = WebDriverWait(driver, 20)
        
        # Open WhatsApp
        print_colored("\nOpening WhatsApp Web...", "blue")
        driver.get("https://web.whatsapp.com")
        
        print_colored("\n" + "=" * 60, "yellow")
        print_colored("   SCAN QR CODE NOW!", "yellow")
        print_colored("   You have 3 minutes to scan", "yellow")
        print_colored("=" * 60 + "\n", "yellow")
        
        # Wait for login - try multiple selectors with longer timeout
        login_wait = WebDriverWait(driver, 180)  # 3 minutes
        logged_in = False
        
        login_selectors = [
            '//div[@contenteditable="true"][@data-tab="3"]',  # Search box
            '//div[@contenteditable="true"][@role="textbox"]',  # Any textbox
            '//canvas[@aria-label="Scan me!"]',  # QR code canvas (means not logged in)
        ]
        
        print_colored("Waiting for you to scan QR code...", "blue")
        
        try:
            # Keep checking every 5 seconds
            for attempt in range(36):  # 36 * 5 = 180 seconds
                try:
                    # Check if logged in (search box appears)
                    driver.find_element(By.XPATH, login_selectors[0])
                    logged_in = True
                    break
                except:
                    try:
                        driver.find_element(By.XPATH, login_selectors[1])
                        logged_in = True
                        break
                    except:
                        # Still on QR code screen
                        if attempt % 6 == 0:  # Print every 30 seconds
                            remaining = 180 - (attempt * 5)
                            print_colored(f"  Still waiting... ({remaining}s remaining)", "yellow")
                        time.sleep(5)
            
            if not logged_in:
                print_colored("✗ QR code scan timeout!", "red")
                print_colored("Please run the script again and scan faster", "yellow")
                driver.quit()
                return
                
        except Exception as e:
            print_colored(f"✗ Error waiting for login: {str(e)}", "red")
            driver.quit()
            return
        
        print_colored("✓ Logged in successfully!", "green")
        time.sleep(3)
        
        # Send messages
        print_colored(f"\n{'=' * 60}", "blue")
        print_colored(f"   Sending {len(contacts)} messages", "blue")
        print_colored(f"{'=' * 60}\n", "blue")
        
        sent = 0
        for i, contact in enumerate(contacts, 1):
            name = contact['name']
            phone = contact['phone']
            message = contact['message'].replace('{name}', name)
            
            print(f"\n[{i}/{len(contacts)}] {name} ({phone})")
            print(f"Message: {message[:50]}...")
            
            if send_message(driver, wait, phone, message):
                sent += 1
                print_colored(f"✓ Sent to {name}!", "green")
            else:
                print_colored(f"✗ Failed to send to {name}", "red")
            
            if i < len(contacts):
                delay = random.randint(MIN_DELAY, MAX_DELAY)
                print_colored(f"⏳ Waiting {delay}s...", "yellow")
                time.sleep(delay)
        
        # Summary
        print_colored(f"\n{'=' * 60}", "blue")
        print_colored(f"Total: {len(contacts)} | Sent: {sent} | Failed: {len(contacts) - sent}", "white")
        print_colored(f"{'=' * 60}\n", "blue")
        
        input("Press Enter to close...")
        driver.quit()
        
    except KeyboardInterrupt:
        print_colored("\n\nCancelled by user", "yellow")
    except Exception as e:
        print_colored(f"\nError: {str(e)}", "red")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
