#!/usr/bin/env python3
"""
Project Zomboid - Standalone Restart Timer
A lightweight program that runs server restart countdowns independently
"""

import tkinter as tk
from tkinter import ttk, messagebox
import socket
import struct
import time
import json
import subprocess
from pathlib import Path
from datetime import datetime


class RCONClient:
    """RCON client for communicating with Project Zomboid server"""
    
    SERVERDATA_AUTH = 3
    SERVERDATA_AUTH_RESPONSE = 2
    SERVERDATA_EXECCOMMAND = 2
    SERVERDATA_RESPONSE_VALUE = 0
    
    def __init__(self, host, port, password):
        self.host = host
        self.port = port
        self.password = password
        self.sock = None
        self.request_id = 0
        self.authenticated = False
        
    def connect(self):
        """Establish connection to RCON server and authenticate"""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(10)
            self.sock.connect((self.host, self.port))
            
            # Authenticate
            self.request_id += 1
            auth_id = self.request_id
            
            # CRITICAL: Body needs password + 2 null terminators (not 1!)
            auth_body = self.password.encode('utf-8')
            packet_data = auth_body + b'\x00\x00'  # Two null terminators
            packet_size = 4 + 4 + len(packet_data)  # id + type + data
            
            packet = struct.pack('<i', packet_size)   # size
            packet += struct.pack('<i', auth_id)      # id  
            packet += struct.pack('<i', self.SERVERDATA_AUTH)  # type
            packet += packet_data
            
            self.sock.sendall(packet)
            
            # Read first packet (might be empty SERVERDATA_RESPONSE_VALUE)
            size_data = self._recv_all(4)
            if not size_data:
                raise Exception("Auth failed - no response")
            
            response_size = struct.unpack('<i', size_data)[0]
            response_data = self._recv_all(response_size)
            
            if not response_data or len(response_data) < 8:
                raise Exception("Auth failed - incomplete response")
            
            first_packet_type = struct.unpack('<i', response_data[4:8])[0]
            
            # If first packet is empty response (type 0), read the auth response
            if first_packet_type == self.SERVERDATA_RESPONSE_VALUE:
                size_data = self._recv_all(4)
                if not size_data:
                    raise Exception("Auth failed - no auth response")
                
                response_size = struct.unpack('<i', size_data)[0]
                response_data = self._recv_all(response_size)
            
            if not response_data or len(response_data) < 8:
                raise Exception("Auth failed - incomplete auth response")
            
            response_id = struct.unpack('<i', response_data[0:4])[0]
            response_type = struct.unpack('<i', response_data[4:8])[0]
            
            if response_id == auth_id and response_type == self.SERVERDATA_AUTH_RESPONSE:
                self.authenticated = True
                return True
            else:
                raise Exception(f"Auth failed - wrong credentials (id={response_id}, type={response_type})")
                
        except Exception as e:
            self.disconnect()
            raise Exception(f"Connection failed: {e}")
        
        return False
    
    def _recv_all(self, n):
        """Helper to receive exactly n bytes"""
        data = b''
        while len(data) < n:
            packet = self.sock.recv(n - len(data))
            if not packet:
                return None
            data += packet
        return data
    
    def execute_command(self, command):
        """Execute a command on the server using existing connection"""
        if not self.sock or not self.authenticated:
            return None
        
        try:
            self.request_id += 1
            cmd_id = self.request_id
            
            cmd_body = command.encode('utf-8')
            packet_data = cmd_body + b'\x00\x00'
            packet_size = 4 + 4 + len(packet_data)
            
            packet = struct.pack('<i', packet_size)
            packet += struct.pack('<i', cmd_id)
            packet += struct.pack('<i', self.SERVERDATA_EXECCOMMAND)
            packet += packet_data
            
            self.sock.sendall(packet)
            
            # Read first response packet
            size_data = self._recv_all(4)
            if not size_data:
                return None
            
            response_size = struct.unpack('<i', size_data)[0]
            response_data = self._recv_all(response_size)
            
            if not response_data or len(response_data) < 8:
                return None
            
            response_id = struct.unpack('<i', response_data[0:4])[0]
            response_type = struct.unpack('<i', response_data[4:8])[0]
            
            # Extract response body (everything after id and type, minus null terminators)
            if len(response_data) > 8:
                body = response_data[8:-2].decode('utf-8', errors='ignore')
            else:
                body = ""
            
            # Read second packet if present (sometimes PZ sends empty response first)
            try:
                self.sock.settimeout(0.5)
                size_data2 = self._recv_all(4)
                if size_data2:
                    response_size2 = struct.unpack('<i', size_data2)[0]
                    response_data2 = self._recv_all(response_size2)
                    if response_data2 and len(response_data2) > 8:
                        body2 = response_data2[8:-2].decode('utf-8', errors='ignore')
                        if body2:
                            body = body2
            except socket.timeout:
                pass
            finally:
                self.sock.settimeout(10)
            
            return body if body else "Command executed"
            
        except Exception as e:
            return None
    
    def disconnect(self):
        """Close the connection"""
        if self.sock:
            try:
                self.sock.close()
            except (OSError, socket.error):
                pass
            self.sock = None
            self.authenticated = False


