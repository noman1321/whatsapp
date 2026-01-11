"""
WhatsApp Web Bulk Message Sender - GUI Version
Beautiful graphical interface for sending WhatsApp messages
"""

import csv
import time
import random
import os
import threading
from tkinter import *
from tkinter import ttk, filedialog, messagebox, scrolledtext
from typing import List, Dict

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException

# Configuration
MIN_DELAY = 5
MAX_DELAY = 10

class WhatsAppSenderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("WhatsApp Web Bulk Message Sender")
        self.root.geometry("750x750")
        self.root.resizable(True, True)
        
        # Variables
        self.csv_file = None
        self.contacts = []
        self.driver = None
        self.wait = None
        self.is_sending = False
        self.should_stop = False
        
        # Colors
        self.bg_color = "#f0f0f0"
        self.primary_color = "#25D366"
        self.secondary_color = "#128C7E"
        self.error_color = "#dc3545"
        
        self.root.configure(bg=self.bg_color)
        
        # Create UI
        self.create_widgets()
        
    def create_widgets(self):
        """Create all UI widgets"""
        
        # Header
        header_frame = Frame(self.root, bg=self.primary_color, height=80)
        header_frame.pack(fill=X)
        header_frame.pack_propagate(False)
        
        title_label = Label(
            header_frame,
            text="📱 WhatsApp Web Message Sender",
            font=("Arial", 20, "bold"),
            bg=self.primary_color,
            fg="white"
        )
        title_label.pack(pady=20)
        
        # Main container
        main_frame = Frame(self.root, bg=self.bg_color, padx=20, pady=20)
        main_frame.pack(fill=BOTH, expand=True)
        
        # CSV File Section
        csv_frame = LabelFrame(
            main_frame,
            text="📄 CSV File",
            font=("Arial", 12, "bold"),
            bg=self.bg_color,
            fg=self.secondary_color,
            padx=10,
            pady=10
        )
        csv_frame.pack(fill=X, pady=(0, 10))
        
        self.file_label = Label(
            csv_frame,
            text="No file selected",
            font=("Arial", 10),
            bg=self.bg_color,
            fg="#666"
        )
        self.file_label.pack(side=LEFT, padx=(0, 10))
        
        browse_btn = Button(
            csv_frame,
            text="Browse CSV",
            command=self.browse_file,
            bg=self.primary_color,
            fg="white",
            font=("Arial", 10, "bold"),
            cursor="hand2",
            relief=FLAT,
            padx=15,
            pady=5
        )
        browse_btn.pack(side=RIGHT)
        
        # Contacts Display
        contacts_frame = LabelFrame(
            main_frame,
            text="👥 Contacts",
            font=("Arial", 12, "bold"),
            bg=self.bg_color,
            fg=self.secondary_color,
            padx=10,
            pady=10
        )
        contacts_frame.pack(fill=BOTH, expand=True, pady=(0, 10))
        
        self.contacts_text = scrolledtext.ScrolledText(
            contacts_frame,
            height=6,
            font=("Consolas", 9),
            bg="white",
            fg="#333",
            relief=FLAT,
            borderwidth=2
        )
        self.contacts_text.pack(fill=BOTH, expand=True)
        self.contacts_text.insert(END, "No contacts loaded yet.\n\nUpload a CSV file to begin.")
        self.contacts_text.config(state=DISABLED)
        
        # Progress Section
        progress_frame = LabelFrame(
            main_frame,
            text="📊 Progress",
            font=("Arial", 12, "bold"),
            bg=self.bg_color,
            fg=self.secondary_color,
            padx=10,
            pady=10
        )
        progress_frame.pack(fill=X, pady=(0, 10))
        
        self.progress = ttk.Progressbar(
            progress_frame,
            length=400,
            mode='determinate'
        )
        self.progress.pack(fill=X, pady=(0, 5))
        
        self.progress_label = Label(
            progress_frame,
            text="0 / 0 messages sent",
            font=("Arial", 10),
            bg=self.bg_color,
            fg="#666"
        )
        self.progress_label.pack()
        
        # Status Log
        status_frame = LabelFrame(
            main_frame,
            text="📋 Status",
            font=("Arial", 12, "bold"),
            bg=self.bg_color,
            fg=self.secondary_color,
            padx=10,
            pady=10
        )
        status_frame.pack(fill=BOTH, expand=True, pady=(0, 10))
        
        self.status_text = scrolledtext.ScrolledText(
            status_frame,
            height=5,
            font=("Consolas", 9),
            bg="#f8f9fa",
            fg="#333",
            relief=FLAT,
            borderwidth=2
        )
        self.status_text.pack(fill=BOTH, expand=True)
        self.status_text.insert(END, "Ready. Please upload a CSV file to start.\n")
        self.status_text.config(state=DISABLED)
        
        # Control Buttons
        button_frame = Frame(main_frame, bg=self.bg_color)
        button_frame.pack(fill=X)
        
        self.start_btn = Button(
            button_frame,
            text="🚀 Start Sending",
            command=self.start_sending,
            bg=self.primary_color,
            fg="white",
            font=("Arial", 12, "bold"),
            cursor="hand2",
            relief=FLAT,
            padx=20,
            pady=10,
            state=DISABLED
        )
        self.start_btn.pack(side=LEFT, padx=(0, 10))
        
        self.stop_btn = Button(
            button_frame,
            text="⏹️ Stop",
            command=self.stop_sending,
            bg=self.error_color,
            fg="white",
            font=("Arial", 12, "bold"),
            cursor="hand2",
            relief=FLAT,
            padx=20,
            pady=10,
            state=DISABLED
        )
        self.stop_btn.pack(side=LEFT)
        
    def log_status(self, message, level="info"):
        """Add message to status log"""
        self.status_text.config(state=NORMAL)
        
        timestamp = time.strftime("%H:%M:%S")
        prefix = {"info": "ℹ️", "success": "✅", "error": "❌", "warning": "⚠️"}.get(level, "ℹ️")
        
        self.status_text.insert(END, f"[{timestamp}] {prefix} {message}\n")
        self.status_text.see(END)
        self.status_text.config(state=DISABLED)
        
    def browse_file(self):
        """Open file dialog to select CSV"""
        filename = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        
        if filename:
            self.csv_file = filename
            self.load_contacts()
            
    def load_contacts(self):
        """Load contacts from CSV file"""
        try:
            self.log_status(f"Loading CSV file: {os.path.basename(self.csv_file)}", "info")
            
            contacts = []
            with open(self.csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row.get('name') and row.get('phone') and row.get('message'):
                        contacts.append({
                            'name': row['name'].strip(),
                            'phone': row['phone'].strip().replace(' ', ''),
                            'message': row['message'].strip()
                        })
            
            if not contacts:
                raise ValueError("No valid contacts found in CSV")
            
            self.contacts = contacts
            
            # Update UI
            self.file_label.config(
                text=f"✓ {os.path.basename(self.csv_file)} ({len(contacts)} contacts)",
                fg=self.secondary_color
            )
            
            # Display contacts
            self.contacts_text.config(state=NORMAL)
            self.contacts_text.delete(1.0, END)
            for i, contact in enumerate(contacts, 1):
                self.contacts_text.insert(END, f"{i}. {contact['name']} - {contact['phone']}\n")
            self.contacts_text.config(state=DISABLED)
            
            # Enable start button
            self.start_btn.config(state=NORMAL)
            
            self.log_status(f"Loaded {len(contacts)} contacts successfully", "success")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load CSV:\n{str(e)}")
            self.log_status(f"Error loading CSV: {str(e)}", "error")
            
    def setup_driver(self):
        """Set up Chrome driver"""
        try:
            self.log_status("Setting up Chrome browser...", "info")
            
            chrome_options = Options()
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_experimental_option("prefs", {
                "profile.default_content_setting_values.notifications": 2
            })
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.maximize_window()
            self.wait = WebDriverWait(self.driver, 20)
            
            self.log_status("Browser setup complete", "success")
            return True
            
        except Exception as e:
            self.log_status(f"Browser setup failed: {str(e)}", "error")
            messagebox.showerror("Error", f"Failed to setup browser:\n{str(e)}")
            return False
            
    def open_whatsapp(self):
        """Open WhatsApp Web and wait for login"""
        try:
            self.log_status("Opening WhatsApp Web...", "info")
            self.driver.get("https://web.whatsapp.com")
            
            self.log_status("Please scan QR code (3 minutes timeout)...", "warning")
            messagebox.showinfo(
                "Scan QR Code",
                "Please scan the QR code in WhatsApp Web\n\nYou have 3 minutes to scan.\n\nClick OK after scanning."
            )
            
            # Wait for login
            login_wait = WebDriverWait(self.driver, 180)
            for attempt in range(36):
                try:
                    self.driver.find_element(By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]')
                    self.log_status("Logged in successfully!", "success")
                    time.sleep(3)
                    return True
                except:
                    if self.should_stop:
                        return False
                    time.sleep(5)
            
            self.log_status("QR code scan timeout", "error")
            return False
            
        except Exception as e:
            self.log_status(f"Error opening WhatsApp: {str(e)}", "error")
            return False
            
    def send_message(self, phone: str, message: str) -> bool:
        """Send a single message"""
        try:
            url = f"https://web.whatsapp.com/send?phone={phone}&text={message}"
            self.driver.get(url)
            time.sleep(5)
            
            # Wait for message input
            selectors = [
                '//div[@contenteditable="true"][@data-tab="10"]',
                '//div[@contenteditable="true"][@role="textbox"]',
            ]
            
            for selector in selectors:
                try:
                    self.wait.until(EC.presence_of_element_located((By.XPATH, selector)))
                    break
                except:
                    continue
            
            time.sleep(3)
            
            # Find and click send button
            try:
                send_btn = self.driver.find_element(By.XPATH, '//button[@data-testid="send"]')
            except:
                try:
                    send_btn = self.driver.find_element(By.XPATH, '//button[.//span[@data-icon="send"]]')
                except:
                    send_btn = self.driver.find_element(By.XPATH, '//button[contains(@aria-label, "Send")]')
            
            send_btn.click()
            time.sleep(2)
            return True
            
        except Exception as e:
            self.log_status(f"Send error: {str(e)[:100]}", "error")
            return False
            
    def send_messages_thread(self):
        """Send messages in a separate thread"""
        try:
            # Setup browser
            if not self.setup_driver():
                self.reset_ui()
                return
            
            # Open WhatsApp
            if not self.open_whatsapp():
                self.log_status("Failed to login to WhatsApp Web", "error")
                if self.driver:
                    self.driver.quit()
                self.reset_ui()
                return
            
            # Send messages
            total = len(self.contacts)
            sent = 0
            
            self.log_status(f"Starting to send {total} messages...", "info")
            
            for i, contact in enumerate(self.contacts, 1):
                if self.should_stop:
                    self.log_status("Sending stopped by user", "warning")
                    break
                
                name = contact['name']
                phone = contact['phone']
                message = contact['message'].replace('{name}', name)
                
                self.log_status(f"[{i}/{total}] Sending to {name} ({phone})", "info")
                
                if self.send_message(phone, message):
                    sent += 1
                    self.log_status(f"✓ Message sent to {name}", "success")
                else:
                    self.log_status(f"✗ Failed to send to {name}", "error")
                
                # Update progress
                progress = (i / total) * 100
                self.progress['value'] = progress
                self.progress_label.config(text=f"{i} / {total} messages sent")
                
                # Wait before next message
                if i < total and not self.should_stop:
                    delay = random.randint(MIN_DELAY, MAX_DELAY)
                    self.log_status(f"Waiting {delay} seconds...", "info")
                    time.sleep(delay)
            
            # Summary
            self.log_status(f"Complete! Sent: {sent}/{total}", "success")
            
            # Close browser
            if self.driver:
                self.driver.quit()
            
            messagebox.showinfo(
                "Complete",
                f"Sending complete!\n\nTotal: {total}\nSent: {sent}\nFailed: {total - sent}"
            )
            
        except Exception as e:
            self.log_status(f"Unexpected error: {str(e)}", "error")
            messagebox.showerror("Error", f"An error occurred:\n{str(e)}")
            
        finally:
            self.reset_ui()
            
    def start_sending(self):
        """Start sending messages"""
        if not self.contacts:
            messagebox.showwarning("No Contacts", "Please load a CSV file first")
            return
        
        # Confirm
        response = messagebox.askyesno(
            "Confirm",
            f"Send messages to {len(self.contacts)} contacts?\n\nThis will open Chrome browser and WhatsApp Web."
        )
        
        if not response:
            return
        
        # Update UI
        self.is_sending = True
        self.should_stop = False
        self.start_btn.config(state=DISABLED)
        self.stop_btn.config(state=NORMAL)
        self.progress['value'] = 0
        self.progress_label.config(text="0 / 0 messages sent")
        
        # Start in thread
        thread = threading.Thread(target=self.send_messages_thread, daemon=True)
        thread.start()
        
    def stop_sending(self):
        """Stop sending messages"""
        self.should_stop = True
        self.stop_btn.config(state=DISABLED)
        self.log_status("Stopping... please wait", "warning")
        
    def reset_ui(self):
        """Reset UI after sending"""
        self.is_sending = False
        self.should_stop = False
        self.start_btn.config(state=NORMAL)
        self.stop_btn.config(state=DISABLED)


def main():
    """Main function"""
    root = Tk()
    app = WhatsAppSenderGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