class RestartTimerApp(tk.Tk):
    """Standalone restart timer application"""
    
    def __init__(self):
        super().__init__()
        
        self.title("PZ Server Restart Timer")
        self.geometry("600x550")
        
        # RCON connection
        self.rcon = None
        self.host = tk.StringVar(value="localhost")
        self.port = tk.StringVar(value="16261")
        self.password = tk.StringVar()
        
        # Timer state
        self.countdown_active = False
        self.time_remaining = 0
        
        # Restart command
        self.restart_cmd = tk.StringVar()
        
        # Load saved config
        self.load_config()
        
        # Create UI
        self.create_ui()
        
        # Load any saved timer
        self.after(500, self.check_saved_timer)
    
    def create_ui(self):
        """Create the user interface"""
        
        # RCON Connection Frame
        conn_frame = ttk.LabelFrame(self, text="RCON Connection (for warnings)", padding=10)
        conn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(conn_frame, text="Host:").grid(row=0, column=0, sticky=tk.W, padx=5)
        ttk.Entry(conn_frame, textvariable=self.host, width=15).grid(row=0, column=1, padx=5)
        
        ttk.Label(conn_frame, text="Port:").grid(row=0, column=2, sticky=tk.W, padx=5)
        ttk.Entry(conn_frame, textvariable=self.port, width=8).grid(row=0, column=3, padx=5)
        
        ttk.Label(conn_frame, text="Password:").grid(row=0, column=4, sticky=tk.W, padx=5)
        ttk.Entry(conn_frame, textvariable=self.password, width=15, show="*").grid(row=0, column=5, padx=5)
        
        self.connect_btn = ttk.Button(conn_frame, text="Connect", command=self.connect_rcon)
        self.connect_btn.grid(row=0, column=6, padx=10)
        
        self.status_label = ttk.Label(conn_frame, text="Status: Disconnected", foreground="red")
        self.status_label.grid(row=0, column=7, padx=5)
        
        # Restart Command Frame
        cmd_frame = ttk.LabelFrame(self, text="Server Restart Command", padding=10)
        cmd_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(cmd_frame, text="Command:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(cmd_frame, textvariable=self.restart_cmd, width=50).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Label(cmd_frame, text="(e.g., systemctl restart zomboid)").pack(side=tk.LEFT, padx=5)
        
        # Timer Setup Frame
        setup_frame = ttk.LabelFrame(self, text="Restart Timer Setup", padding=10)
        setup_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Time selection
        time_frame = ttk.Frame(setup_frame)
        time_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(time_frame, text="Restart every:").pack(side=tk.LEFT, padx=5)
        self.minutes_var = tk.IntVar(value=180)
        ttk.Spinbox(time_frame, from_=5, to=480, textvariable=self.minutes_var, width=8).pack(side=tk.LEFT, padx=5)
        ttk.Label(time_frame, text="minutes").pack(side=tk.LEFT)
        
        # Presets
        preset_frame = ttk.Frame(setup_frame)
        preset_frame.pack(fill=tk.X, pady=5)
        ttk.Label(preset_frame, text="Quick:").pack(side=tk.LEFT, padx=5)
        ttk.Button(preset_frame, text="30m", command=lambda: self.minutes_var.set(30)).pack(side=tk.LEFT, padx=2)
        ttk.Button(preset_frame, text="1h", command=lambda: self.minutes_var.set(60)).pack(side=tk.LEFT, padx=2)
        ttk.Button(preset_frame, text="2h", command=lambda: self.minutes_var.set(120)).pack(side=tk.LEFT, padx=2)
        ttk.Button(preset_frame, text="3h", command=lambda: self.minutes_var.set(180)).pack(side=tk.LEFT, padx=2)
        ttk.Button(preset_frame, text="6h", command=lambda: self.minutes_var.set(360)).pack(side=tk.LEFT, padx=2)
        
        # Warnings
        ttk.Label(setup_frame, text="Warnings:", font=('TkDefaultFont', 9, 'bold')).pack(anchor=tk.W, pady=(10, 5))
        
        self.warn_30min = tk.BooleanVar(value=True)
        self.warn_15min = tk.BooleanVar(value=True)
        self.warn_10min = tk.BooleanVar(value=True)
        self.warn_5min = tk.BooleanVar(value=True)
        self.warn_1min = tk.BooleanVar(value=True)
        
        warn_frame = ttk.Frame(setup_frame)
        warn_frame.pack(fill=tk.X)
        
        ttk.Checkbutton(warn_frame, text="30min", variable=self.warn_30min).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(warn_frame, text="15min", variable=self.warn_15min).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(warn_frame, text="10min", variable=self.warn_10min).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(warn_frame, text="5min", variable=self.warn_5min).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(warn_frame, text="1min", variable=self.warn_1min).pack(side=tk.LEFT, padx=5)
        
        # Auto-save
        self.auto_save = tk.BooleanVar(value=True)
        ttk.Checkbutton(setup_frame, text="💾 Auto-save 1 minute before restart", 
                       variable=self.auto_save).pack(anchor=tk.W, pady=5)
        
        # Start button
        self.start_btn = ttk.Button(setup_frame, text="🔄 Start Repeating Restart Timer", 
                                    command=self.start_timer, style='Accent.TButton')
        self.start_btn.pack(pady=10)
        
        # Status display
        status_display_frame = ttk.LabelFrame(self, text="Timer Status", padding=10)
        status_display_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.timer_label = ttk.Label(status_display_frame, text="No active timer", 
                                     font=('TkDefaultFont', 14, 'bold'))
        self.timer_label.pack(pady=5)
        
        self.next_restart_label = ttk.Label(status_display_frame, text="")
        self.next_restart_label.pack()
        
        self.stop_btn = ttk.Button(status_display_frame, text="❌ Stop Timer", 
                                   command=self.stop_timer, state='disabled')
        self.stop_btn.pack(pady=5)
        
        # Bottom buttons
        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(bottom_frame, text="Save Settings", command=self.save_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="Exit", command=self.on_closing).pack(side=tk.RIGHT, padx=5)
    
    def connect_rcon(self):
        """Connect to RCON server"""
        if self.rcon and self.rcon.authenticated:
            self.rcon.disconnect()
            self.rcon = None
            self.status_label.config(text="Status: Disconnected", foreground="red")
            self.connect_btn.config(text="Connect")
            return
        
        try:
            self.rcon = RCONClient(self.host.get(), int(self.port.get()), self.password.get())
            if self.rcon.connect():
                self.status_label.config(text="Status: Connected", foreground="green")
                self.connect_btn.config(text="Disconnect")
                messagebox.showinfo("Success", "Connected to RCON server")
            else:
                raise Exception("Authentication failed")
        except Exception as e:
            messagebox.showerror("Connection Error", str(e))
            self.rcon = None
            self.status_label.config(text="Status: Failed", foreground="red")
    
    def start_timer(self):
        """Start the restart timer"""
        if self.countdown_active:
            messagebox.showwarning("Timer Active", "A timer is already running!")
            return
        
        minutes = self.minutes_var.get()
        if minutes < 5:
            messagebox.showwarning("Invalid Time", "Minimum time is 5 minutes")
            return
        
        self.countdown_active = True
        self.time_remaining = minutes * 60
        
        # Save timer state
        self.save_timer_state()
        
        # Update UI
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        
        # Start countdown
        self.warnings_sent = set()
        self.update_countdown()
    
    def update_countdown(self):
        """Update countdown timer"""
        if not self.countdown_active:
            return
        
        # Update display
        mins = self.time_remaining // 60
        secs = self.time_remaining % 60
        self.timer_label.config(text=f"⏰ Restart in {mins}:{secs:02d}")
        
        # Calculate next restart time
        next_time = datetime.now().timestamp() + self.time_remaining
        next_dt = datetime.fromtimestamp(next_time)
        self.next_restart_label.config(text=f"Next restart: {next_dt.strftime('%I:%M:%S %p')}")
        
        # Check for warnings
        if self.rcon and self.rcon.authenticated:
            try:
                if self.warn_30min.get() and self.time_remaining == 1800 and '30min' not in self.warnings_sent:
                    self.rcon.execute_command('servermsg "Server will restart in 30 minutes!"')
                    self.warnings_sent.add('30min')
                elif self.warn_15min.get() and self.time_remaining == 900 and '15min' not in self.warnings_sent:
                    self.rcon.execute_command('servermsg "Server will restart in 15 minutes!"')
                    self.warnings_sent.add('15min')
                elif self.warn_10min.get() and self.time_remaining == 600 and '10min' not in self.warnings_sent:
                    self.rcon.execute_command('servermsg "Server will restart in 10 minutes!"')
                    self.warnings_sent.add('10min')
                elif self.warn_5min.get() and self.time_remaining == 300 and '5min' not in self.warnings_sent:
                    self.rcon.execute_command('servermsg "Server will restart in 5 minutes!"')
                    self.warnings_sent.add('5min')
                elif self.warn_1min.get() and self.time_remaining == 60 and '1min' not in self.warnings_sent:
                    self.rcon.execute_command('servermsg "Server will restart in 1 minute!"')
                    if self.auto_save.get():
                        self.rcon.execute_command('save')
                    self.warnings_sent.add('1min')
                elif self.time_remaining == 10:
                    self.rcon.execute_command('servermsg "Server restarting in 10 seconds!"')
            except Exception:
                pass  # Continue even if warning fails
        
        # Check if time's up
        if self.time_remaining <= 0:
            self.execute_restart()
            return
        
        # Continue countdown
        self.time_remaining -= 1
        self.after(1000, self.update_countdown)
    
    def execute_restart(self):
        """Execute server restart"""
        # Final warning
        if self.rcon and self.rcon.authenticated:
            try:
                self.rcon.execute_command('servermsg "Server is restarting NOW!"')
                time.sleep(1)
            except Exception:
                pass
        
        # Execute restart command
        cmd = self.restart_cmd.get()
        if cmd:
            try:
                subprocess.Popen(cmd, shell=True)
                messagebox.showinfo("Restart", f"Server restart command executed:\n{cmd}")
            except Exception as e:
                messagebox.showerror("Restart Error", f"Failed to execute restart:\n{e}")
        
        # Schedule next restart
        minutes = self.minutes_var.get()
        self.time_remaining = minutes * 60
        self.warnings_sent = set()
        
        # Save new timer state
        self.save_timer_state()
        
        # Continue countdown
        self.after(5000, self.update_countdown)
    
    def stop_timer(self):
        """Stop the restart timer"""
        if messagebox.askyesno("Stop Timer", "Stop the restart timer?"):
            self.countdown_active = False
            self.clear_timer_state()
            
            # Broadcast cancellation
            if self.rcon and self.rcon.authenticated:
                try:
                    self.rcon.execute_command('servermsg "Automatic restarts have been CANCELLED."')
                except Exception:
                    pass
            
            # Update UI
            self.timer_label.config(text="No active timer")
            self.next_restart_label.config(text="")
            self.start_btn.config(state='normal')
            self.stop_btn.config(state='disabled')
    
    def save_config(self):
        """Save configuration"""
        config = {
            'host': self.host.get(),
            'port': self.port.get(),
            'password': self.password.get(),
            'restart_cmd': self.restart_cmd.get(),
            'minutes': self.minutes_var.get(),
            'warn_30min': self.warn_30min.get(),
            'warn_15min': self.warn_15min.get(),
            'warn_10min': self.warn_10min.get(),
            'warn_5min': self.warn_5min.get(),
            'warn_1min': self.warn_1min.get(),
            'auto_save': self.auto_save.get()
        }
        
        try:
            config_file = Path.home() / '.pz_restart_timer_config.json'
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            messagebox.showinfo("Saved", "Settings saved successfully")
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save settings:\n{e}")
    
    def load_config(self):
        """Load configuration"""
        try:
            config_file = Path.home() / '.pz_restart_timer_config.json'
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                self.host.set(config.get('host', 'localhost'))
                self.port.set(config.get('port', '16261'))
                self.password.set(config.get('password', ''))
                self.restart_cmd.set(config.get('restart_cmd', ''))
                self.minutes_var.set(config.get('minutes', 180))
                self.warn_30min.set(config.get('warn_30min', True))
                self.warn_15min.set(config.get('warn_15min', True))
                self.warn_10min.set(config.get('warn_10min', True))
                self.warn_5min.set(config.get('warn_5min', True))
                self.warn_1min.set(config.get('warn_1min', True))
                self.auto_save.set(config.get('auto_save', True))
        except Exception:
            pass
    
    def save_timer_state(self):
        """Save timer state for recovery"""
        try:
            state = {
                'start_time': time.time(),
                'time_remaining': self.time_remaining,
                'total_minutes': self.minutes_var.get(),
                'warnings': {
                    'warn_30min': self.warn_30min.get(),
                    'warn_15min': self.warn_15min.get(),
                    'warn_10min': self.warn_10min.get(),
                    'warn_5min': self.warn_5min.get(),
                    'warn_1min': self.warn_1min.get(),
                    'auto_save': self.auto_save.get()
                }
            }
            state_file = Path.home() / '.pz_restart_timer_state.json'
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception:
            pass
    
    def clear_timer_state(self):
        """Clear saved timer state"""
        try:
            state_file = Path.home() / '.pz_restart_timer_state.json'
            if state_file.exists():
                state_file.unlink()
        except Exception:
            pass
    
    def check_saved_timer(self):
        """Check for saved timer and resume"""
        try:
            state_file = Path.home() / '.pz_restart_timer_state.json'
            if not state_file.exists():
                return
            
            with open(state_file, 'r') as f:
                state = json.load(f)
            
            start_time = state.get('start_time')
            saved_remaining = state.get('time_remaining')
            total_minutes = state.get('total_minutes')
            warnings = state.get('warnings', {})
            
            if not all([start_time, saved_remaining, total_minutes]):
                self.clear_timer_state()
                return
            
            # Calculate actual remaining time
            elapsed = int(time.time() - start_time)
            actual_remaining = saved_remaining - elapsed
            
            if actual_remaining <= 0:
                self.clear_timer_state()
                return
            
            # Ask to resume
            mins = actual_remaining // 60
            secs = actual_remaining % 60
            
            response = messagebox.askyesno(
                "Resume Timer?",
                f"A restart timer was active:\n\n"
                f"Time remaining: {mins}m {secs}s\n"
                f"Repeating every: {total_minutes} minutes\n\n"
                f"Resume the timer?",
                icon='question'
            )
            
            if response:
                # Restore state
                self.time_remaining = actual_remaining
                self.minutes_var.set(total_minutes)
                self.warn_30min.set(warnings.get('warn_30min', True))
                self.warn_15min.set(warnings.get('warn_15min', True))
                self.warn_10min.set(warnings.get('warn_10min', True))
                self.warn_5min.set(warnings.get('warn_5min', True))
                self.warn_1min.set(warnings.get('warn_1min', True))
                self.auto_save.set(warnings.get('auto_save', True))
                
                # Start timer
                self.countdown_active = True
                self.start_btn.config(state='disabled')
                self.stop_btn.config(state='normal')
                self.warnings_sent = set()
                self.update_countdown()
            else:
                self.clear_timer_state()
        
        except Exception:
            self.clear_timer_state()
    
    def on_closing(self):
        """Handle window close"""
        if self.countdown_active:
            response = messagebox.askyesno(
                "Timer Active",
                "A restart timer is currently running.\n\n"
                "The timer will continue in the background when you close this window.\n\n"
                "Exit anyway?",
                icon='warning'
            )
            if not response:
                return
        
        if self.rcon:
            self.rcon.disconnect()
        
        self.destroy()


if __name__ == "__main__":
    app = RestartTimerApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
