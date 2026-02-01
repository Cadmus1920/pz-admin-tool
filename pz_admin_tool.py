"""
Project Zomboid Server Administration Tool
A comprehensive GUI tool for managing Project Zomboid servers
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, font
import socket
import struct
import threading
import time
import sqlite3
import os
import json
import re
import subprocess
import webbrowser
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
            # DEBUG: Print what we're using
            print(f"DEBUG: Connecting to {self.host}:{self.port}")
            print(f"DEBUG: Password = {repr(self.password)}")
            print(f"DEBUG: Password length = {len(self.password)}")
            print(f"DEBUG: Password hex = {self.password.encode('utf-8').hex()}")
            
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
            
            print(f"DEBUG: Sending auth packet: {packet.hex()}")
            
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
                
                if not response_data or len(response_data) < 4:
                    raise Exception("Auth failed - incomplete auth response")
            
            # Check auth result
            response_id = struct.unpack('<i', response_data[:4])[0]
            if response_id == -1:
                raise Exception("Authentication failed - wrong password")
            
            self.authenticated = True
            return True
            
        except socket.timeout:
            raise Exception("Connection timed out - check host and port")
        except ConnectionRefusedError:
            raise Exception("Connection refused - is RCON enabled and server running?")
        except Exception as e:
            if self.sock:
                self.sock.close()
                self.sock = None
            raise
    
    def disconnect(self):
        """Close RCON connection"""
        if self.sock:
            try:
                self.sock.close()
            except (OSError, socket.error):
                pass  # Socket already closed, ignore
            self.sock = None
            self.authenticated = False
    
    def execute_command(self, command):
        """Execute a command on the server using existing connection"""
        if not self.sock or not self.authenticated:
            raise Exception("Not connected to server")
        
        try:
            # Send command
            self.request_id += 1
            cmd_id = self.request_id
            
            # Build command packet with 2 null terminators
            cmd_body = command.encode('utf-8')
            packet_data = cmd_body + b'\x00\x00'
            packet_size = 4 + 4 + len(packet_data)
            
            packet = struct.pack('<i', packet_size)
            packet += struct.pack('<i', cmd_id)
            packet += struct.pack('<i', self.SERVERDATA_EXECCOMMAND)
            packet += packet_data
            
            self.sock.sendall(packet)
            
            # Read response
            response_text = ""
            
            size_data = self._recv_all(4)
            if size_data:
                response_size = struct.unpack('<i', size_data)[0]
                response_data = self._recv_all(response_size)
                
                if response_data and len(response_data) >= 8:
                    response_text = response_data[8:].rstrip(b'\x00').decode('utf-8', errors='ignore')
            
            return response_text
            
        except (BrokenPipeError, ConnectionResetError):
            self.authenticated = False
            raise Exception("Connection lost - please reconnect")
        except socket.timeout:
            raise Exception("Command timed out")
        except Exception as e:
            raise Exception(f"Command failed: {str(e)}")
    
    def _recv_all(self, n):
        """Receive exactly n bytes from socket"""
        data = b''
        while len(data) < n:
            try:
                chunk = self.sock.recv(n - len(data))
                if not chunk:
                    return None
                data += chunk
            except socket.error:
                return None
        return data


class PZServerAdmin(tk.Tk):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        self.title("Project Zomboid Server Administration Tool")
        self.geometry("1000x700")
        
        self.rcon = None
        self.auto_refresh = False
        self.server_path = tk.StringVar()
        
        # Restart countdown tracking
        self.restart_countdown_active = False
        self.restart_time_remaining = 0
        
        # Theme and appearance settings
        self.current_theme = tk.StringVar(value="light")
        self.font_size = tk.IntVar(value=9)
        
        # Load appearance preferences
        self.load_appearance_settings()
        
        # Create menu bar
        self.create_menu()
        
        # Apply theme
        self.apply_theme()
        
        self.create_widgets()
        self.load_config()
    
    def create_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        
        # Theme submenu
        theme_menu = tk.Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label="Theme", menu=theme_menu)
        theme_menu.add_radiobutton(label="Light Theme", variable=self.current_theme, 
                                   value="light", command=self.apply_theme)
        theme_menu.add_radiobutton(label="Dark Theme", variable=self.current_theme, 
                                   value="dark", command=self.apply_theme)
        
        view_menu.add_separator()
        
        # Font size submenu
        font_menu = tk.Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label="Font Size", menu=font_menu)
        font_menu.add_radiobutton(label="Small (8pt)", variable=self.font_size, 
                                 value=8, command=self.apply_font_size)
        font_menu.add_radiobutton(label="Normal (9pt)", variable=self.font_size, 
                                 value=9, command=self.apply_font_size)
        font_menu.add_radiobutton(label="Medium (10pt)", variable=self.font_size, 
                                 value=10, command=self.apply_font_size)
        font_menu.add_radiobutton(label="Large (11pt)", variable=self.font_size, 
                                 value=11, command=self.apply_font_size)
        font_menu.add_radiobutton(label="Extra Large (12pt)", variable=self.font_size, 
                                 value=12, command=self.apply_font_size)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
    
    def apply_theme(self):
        """Apply the selected theme"""
        theme = self.current_theme.get()
        
        style = ttk.Style()
        
        if theme == "dark":
            # Dark theme colors - consistent palette
            bg_main = "#2b2b2b"      # Main background
            bg_widget = "#353535"     # Widget background (slightly lighter)
            bg_input = "#404040"      # Input fields
            fg_main = "#e0e0e0"       # Main text
            fg_bright = "#ffffff"     # Bright text
            border = "#1a1a1a"        # Borders (darker)
            select_bg = "#505050"     # Selection background
            
            # Use 'clam' theme as base - it handles colors better
            try:
                style.theme_use('clam')
            except tk.TclError:
                style.theme_use('default')  # Fallback if clam not available
            
            # Configure all ttk styles consistently
            style.configure(".", background=bg_main, foreground=fg_main,
                          fieldbackground=bg_input, bordercolor=border,
                          darkcolor=bg_main, lightcolor=bg_widget,
                          troughcolor=bg_widget, selectbackground=select_bg,
                          selectforeground=fg_bright)
            
            style.configure("TFrame", background=bg_main)
            style.configure("TLabel", background=bg_main, foreground=fg_main)
            style.configure("TLabelframe", background=bg_main, foreground=fg_main,
                          bordercolor=border, darkcolor=bg_main, lightcolor=bg_widget)
            style.configure("TLabelframe.Label", background=bg_main, foreground=fg_main)
            
            style.configure("TButton", background=bg_widget, foreground=fg_main,
                          bordercolor=border, darkcolor=bg_main, lightcolor=bg_widget)
            style.map("TButton",
                     background=[('active', select_bg), ('pressed', border)],
                     foreground=[('active', fg_bright)])
            
            style.configure("TCheckbutton", background=bg_main, foreground=fg_main)
            style.map("TCheckbutton",
                     background=[('active', bg_main)],
                     foreground=[('active', fg_bright)])
            
            style.configure("TRadiobutton", background=bg_main, foreground=fg_main)
            style.map("TRadiobutton",
                     background=[('active', bg_main)],
                     foreground=[('active', fg_bright)])
            
            style.configure("TNotebook", background=bg_main, bordercolor=border,
                          darkcolor=bg_main, lightcolor=bg_widget)
            style.configure("TNotebook.Tab", background=bg_widget, foreground=fg_main,
                          bordercolor=border, darkcolor=bg_main, lightcolor=bg_widget)
            style.map("TNotebook.Tab",
                     background=[("selected", bg_main), ('active', select_bg)],
                     foreground=[("selected", fg_bright), ('active', fg_bright)],
                     expand=[("selected", [1, 1, 1, 0])])
            
            # Entry and Spinbox
            style.configure("TEntry", fieldbackground=bg_input, foreground=fg_bright,
                          insertcolor=fg_bright, bordercolor=border,
                          darkcolor=bg_main, lightcolor=bg_widget)
            style.map("TEntry",
                     fieldbackground=[('focus', bg_input)],
                     foreground=[('focus', fg_bright)])
            
            style.configure("TSpinbox", fieldbackground=bg_input, foreground=fg_bright,
                          insertcolor=fg_bright, bordercolor=border,
                          darkcolor=bg_main, lightcolor=bg_widget,
                          arrowcolor=fg_main)
            style.map("TSpinbox",
                     fieldbackground=[('focus', bg_input)],
                     foreground=[('focus', fg_bright)])
            
            # Combobox
            style.configure("TCombobox", fieldbackground=bg_input, foreground=fg_bright,
                          selectbackground=select_bg, selectforeground=fg_bright,
                          bordercolor=border, darkcolor=bg_main, lightcolor=bg_widget,
                          arrowcolor=fg_main)
            style.map("TCombobox",
                     fieldbackground=[("readonly", bg_input), ('focus', bg_input)],
                     foreground=[("readonly", fg_bright), ('focus', fg_bright)],
                     selectbackground=[('focus', select_bg)])
            
            # Configure the dropdown list colors (this affects the popdown menu)
            self.option_add('*TCombobox*Listbox.background', bg_input)
            self.option_add('*TCombobox*Listbox.foreground', fg_bright)
            self.option_add('*TCombobox*Listbox.selectBackground', select_bg)
            self.option_add('*TCombobox*Listbox.selectForeground', fg_bright)
            
            # Treeview
            style.configure("Treeview", background=bg_input, foreground=fg_bright,
                          fieldbackground=bg_input, bordercolor=border)
            style.configure("Treeview.Heading", background=bg_widget, foreground=fg_main,
                          bordercolor=border, relief="flat")
            style.map("Treeview",
                     background=[("selected", select_bg)],
                     foreground=[("selected", fg_bright)])
            style.map("Treeview.Heading",
                     background=[('active', select_bg)],
                     foreground=[('active', fg_bright)])
            
            # Scale (for sliders)
            style.configure("TScale", background=bg_main, troughcolor=bg_widget,
                          bordercolor=border, darkcolor=bg_main, lightcolor=bg_widget)
            
            # Configure main window
            self.configure(bg=bg_main)
            
            # Update ScrolledText widgets
            if hasattr(self, 'info_text'):
                self.info_text.configure(bg=bg_input, fg=fg_bright, 
                                        insertbackground=fg_bright, selectbackground=select_bg,
                                        selectforeground=fg_bright)
            if hasattr(self, 'command_output'):
                self.command_output.configure(bg=bg_input, fg=fg_bright,
                                             insertbackground=fg_bright, selectbackground=select_bg,
                                             selectforeground=fg_bright)
            if hasattr(self, 'logs_text'):
                self.logs_text.configure(bg=bg_input, fg=fg_bright,
                                        insertbackground=fg_bright, selectbackground=select_bg,
                                        selectforeground=fg_bright)
            
        else:  # light theme
            # Light theme - clean and consistent
            bg_main = "#f5f5f5"
            bg_widget = "#ffffff"
            fg_main = "#000000"
            border = "#d0d0d0"
            select_bg = "#0078d7"
            select_fg = "#ffffff"
            
            try:
                style.theme_use('clam')
            except tk.TclError:
                style.theme_use('default')  # Fallback if clam not available
            
            # Reset to light defaults
            style.configure(".", background=bg_main, foreground=fg_main,
                          fieldbackground=bg_widget, bordercolor=border,
                          selectbackground=select_bg, selectforeground=select_fg)
            
            style.configure("TFrame", background=bg_main)
            style.configure("TLabel", background=bg_main, foreground=fg_main)
            style.configure("TLabelframe", background=bg_main, foreground=fg_main,
                          bordercolor=border)
            style.configure("TLabelframe.Label", background=bg_main, foreground=fg_main)
            
            style.configure("TButton", background=bg_widget, foreground=fg_main,
                          bordercolor=border)
            style.map("TButton",
                     background=[('active', '#e5e5e5'), ('pressed', '#d0d0d0')])
            
            style.configure("TCheckbutton", background=bg_main, foreground=fg_main)
            style.configure("TRadiobutton", background=bg_main, foreground=fg_main)
            
            style.configure("TNotebook", background=bg_main, bordercolor=border)
            style.configure("TNotebook.Tab", background="#e0e0e0", foreground=fg_main,
                          bordercolor=border)
            style.map("TNotebook.Tab",
                     background=[("selected", bg_main), ('active', '#f0f0f0')],
                     expand=[("selected", [1, 1, 1, 0])])
            
            # Entry and Spinbox
            style.configure("TEntry", fieldbackground=bg_widget, foreground=fg_main,
                          insertcolor=fg_main, bordercolor=border)
            style.configure("TSpinbox", fieldbackground=bg_widget, foreground=fg_main,
                          insertcolor=fg_main, bordercolor=border)
            
            # Combobox
            style.configure("TCombobox", fieldbackground=bg_widget, foreground=fg_main,
                          selectbackground=select_bg, selectforeground=select_fg,
                          bordercolor=border)
            style.map("TCombobox",
                     fieldbackground=[("readonly", bg_widget)])
            
            # Configure the dropdown list colors
            self.option_add('*TCombobox*Listbox.background', bg_widget)
            self.option_add('*TCombobox*Listbox.foreground', fg_main)
            self.option_add('*TCombobox*Listbox.selectBackground', select_bg)
            self.option_add('*TCombobox*Listbox.selectForeground', select_fg)
            
            # Treeview
            style.configure("Treeview", background=bg_widget, foreground=fg_main,
                          fieldbackground=bg_widget, bordercolor=border)
            style.configure("Treeview.Heading", background="#e0e0e0", foreground=fg_main,
                          bordercolor=border, relief="flat")
            style.map("Treeview",
                     background=[("selected", select_bg)],
                     foreground=[("selected", select_fg)])
            
            # Scale
            style.configure("TScale", background=bg_main, troughcolor="#e0e0e0",
                          bordercolor=border)
            
            self.configure(bg=bg_main)
            
            # Update ScrolledText widgets
            if hasattr(self, 'info_text'):
                self.info_text.configure(bg=bg_widget, fg=fg_main, 
                                        insertbackground=fg_main, selectbackground=select_bg,
                                        selectforeground=select_fg)
            if hasattr(self, 'command_output'):
                self.command_output.configure(bg=bg_widget, fg=fg_main,
                                             insertbackground=fg_main, selectbackground=select_bg,
                                             selectforeground=select_fg)
            if hasattr(self, 'logs_text'):
                self.logs_text.configure(bg=bg_widget, fg=fg_main,
                                        insertbackground=fg_main, selectbackground=select_bg,
                                        selectforeground=select_fg)
        
        # Save preference
        self.save_appearance_settings()
    
    def apply_font_size(self):
        """Apply the selected font size"""
        size = self.font_size.get()
        
        # Update default font
        default_font = font.nametofont("TkDefaultFont")
        default_font.configure(size=size)
        
        text_font = font.nametofont("TkTextFont")
        text_font.configure(size=size)
        
        # Save preference
        self.save_appearance_settings()
    
    def save_appearance_settings(self):
        """Save appearance settings to file"""
        try:
            config = {
                'theme': self.current_theme.get(),
                'font_size': self.font_size.get()
            }
            config_file = Path.home() / '.pz_admin_tool_appearance.json'
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except (IOError, OSError) as e:
            pass  # Silently fail if can't save preferences
    
    def load_appearance_settings(self):
        """Load appearance settings from file"""
        try:
            config_file = Path.home() / '.pz_admin_tool_appearance.json'
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    self.current_theme.set(config.get('theme', 'light'))
                    self.font_size.set(config.get('font_size', 9))
        except (IOError, OSError, json.JSONDecodeError):
            pass  # Use defaults if can't load preferences
    
    def show_about(self):
        """Show about dialog"""
        about_text = """Project Zomboid Server Administration Tool
Version 1.3.0

A comprehensive GUI tool for managing Project Zomboid dedicated servers.

Features:
• Player Management
• Server Settings Editor
• Mod Manager
• Ban List Manager
• Task Scheduler
• Server Control
• Live Log Streaming
• And more!

Created with ❤️ for the PZ community
"""
        messagebox.showinfo("About", about_text)
    
    def apply_dialog_theme(self, dialog):
        """Apply current theme to a dialog window"""
        theme = self.current_theme.get()
        if theme == "dark":
            dialog.configure(bg="#2b2b2b")
        else:
            dialog.configure(bg="#f5f5f5")
    
    def get_text_colors(self):
        """Get text widget colors based on theme"""
        theme = self.current_theme.get()
        if theme == "dark":
            return {
                'bg': "#404040",
                'fg': "#ffffff",
                'insertbackground': "#ffffff",
                'selectbackground': "#505050",
                'selectforeground': "#ffffff"
            }
        else:
            return {
                'bg': "#ffffff",
                'fg': "#000000",
                'insertbackground': "#000000",
                'selectbackground': "#0078d7",
                'selectforeground': "#ffffff"
            }
        
    def create_widgets(self):
        """Create the GUI widgets"""
        
        # Connection Frame
        conn_frame = ttk.LabelFrame(self, text="Server Connection", padding=10)
        conn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(conn_frame, text="Host:").grid(row=0, column=0, sticky=tk.W)
        self.host_entry = ttk.Entry(conn_frame, width=20)
        self.host_entry.grid(row=0, column=1, padx=5)
        self.host_entry.insert(0, "localhost")
        
        ttk.Label(conn_frame, text="Port:").grid(row=0, column=2, sticky=tk.W, padx=(10, 0))
        self.port_entry = ttk.Entry(conn_frame, width=10)
        self.port_entry.grid(row=0, column=3, padx=5)
        self.port_entry.insert(0, "16261")
        
        ttk.Label(conn_frame, text="Password:").grid(row=0, column=4, sticky=tk.W, padx=(10, 0))
        self.password_entry = ttk.Entry(conn_frame, width=20, show="*")
        self.password_entry.grid(row=0, column=5, padx=5)
        
        # Show password checkbox
        self.show_password_var = tk.BooleanVar()
        ttk.Checkbutton(conn_frame, text="Show", variable=self.show_password_var,
                       command=self.toggle_password_visibility).grid(row=0, column=6, padx=(0, 5))
        
        self.connect_btn = ttk.Button(conn_frame, text="Connect", command=self.connect_to_server)
        self.connect_btn.grid(row=0, column=7, padx=10)
        
        self.status_label = ttk.Label(conn_frame, text="Status: Disconnected", foreground="red")
        self.status_label.grid(row=0, column=8, padx=10)
        
        # Restart timer indicator (initially hidden)
        self.restart_indicator = ttk.Label(conn_frame, text="", foreground="orange", font=('TkDefaultFont', 9, 'bold'))
        self.restart_indicator.grid(row=0, column=9, padx=10)
        
        # Server Path Frame
        path_frame = ttk.LabelFrame(self, text="Server Files (Optional - for Mods/Logs viewing)", padding=10)
        path_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(path_frame, text="Server Path:").grid(row=0, column=0, sticky=tk.W)
        self.path_entry = ttk.Entry(path_frame, textvariable=self.server_path, width=50)
        self.path_entry.grid(row=0, column=1, padx=5)
        ttk.Button(path_frame, text="Browse", command=self.browse_path).grid(row=0, column=2, padx=5)
        ttk.Button(path_frame, text="Auto-Detect", command=self.auto_detect_path).grid(row=0, column=3, padx=5)
        
        # Help text for server path
        help_text = "Tip: Use the steamcmd install path (e.g., /home/pzserver/.steam/steamapps/common/Project Zomboid Dedicated Server)"
        ttk.Label(path_frame, text=help_text, font=('TkDefaultFont', 8), foreground='gray').grid(row=1, column=0, columnspan=4, sticky=tk.W, pady=(5, 0))
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Players Tab
        self.players_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.players_frame, text="Players")
        self.create_players_tab()
        
        # Server Info Tab
        self.info_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.info_frame, text="Server Info")
        self.create_info_tab()
        
        # Commands Tab
        self.commands_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.commands_frame, text="Commands")
        self.create_commands_tab()
        
        # Mods Tab
        self.mods_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.mods_frame, text="Mods")
        self.create_mods_tab()
        
        # Logs Tab
        self.logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.logs_frame, text="Logs")
        self.create_logs_tab()
        
        # Ban List Tab
        self.banlist_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.banlist_frame, text="Ban List")
        self.create_banlist_tab()
        
        # Scheduler Tab
        self.scheduler_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.scheduler_frame, text="Scheduler")
        self.create_scheduler_tab()
        
        # Bottom buttons
        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.auto_refresh_var = tk.BooleanVar()
        ttk.Checkbutton(bottom_frame, text="Auto Refresh (30s)", 
                       variable=self.auto_refresh_var,
                       command=self.toggle_auto_refresh).pack(side=tk.LEFT)
        
        ttk.Button(bottom_frame, text="Refresh All", command=self.refresh_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="Save Config", command=self.save_config).pack(side=tk.RIGHT, padx=5)
        
    def create_players_tab(self):
        """Create the players management tab"""
        # Players list
        list_frame = ttk.Frame(self.players_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Treeview for players
        columns = ('Username', 'Access Level', 'Status')
        self.players_tree = ttk.Treeview(list_frame, columns=columns, show='tree headings')
        self.players_tree.heading('#0', text='ID')
        self.players_tree.heading('Username', text='Username')
        self.players_tree.heading('Access Level', text='Access Level')
        self.players_tree.heading('Status', text='Status')
        
        self.players_tree.column('#0', width=50)
        self.players_tree.column('Username', width=200)
        self.players_tree.column('Access Level', width=150)
        self.players_tree.column('Status', width=100)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.players_tree.yview)
        self.players_tree.configure(yscrollcommand=scrollbar.set)
        
        self.players_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Player actions
        actions_frame = ttk.LabelFrame(self.players_frame, text="Player Actions", padding=10)
        actions_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(actions_frame, text="Username:").grid(row=0, column=0, sticky=tk.W)
        self.player_username_entry = ttk.Entry(actions_frame, width=20)
        self.player_username_entry.grid(row=0, column=1, padx=5)
        
        # Row 0: Basic actions
        ttk.Button(actions_frame, text="Kick", command=lambda: self.player_action('kick')).grid(row=0, column=2, padx=5)
        ttk.Button(actions_frame, text="Ban", command=lambda: self.player_action('ban')).grid(row=0, column=3, padx=5)
        ttk.Button(actions_frame, text="Teleport", command=lambda: self.player_action('teleport')).grid(row=0, column=4, padx=5)
        
        # Row 1: Admin controls
        ttk.Button(actions_frame, text="Grant Admin", command=lambda: self.player_action('admin'), 
                  ).grid(row=1, column=2, padx=5, pady=5)
        ttk.Button(actions_frame, text="Remove Admin", command=lambda: self.player_action('removeadmin'),
                  ).grid(row=1, column=3, padx=5, pady=5)
        ttk.Button(actions_frame, text="Toggle God Mode", command=lambda: self.player_action('godmode'),
                  ).grid(row=1, column=4, padx=5, pady=5)
        
        ttk.Button(actions_frame, text="Refresh Players", command=self.refresh_players).grid(row=2, column=0, columnspan=6, pady=10)
        
    def create_info_tab(self):
        """Create the server info tab"""
        info_text_frame = ttk.Frame(self.info_frame)
        info_text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        colors = self.get_text_colors()
        self.info_text = scrolledtext.ScrolledText(info_text_frame, wrap=tk.WORD, height=20, **colors)
        self.info_text.pack(fill=tk.BOTH, expand=True)
        
        # Server Control buttons
        control_frame = ttk.LabelFrame(self.info_frame, text="Server Control", padding=5)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(control_frame, text="Start Server", command=self.start_server).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Stop Server", command=self.stop_server).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Restart Server", command=self.restart_server).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Scheduled Restart", command=self.open_restart_timer).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Check Status", command=self.check_server_status).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Configure Commands", command=self.configure_server_control).pack(side=tk.LEFT, padx=5)
        
        # Info buttons
        btn_frame = ttk.Frame(self.info_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text="Get Server Info", command=self.get_server_info).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Get Server Stats", command=self.get_server_stats).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Edit Server Settings", command=self.open_settings_editor).pack(side=tk.LEFT, padx=5)
        
    def create_commands_tab(self):
        """Create the commands tab"""
        # Quick commands
        quick_frame = ttk.LabelFrame(self.commands_frame, text="Quick Commands", padding=10)
        quick_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(quick_frame, text="Save Server", command=lambda: self.quick_command('save')).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(quick_frame, text="Help", command=lambda: self.quick_command('help')).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(quick_frame, text="Show Players", command=lambda: self.quick_command('players')).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(quick_frame, text="Server Message", command=self.send_server_message).grid(row=0, column=3, padx=5, pady=5)
        
        # Custom command
        custom_frame = ttk.LabelFrame(self.commands_frame, text="Custom Command", padding=10)
        custom_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(custom_frame, text="Command:").pack(side=tk.LEFT, padx=5)
        self.command_entry = ttk.Entry(custom_frame, width=40)
        self.command_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(custom_frame, text="Execute", command=self.execute_custom_command).pack(side=tk.LEFT, padx=5)
        
        # Command output
        output_frame = ttk.LabelFrame(self.commands_frame, text="Command Output", padding=10)
        output_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        colors = self.get_text_colors()
        self.command_output = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, height=15, **colors)
        self.command_output.pack(fill=tk.BOTH, expand=True)
        
    def create_mods_tab(self):
        """Create the mods information tab"""
        # Create a paned window to show mods and workshop IDs side by side
        paned = ttk.PanedWindow(self.mods_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - Mod Names
        left_frame = ttk.LabelFrame(paned, text="Installed Mods (by Mod ID)", padding=5)
        paned.add(left_frame, weight=1)
        
        self.mods_tree = ttk.Treeview(left_frame, columns=('Name',), show='tree headings')
        self.mods_tree.heading('#0', text='#')
        self.mods_tree.heading('Name', text='Mod ID')
        self.mods_tree.column('#0', width=50)
        self.mods_tree.column('Name', width=300)
        
        scrollbar1 = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.mods_tree.yview)
        self.mods_tree.configure(yscrollcommand=scrollbar1.set)
        self.mods_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar1.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Right panel - Workshop IDs
        right_frame = ttk.LabelFrame(paned, text="Workshop Items (Steam IDs)", padding=5)
        paned.add(right_frame, weight=1)
        
        self.workshop_tree = ttk.Treeview(right_frame, columns=('ID',), show='tree headings')
        self.workshop_tree.heading('#0', text='#')
        self.workshop_tree.heading('ID', text='Workshop ID')
        self.workshop_tree.column('#0', width=50)
        self.workshop_tree.column('ID', width=150)
        
        # Bind double-click to open in browser
        self.workshop_tree.bind('<Double-Button-1>', lambda e: self.open_workshop_in_browser())
        
        scrollbar2 = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.workshop_tree.yview)
        self.workshop_tree.configure(yscrollcommand=scrollbar2.set)
        self.workshop_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar2.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Buttons
        btn_frame = ttk.Frame(self.mods_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text="Refresh Mods", command=self.refresh_mods).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Edit Mods", command=self.open_mod_editor_from_mods_tab).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Open Selected Workshop ID in Browser", 
                  command=self.open_workshop_in_browser).pack(side=tk.LEFT, padx=5)
        ttk.Label(btn_frame, text="Note: Mod IDs and Workshop IDs are separate lists and may not align 1:1", 
                 font=('TkDefaultFont', 8), foreground='gray').pack(side=tk.LEFT, padx=10)
        
    def create_logs_tab(self):
        """Create the logs viewer tab"""
        log_frame = ttk.Frame(self.logs_frame)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        colors = self.get_text_colors()
        self.logs_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, **colors)
        self.logs_text.pack(fill=tk.BOTH, expand=True)
        
        btn_frame = ttk.Frame(self.logs_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text="Refresh Logs", command=self.refresh_logs).pack(side=tk.LEFT, padx=5)
        ttk.Label(btn_frame, text="Lines:").pack(side=tk.LEFT, padx=5)
        self.log_lines_entry = ttk.Entry(btn_frame, width=10)
        self.log_lines_entry.insert(0, "100")
        self.log_lines_entry.pack(side=tk.LEFT, padx=5)
        
        # Live streaming toggle
        self.live_logs_var = tk.BooleanVar()
        ttk.Checkbutton(btn_frame, text="Live Stream", 
                       variable=self.live_logs_var,
                       command=self.toggle_live_logs).pack(side=tk.LEFT, padx=20)
        
        # Initialize live log tracking
        self.live_logs_active = False
        self.log_file_position = 0
        self.current_log_file = None
    
    def create_banlist_tab(self):
        """Create the ban list manager tab"""
        # Ban list display
        list_frame = ttk.Frame(self.banlist_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Treeview for banned users
        columns = ('Username', 'IP', 'Reason', 'Date')
        self.banlist_tree = ttk.Treeview(list_frame, columns=columns, show='tree headings')
        self.banlist_tree.heading('#0', text='#')
        self.banlist_tree.heading('Username', text='Username')
        self.banlist_tree.heading('IP', text='IP Address')
        self.banlist_tree.heading('Reason', text='Ban Reason')
        self.banlist_tree.heading('Date', text='Date')
        
        self.banlist_tree.column('#0', width=50)
        self.banlist_tree.column('Username', width=150)
        self.banlist_tree.column('IP', width=120)
        self.banlist_tree.column('Reason', width=250)
        self.banlist_tree.column('Date', width=150)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.banlist_tree.yview)
        self.banlist_tree.configure(yscrollcommand=scrollbar.set)
        
        self.banlist_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Actions frame
        actions_frame = ttk.LabelFrame(self.banlist_frame, text="Ban List Actions", padding=10)
        actions_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(actions_frame, text="Refresh Ban List", command=self.refresh_banlist).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions_frame, text="Unban Selected", command=self.unban_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions_frame, text="Clear All Bans", command=self.clear_all_bans).pack(side=tk.LEFT, padx=5)
        
        # Manual unban
        ttk.Label(actions_frame, text="Username:").pack(side=tk.LEFT, padx=(20, 5))
        self.unban_username_entry = ttk.Entry(actions_frame, width=20)
        self.unban_username_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(actions_frame, text="Unban", command=self.unban_manual).pack(side=tk.LEFT, padx=5)
    
    def create_scheduler_tab(self):
        """Create the scheduler tab for automated tasks"""
        # Scheduled tasks list
        list_frame = ttk.Frame(self.scheduler_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Treeview for scheduled tasks
        columns = ('Type', 'Interval', 'Command/Message', 'Status')
        self.scheduler_tree = ttk.Treeview(list_frame, columns=columns, show='tree headings')
        self.scheduler_tree.heading('#0', text='#')
        self.scheduler_tree.heading('Type', text='Type')
        self.scheduler_tree.heading('Interval', text='Interval')
        self.scheduler_tree.heading('Command/Message', text='Command/Message')
        self.scheduler_tree.heading('Status', text='Status')
        
        self.scheduler_tree.column('#0', width=50)
        self.scheduler_tree.column('Type', width=120)
        self.scheduler_tree.column('Interval', width=120)
        self.scheduler_tree.column('Command/Message', width=350)
        self.scheduler_tree.column('Status', width=100)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.scheduler_tree.yview)
        self.scheduler_tree.configure(yscrollcommand=scrollbar.set)
        
        self.scheduler_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Actions frame
        actions_frame = ttk.LabelFrame(self.scheduler_frame, text="Scheduler Actions", padding=10)
        actions_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(actions_frame, text="Add Announcement", command=self.add_scheduled_announcement).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions_frame, text="Add Command", command=self.add_scheduled_command).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions_frame, text="Enable Selected", command=self.enable_scheduled_task).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions_frame, text="Disable Selected", command=self.disable_scheduled_task).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions_frame, text="Remove Selected", command=self.remove_scheduled_task).pack(side=tk.LEFT, padx=5)
        
        # Initialize scheduler storage
        self.scheduled_tasks = []
        self.scheduler_timers = {}
        
        # Load saved tasks
        self.load_scheduled_tasks()
        
    def toggle_password_visibility(self):
        """Toggle password visibility"""
        if self.show_password_var.get():
            self.password_entry.config(show="")
        else:
            self.password_entry.config(show="*")
    
    def connect_to_server(self):
        """Connect to the RCON server"""
        # Check if already connected - if so, disconnect
        if self.rcon and self.connect_btn.cget('text') == 'Disconnect':
            self.rcon.disconnect()
            self.rcon = None
            self.status_label.config(text="Status: Disconnected", foreground="red")
            self.connect_btn.config(text="Connect")
            return
        
        try:
            host = self.host_entry.get().strip()  # Strip whitespace
            port_str = self.port_entry.get().strip()
            password = self.password_entry.get()  # DON'T strip password - might be intentional
            
            if not host or not port_str:
                messagebox.showwarning("Missing Info", "Please enter host and port")
                return
            
            try:
                port = int(port_str)
            except ValueError:
                messagebox.showerror("Invalid Port", "Port must be a number")
                return
            
            if not password:
                if not messagebox.askyesno("No Password", "RCON password is empty. Continue?"):
                    return
            
            # Debug: show what we're actually using
            print(f"DEBUG: Connecting to {repr(host)}:{port} with password {repr(password)}")
            
            # Create RCON client and connect
            self.rcon = RCONClient(host, port, password)
            self.rcon.connect()
            
            self.status_label.config(text="Status: Connected", foreground="green")
            self.connect_btn.config(text="Disconnect")
            messagebox.showinfo("Success", "Connected to server successfully!\n\nConnection will remain open for commands.")
            
            # Auto-refresh initial data
            self.refresh_all()
            
        except Exception as e:
            error_msg = str(e)
            print(f"DEBUG: Connection error: {error_msg}")
            messagebox.showerror("Connection Error", error_msg)
            self.status_label.config(text="Status: Connection Failed", foreground="red")
            self.rcon = None
            
    def refresh_players(self):
        """Refresh the players list"""
        if not self.rcon:
            messagebox.showwarning("Not Connected", "Please connect to the server first")
            return
        
        try:
            # Clear existing items
            for item in self.players_tree.get_children():
                self.players_tree.delete(item)
            
            # Get players from RCON
            response = self.rcon.execute_command('players')
            
            # Log the raw response for debugging
            self.log_command_output(f"Raw 'players' response:\n{repr(response)}\n---\n{response}")
            
            # Parse response - format is like: "Players connected (1): \nPlayerName\n"
            if not response or not response.strip():
                self.players_tree.insert('', tk.END, text='0',
                                        values=('No players online', '', ''))
                return
            
            lines = response.strip().split('\n')
            player_count = 0
            
            # First line is "Players connected (N):"
            # Remaining lines are player names
            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                
                # Skip the header line
                if 'Players connected' in line:
                    continue
                
                # This is a player name
                player_count += 1
                self.players_tree.insert('', tk.END, text=str(player_count), 
                                        values=(line, 'User', 'Online'))
            
            # If no players found after parsing
            if player_count == 0:
                self.players_tree.insert('', tk.END, text='0',
                                        values=('No players online', '', ''))
                        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh players: {str(e)}")
            self.log_command_output(f"Error refreshing players: {str(e)}")
            
    def player_action(self, action):
        """Perform action on a player"""
        username = self.player_username_entry.get()
        if not username:
            messagebox.showwarning("No Username", "Please enter a username")
            return
        
        if not self.rcon:
            messagebox.showwarning("Not Connected", "Please connect to the server first")
            return
        
        try:
            if action == 'kick':
                cmd = f'kickuser "{username}"'
            elif action == 'ban':
                cmd = f'banuser "{username}"'
            elif action == 'admin':
                cmd = f'setaccesslevel "{username}" admin'
            elif action == 'removeadmin':
                cmd = f'setaccesslevel "{username}" none'
            elif action == 'godmode':
                cmd = f'godmod "{username}"'
            elif action == 'teleport':
                # Open teleport dialog
                self.open_teleport_dialog(username)
                return
            else:
                return
            
            response = self.rcon.execute_command(cmd)
            self.log_command_output(f"Action: {action}\nCommand: {cmd}\nResponse: {response}")
            messagebox.showinfo("Success", f"Action '{action}' executed for {username}")
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def open_teleport_dialog(self, username):
        """Open dialog to choose teleport destination"""
        dialog = tk.Toplevel(self)
        dialog.title(f"Teleport {username}")
        dialog.geometry("400x200")
        dialog.transient(self)
        dialog.grab_set()
        self.apply_dialog_theme(dialog)
        
        ttk.Label(dialog, text=f"Teleport {username} to another player:", 
                 font=('TkDefaultFont', 10, 'bold')).pack(pady=10)
        
        info_label = ttk.Label(dialog, 
                              text="Note: RCON can only teleport players to other players.\nCoordinate teleports must be done in-game by an admin.",
                              foreground='blue', font=('TkDefaultFont', 8))
        info_label.pack(pady=5)
        
        # Teleport to another player
        player_frame = ttk.LabelFrame(dialog, text="Teleport to Player", padding=10)
        player_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(player_frame, text="Target player name:").pack(anchor=tk.W, pady=5)
        target_entry = ttk.Entry(player_frame, width=30)
        target_entry.pack(fill=tk.X, pady=5)
        target_entry.focus()
        
        def teleport_to_player():
            target = target_entry.get().strip()
            if not target:
                messagebox.showwarning("No Target", "Please enter a target player name")
                return
            
            try:
                cmd = f'teleport "{username}" "{target}"'
                response = self.rcon.execute_command(cmd)
                self.log_command_output(f"Teleport: {username} → {target}\nCommand: {cmd}\nResponse: {response}")
                messagebox.showinfo("Success", f"Teleported {username} to {target}")
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        btn_frame = ttk.Frame(player_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="Teleport", command=teleport_to_player).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
            
    def get_server_info(self):
        """Get server information"""
        if not self.rcon:
            messagebox.showwarning("Not Connected", "Please connect to the server first")
            return
        
        try:
            self.info_text.delete(1.0, tk.END)
            
            # Get various server info
            commands = ['help', 'servermsg', 'players']
            
            info = "=== SERVER INFORMATION ===\n\n"
            info += f"Connected to: {self.host_entry.get()}:{self.port_entry.get()}\n"
            info += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            # If server path is set, get file-based info
            if self.server_path.get() and os.path.exists(self.server_path.get()):
                info += self.get_file_based_info()
            
            self.info_text.insert(tk.END, info)
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
            
    def get_file_based_info(self):
        """Get information from server files"""
        info = "=== FILE-BASED INFORMATION ===\n\n"
        server_path = Path(self.server_path.get())
        
        try:
            # Check for server config
            config_files = ['servertest.ini', 'Zomboid/Server/servertest.ini']
            for config_file in config_files:
                config_path = server_path / config_file
                if config_path.exists():
                    info += f"Config file found: {config_path}\n"
                    # Could parse config here
                    break
            
            # Check for database
            db_files = list(server_path.rglob('players.db'))
            if db_files:
                info += f"\nPlayer database found: {db_files[0]}\n"
                info += self.get_database_info(db_files[0])
            
            # Check for logs
            log_dir = server_path / 'Zomboid' / 'Logs'
            if log_dir.exists():
                log_files = list(log_dir.glob('*.txt'))
                info += f"\nLog files found: {len(log_files)}\n"
                
        except Exception as e:
            info += f"\nError reading files: {str(e)}\n"
        
        return info + "\n"
        
    def get_database_info(self, db_path):
        """Get information from the players database"""
        info = ""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get player count
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            info += f"Database tables: {', '.join([t[0] for t in tables])}\n"
            
            # Try to get player count
            if ('networkPlayers',) in tables:
                cursor.execute("SELECT COUNT(*) FROM networkPlayers")
                count = cursor.fetchone()[0]
                info += f"Total players in database: {count}\n"
            
            conn.close()
        except Exception as e:
            info += f"Error reading database: {str(e)}\n"
        
        return info
        
    def get_server_stats(self):
        """Get server statistics"""
        # This would require custom implementation based on available data
        messagebox.showinfo("Info", "Server stats feature requires additional RCON commands or mods")
    
    def configure_server_control(self):
        """Open configuration dialog for server control commands"""
        dialog = tk.Toplevel(self)
        dialog.title("Configure Server Control Commands")
        dialog.geometry("700x500")  # Increased from 600x400
        dialog.transient(self)
        dialog.grab_set()
        self.apply_dialog_theme(dialog)
        
        ttk.Label(dialog, text="Configure Server Control Commands", 
                 font=('TkDefaultFont', 11, 'bold')).pack(pady=10)
        
        ttk.Label(dialog, text="Enter the commands your system uses to control the server.\nExamples: systemctl, scripts, docker, screen, etc.", 
                 foreground='blue', font=('TkDefaultFont', 9)).pack(pady=5)
        
        # Form frame
        form_frame = ttk.Frame(dialog)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Start command
        ttk.Label(form_frame, text="Start Command:").grid(row=0, column=0, sticky=tk.W, pady=5)
        start_entry = ttk.Entry(form_frame, width=50)
        start_entry.grid(row=0, column=1, pady=5, sticky=tk.EW)
        
        # Stop command
        ttk.Label(form_frame, text="Stop Command:").grid(row=1, column=0, sticky=tk.W, pady=5)
        stop_entry = ttk.Entry(form_frame, width=50)
        stop_entry.grid(row=1, column=1, pady=5, sticky=tk.EW)
        
        # Restart command
        ttk.Label(form_frame, text="Restart Command:").grid(row=2, column=0, sticky=tk.W, pady=5)
        restart_entry = ttk.Entry(form_frame, width=50)
        restart_entry.grid(row=2, column=1, pady=5, sticky=tk.EW)
        
        # Status command
        ttk.Label(form_frame, text="Status Command (optional):").grid(row=3, column=0, sticky=tk.W, pady=5)
        status_entry = ttk.Entry(form_frame, width=50)
        status_entry.grid(row=3, column=1, pady=5, sticky=tk.EW)
        
        form_frame.columnconfigure(1, weight=1)
        
        # Examples
        examples_frame = ttk.LabelFrame(dialog, text="Examples", padding=10)
        examples_frame.pack(fill=tk.X, padx=20, pady=10)
        
        examples_text = scrolledtext.ScrolledText(examples_frame, height=6, wrap=tk.WORD)
        examples_text.pack(fill=tk.BOTH, expand=True)
        examples_text.insert(tk.END, """systemd:
  Start: sudo systemctl start zomboid
  Stop: sudo systemctl stop zomboid
  Restart: sudo systemctl restart zomboid
  Status: sudo systemctl status zomboid

Script:
  Start: cd /home/zomboid/server && ./start-server.sh
  Stop: cd /home/zomboid/server && ./stop-server.sh
  
Docker:
  Start: docker start pz-server
  Stop: docker stop pz-server
  Restart: docker restart pz-server

Screen:
  Start: screen -dmS pz /home/zomboid/server/start-server.sh
  Stop: screen -S pz -X quit
""")
        examples_text.config(state=tk.DISABLED)
        
        # Load existing values
        try:
            config_file = Path.home() / '.pz_admin_tool_server_control.json'
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    start_entry.insert(0, config.get('start_cmd', ''))
                    stop_entry.insert(0, config.get('stop_cmd', ''))
                    restart_entry.insert(0, config.get('restart_cmd', ''))
                    status_entry.insert(0, config.get('status_cmd', ''))
        except (IOError, OSError, json.JSONDecodeError):
            pass  # Use empty fields if can't load config
        
        # Save button
        def save_commands():
            config = {
                'start_cmd': start_entry.get(),
                'stop_cmd': stop_entry.get(),
                'restart_cmd': restart_entry.get(),
                'status_cmd': status_entry.get()
            }
            
            config_file = Path.home() / '.pz_admin_tool_server_control.json'
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            messagebox.showinfo("Success", "Server control commands saved!")
            dialog.destroy()
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Button(btn_frame, text="Save Commands", command=save_commands).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def _load_server_control_config(self):
        """Load server control commands from config"""
        try:
            config_file = Path.home() / '.pz_admin_tool_server_control.json'
            if config_file.exists():
                with open(config_file, 'r') as f:
                    return json.load(f)
        except (IOError, OSError, json.JSONDecodeError):
            pass  # Return empty dict if can't load
        return {}
    
    def _execute_shell_command(self, command, action_name):
        """Execute a shell command and show result"""
        if not command:
            messagebox.showwarning("Not Configured", 
                                 f"{action_name} command not configured.\n\n"
                                 f"Click 'Configure Commands' to set it up.")
            return
        
        try:
            self.log_command_output(f"Executing {action_name}: {command}")
            
            # Execute command
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            
            output = result.stdout + result.stderr
            self.log_command_output(f"{action_name} output:\n{output}")
            
            if result.returncode == 0:
                messagebox.showinfo("Success", f"{action_name} completed successfully!\n\nCheck the Commands tab for output.")
            else:
                messagebox.showwarning("Command Completed", 
                                     f"{action_name} completed with return code {result.returncode}\n\n"
                                     f"Check the Commands tab for details.")
        except subprocess.TimeoutExpired:
            messagebox.showerror("Timeout", f"{action_name} command timed out after 30 seconds")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to execute {action_name}:\n{str(e)}")
    
    def start_server(self):
        """Start the server"""
        config = self._load_server_control_config()
        cmd = config.get('start_cmd', '')
        
        if messagebox.askyesno("Confirm Start", "Start the Project Zomboid server?"):
            self._execute_shell_command(cmd, "Start Server")
    
    def stop_server(self):
        """Stop the server"""
        config = self._load_server_control_config()
        cmd = config.get('stop_cmd', '')
        
        if messagebox.askyesno("Confirm Stop", 
                              "Stop the Project Zomboid server?\n\n"
                              "⚠️ Make sure to save first!",
                              icon='warning'):
            self._execute_shell_command(cmd, "Stop Server")
    
    def restart_server(self):
        """Restart the server"""
        config = self._load_server_control_config()
        cmd = config.get('restart_cmd', '')
        
        if messagebox.askyesno("Confirm Restart", 
                              "Restart the Project Zomboid server?\n\n"
                              "⚠️ Make sure to save first!",
                              icon='warning'):
            self._execute_shell_command(cmd, "Restart Server")
    
    def open_restart_timer(self):
        """Open scheduled restart timer dialog"""
        dialog = tk.Toplevel(self)
        dialog.title("Scheduled Server Restart")
        dialog.geometry("500x400")
        dialog.transient(self)
        dialog.grab_set()
        self.apply_dialog_theme(dialog)
        
        ttk.Label(dialog, text="Schedule Server Restart with Countdown", 
                 font=('TkDefaultFont', 11, 'bold')).pack(pady=10)
        
        # Time selection frame
        time_frame = ttk.LabelFrame(dialog, text="Restart In", padding=10)
        time_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Minutes selection
        ttk.Label(time_frame, text="Minutes:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        minutes_var = tk.IntVar(value=30)
        minutes_spin = ttk.Spinbox(time_frame, from_=1, to=480, textvariable=minutes_var, width=10)
        minutes_spin.grid(row=0, column=1, padx=5, pady=5)
        
        # Quick presets
        preset_frame = ttk.Frame(time_frame)
        preset_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        ttk.Button(preset_frame, text="5 min", command=lambda: minutes_var.set(5)).pack(side=tk.LEFT, padx=2)
        ttk.Button(preset_frame, text="15 min", command=lambda: minutes_var.set(15)).pack(side=tk.LEFT, padx=2)
        ttk.Button(preset_frame, text="30 min", command=lambda: minutes_var.set(30)).pack(side=tk.LEFT, padx=2)
        ttk.Button(preset_frame, text="1 hour", command=lambda: minutes_var.set(60)).pack(side=tk.LEFT, padx=2)
        ttk.Button(preset_frame, text="2 hours", command=lambda: minutes_var.set(120)).pack(side=tk.LEFT, padx=2)
        ttk.Button(preset_frame, text="3 hours", command=lambda: minutes_var.set(180)).pack(side=tk.LEFT, padx=2)
        
        # Warning intervals
        warnings_frame = ttk.LabelFrame(dialog, text="Warning Intervals", padding=10)
        warnings_frame.pack(fill=tk.X, padx=20, pady=10)
        
        warn_30min = tk.BooleanVar(value=True)
        warn_15min = tk.BooleanVar(value=True)
        warn_10min = tk.BooleanVar(value=True)
        warn_5min = tk.BooleanVar(value=True)
        warn_1min = tk.BooleanVar(value=True)
        warn_30sec = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(warnings_frame, text="30 minutes", variable=warn_30min).grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Checkbutton(warnings_frame, text="15 minutes", variable=warn_15min).grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        ttk.Checkbutton(warnings_frame, text="10 minutes", variable=warn_10min).grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)
        ttk.Checkbutton(warnings_frame, text="5 minutes", variable=warn_5min).grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Checkbutton(warnings_frame, text="1 minute", variable=warn_1min).grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        ttk.Checkbutton(warnings_frame, text="30 seconds", variable=warn_30sec).grid(row=1, column=2, sticky=tk.W, padx=5, pady=2)
        
        # Options
        options_frame = ttk.LabelFrame(dialog, text="Options", padding=10)
        options_frame.pack(fill=tk.X, padx=20, pady=10)
        
        auto_save = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Auto-save 1 minute before restart", variable=auto_save).pack(anchor=tk.W)
        
        repeat_restart = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="🔄 Repeat restart automatically (for daily/scheduled restarts)", 
                       variable=repeat_restart).pack(anchor=tk.W, pady=(5, 0))
        
        # Buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill=tk.X, padx=20, pady=10)
        
        def start_countdown():
            minutes = minutes_var.get()
            if minutes < 1:
                messagebox.showwarning("Invalid Time", "Please enter at least 1 minute")
                return
            
            warnings = {
                'warn_30min': warn_30min.get(),
                'warn_15min': warn_15min.get(),
                'warn_10min': warn_10min.get(),
                'warn_5min': warn_5min.get(),
                'warn_1min': warn_1min.get(),
                'warn_30sec': warn_30sec.get(),
                'auto_save': auto_save.get(),
                'repeat': repeat_restart.get()
            }
            
            dialog.destroy()
            self.start_restart_countdown(minutes, warnings)
        
        ttk.Button(btn_frame, text="Start Countdown", command=start_countdown).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
    
    def start_restart_countdown(self, total_minutes, warnings):
        """Start the restart countdown with progress window"""
        self.restart_countdown_active = True
        self.restart_time_remaining = total_minutes * 60  # Convert to seconds
        
        # Create countdown window
        countdown_window = tk.Toplevel(self)
        if warnings.get('repeat', False):
            countdown_window.title("Repeating Server Restart")
            title_text = "🔄 Repeating Server Restart"
        else:
            countdown_window.title("Server Restart in Progress")
            title_text = "⏰ Server Restart Scheduled"
        
        countdown_window.geometry("450x250")
        countdown_window.transient(self)
        self.apply_dialog_theme(countdown_window)
        
        # Prevent closing without canceling
        countdown_window.protocol("WM_DELETE_WINDOW", lambda: None)
        
        ttk.Label(countdown_window, text=title_text, 
                 font=('TkDefaultFont', 12, 'bold')).pack(pady=15)
        
        # Time remaining label
        time_label = ttk.Label(countdown_window, text="", font=('TkDefaultFont', 16))
        time_label.pack(pady=10)
        
        # Progress bar
        progress = ttk.Progressbar(countdown_window, length=400, mode='determinate')
        progress.pack(pady=10)
        progress['maximum'] = total_minutes * 60
        progress['value'] = total_minutes * 60
        
        # Status label
        status_label = ttk.Label(countdown_window, text="Countdown active...")
        status_label.pack(pady=10)
        
        # Cancel button
        def cancel_restart():
            self.restart_countdown_active = False
            self.restart_indicator.config(text="")  # Clear indicator
            countdown_window.destroy()
            if self.rcon and self.rcon.authenticated:
                try:
                    self.rcon.execute_command('servermsg "Server restart has been CANCELLED."')
                except Exception:
                    pass
            messagebox.showinfo("Cancelled", "Server restart has been cancelled")
        
        ttk.Button(countdown_window, text="Cancel Restart", command=cancel_restart).pack(pady=10)
        
        # Warning tracking
        warnings_sent = set()
        total_seconds = total_minutes * 60
        
        def update_countdown():
            if not self.restart_countdown_active:
                return
            
            # Update time display
            mins = self.restart_time_remaining // 60
            secs = self.restart_time_remaining % 60
            time_label.config(text=f"{mins:02d}:{secs:02d}")
            progress['value'] = self.restart_time_remaining
            
            # Update admin indicator in main window
            if mins > 0:
                self.restart_indicator.config(text=f"⏰ Restart in {mins}m {secs}s")
            else:
                self.restart_indicator.config(text=f"⏰ Restart in {secs}s")
            
            # Check for warnings
            if self.rcon and self.rcon.authenticated:
                try:
                    # 30 minutes
                    if warnings['warn_30min'] and self.restart_time_remaining == 1800 and '30min' not in warnings_sent:
                        self.rcon.execute_command('servermsg "Server will restart in 30 minutes! Please finish up."')
                        status_label.config(text="⚠️ 30 minute warning sent")
                        warnings_sent.add('30min')
                    
                    # 15 minutes
                    elif warnings['warn_15min'] and self.restart_time_remaining == 900 and '15min' not in warnings_sent:
                        self.rcon.execute_command('servermsg "Server will restart in 15 minutes!"')
                        status_label.config(text="⚠️ 15 minute warning sent")
                        warnings_sent.add('15min')
                    
                    # 10 minutes
                    elif warnings['warn_10min'] and self.restart_time_remaining == 600 and '10min' not in warnings_sent:
                        self.rcon.execute_command('servermsg "Server will restart in 10 minutes!"')
                        status_label.config(text="⚠️ 10 minute warning sent")
                        warnings_sent.add('10min')
                    
                    # 5 minutes
                    elif warnings['warn_5min'] and self.restart_time_remaining == 300 and '5min' not in warnings_sent:
                        self.rcon.execute_command('servermsg "Server will restart in 5 minutes!"')
                        status_label.config(text="⚠️ 5 minute warning sent")
                        warnings_sent.add('5min')
                    
                    # 1 minute + auto-save
                    elif warnings['warn_1min'] and self.restart_time_remaining == 60 and '1min' not in warnings_sent:
                        self.rcon.execute_command('servermsg "Server will restart in 1 minute!"')
                        if warnings['auto_save']:
                            self.rcon.execute_command('save')
                            status_label.config(text="💾 Auto-save triggered")
                        else:
                            status_label.config(text="⚠️ 1 minute warning sent")
                        warnings_sent.add('1min')
                    
                    # 30 seconds
                    elif warnings['warn_30sec'] and self.restart_time_remaining == 30 and '30sec' not in warnings_sent:
                        self.rcon.execute_command('servermsg "Server restarting in 30 seconds!"')
                        status_label.config(text="⚠️ 30 second warning sent")
                        warnings_sent.add('30sec')
                except Exception:
                    pass  # Continue countdown even if message fails
            
            # Countdown complete
            if self.restart_time_remaining <= 0:
                self.restart_countdown_active = False
                countdown_window.destroy()
                
                # Final warning
                if self.rcon and self.rcon.authenticated:
                    try:
                        self.rcon.execute_command('servermsg "Server is restarting NOW!"')
                    except Exception:
                        pass
                
                # Execute restart
                self.log_command_output("⏰ Scheduled restart time reached - restarting server...")
                config = self._load_server_control_config()
                cmd = config.get('restart_cmd', '')
                self._execute_shell_command(cmd, "Scheduled Restart")
                
                # Check if should repeat
                if warnings.get('repeat', False):
                    # Schedule next restart with same settings
                    self.after(5000, lambda: self.start_restart_countdown(total_minutes, warnings))
                    self.log_command_output(f"🔄 Repeating restart scheduled - next restart in {total_minutes} minutes")
                else:
                    # One-time restart, clear indicator
                    self.restart_indicator.config(text="")
                
                return
            
            # Decrement and schedule next update
            self.restart_time_remaining -= 1
            countdown_window.after(1000, update_countdown)
        
        # Start the countdown
        update_countdown()
    
    def check_server_status(self):
        """Check server status"""
        config = self._load_server_control_config()
        cmd = config.get('status_cmd', '')
        
        if not cmd:
            messagebox.showinfo("No Status Command", 
                              "Status command not configured.\n\n"
                              "You can still check if the server is running by trying to connect via RCON.")
            return
        
        self._execute_shell_command(cmd, "Server Status")
        
    def quick_command(self, cmd):
        """Execute a quick command"""
        if not self.rcon:
            messagebox.showwarning("Not Connected", "Please connect to the server first")
            return
        
        try:
            response = self.rcon.execute_command(cmd)
            self.log_command_output(f"Command: {cmd}\nResponse: {response}")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            
    def send_server_message(self):
        """Send a message to all players"""
        message = tk.simpledialog.askstring("Server Message", "Enter message to broadcast:")
        if message:
            try:
                # Replace spaces with underscores for RCON compatibility
                safe_message = message.replace(' ', '_')
                response = self.rcon.execute_command(f'servermsg "{safe_message}"')
                self.log_command_output(f"Broadcast: {message}\nResponse: {response}")
            except Exception as e:
                messagebox.showerror("Error", str(e))
                
    def execute_custom_command(self):
        """Execute a custom RCON command"""
        cmd = self.command_entry.get()
        if not cmd:
            return
        
        if not self.rcon:
            messagebox.showwarning("Not Connected", "Please connect to the server first")
            return
        
        try:
            response = self.rcon.execute_command(cmd)
            self.log_command_output(f"Command: {cmd}\nResponse: {response}")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            
    def log_command_output(self, text):
        """Log command output to the commands tab"""
        self.command_output.insert(tk.END, f"\n[{datetime.now().strftime('%H:%M:%S')}]\n{text}\n")
        self.command_output.insert(tk.END, "=" * 50 + "\n")
        self.command_output.see(tk.END)
    
    def open_workshop_in_browser(self):
        """Open selected Workshop ID in Steam browser"""
        
        # Get selected item from workshop tree
        selection = self.workshop_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a Workshop ID from the right panel")
            return
        
        # Get the Workshop ID from the selected item
        item = selection[0]
        workshop_id = self.workshop_tree.item(item)['values'][0]
        
        # Build URL
        url = f"https://steamcommunity.com/sharedfiles/filedetails/?id={workshop_id}"
        
        # Try to copy to clipboard
        try:
            self.clipboard_clear()
            self.clipboard_append(url)
            self.update()
            clipboard_success = True
        except tk.TclError:
            clipboard_success = False  # Clipboard not available
        
        # Try multiple methods to open browser
        browser_opened = False
        
        # Method 1: Python webbrowser
        try:
            webbrowser.open(url)
            browser_opened = True
        except (webbrowser.Error, OSError):
            pass  # Try next method
        
        # Method 2: xdg-open (Linux)
        if not browser_opened:
            try:
                subprocess.Popen(['xdg-open', url])
                browser_opened = True
            except (FileNotFoundError, OSError):
                pass  # Try next method
        
        # Method 3: Direct firefox
        if not browser_opened:
            try:
                subprocess.Popen(['firefox', url])
                browser_opened = True
            except (FileNotFoundError, OSError):
                pass  # Try next method
        
        # Method 4: Direct chrome/chromium
        if not browser_opened:
            try:
                subprocess.Popen(['google-chrome', url])
                browser_opened = True
            except (FileNotFoundError, OSError):
                try:
                    subprocess.Popen(['chromium-browser', url])
                    browser_opened = True
                except (FileNotFoundError, OSError):
                    pass  # All methods failed
        
        # Show result
        if browser_opened:
            msg = f"Opened Workshop ID {workshop_id} in browser"
            if clipboard_success:
                msg += "\n\nURL also copied to clipboard!"
            messagebox.showinfo("Success", msg)
        else:
            # Browser didn't open - show URL for manual copy
            msg = f"Could not automatically open browser.\n\nWorkshop ID: {workshop_id}\n\nURL:\n{url}"
            if clipboard_success:
                msg += "\n\n✓ URL copied to clipboard - paste in your browser!"
            else:
                msg += "\n\nPlease copy the URL above and paste in your browser."
            messagebox.showinfo("Workshop URL", msg)
        
        self.log_command_output(f"Workshop ID {workshop_id}:\n{url}")
    
    def open_mod_editor_from_mods_tab(self):
        """Open the mod editor from the mods tab"""
        if not self.server_path.get() or not os.path.exists(self.server_path.get()):
            messagebox.showwarning("No Server Path", "Please set the server path first")
            return
        
        # Find the .ini file
        server_path = Path(self.server_path.get())
        server_dir = server_path / 'Server'
        
        ini_files = []
        if server_dir.exists():
            ini_files = list(server_dir.glob('*.ini'))
        
        if not ini_files:
            messagebox.showerror("Error", "Could not find server .ini file in Server directory")
            return
        
        # If only one file, use it; otherwise let user choose
        if len(ini_files) == 1:
            ini_file = ini_files[0]
            ModManagerWindow(self, ini_file, server_path)
        else:
            # Show selection dialog
            FileSelectionDialog(self, server_path, ini_files, [])
        
    def refresh_mods(self):
        """Refresh the mods list from server files"""
        # Clear existing items
        for item in self.mods_tree.get_children():
            self.mods_tree.delete(item)
        for item in self.workshop_tree.get_children():
            self.workshop_tree.delete(item)
        
        if not self.server_path.get() or not os.path.exists(self.server_path.get()):
            messagebox.showwarning("No Server Path", "Please set the server path to view mods")
            return
        
        try:
            server_path = Path(self.server_path.get())
            
            # Look for server config file
            config_files = ['Server/servertest.ini', 'servertest.ini']
            
            mods = []
            workshop_ids = []
            
            for config_file in config_files:
                config_path = server_path / config_file
                if config_path.exists():
                    with open(config_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                        # Parse mods and workshop IDs
                        for line in content.split('\n'):
                            if line.startswith('Mods='):
                                mods_str = line.split('=')[1].strip()
                                mods = [m.strip() for m in mods_str.split(';') if m.strip()]
                            elif line.startswith('WorkshopItems='):
                                workshop_str = line.split('=')[1].strip()
                                workshop_ids = [w.strip() for w in workshop_str.split(';') if w.strip()]
                    break
            
            # Populate mods list (left panel) - clean display
            for i, mod in enumerate(mods):
                self.mods_tree.insert('', tk.END, text=str(i+1), values=(mod,))
            
            # Populate workshop IDs list (right panel) - clean display
            for i, workshop_id in enumerate(workshop_ids):
                self.workshop_tree.insert('', tk.END, text=str(i+1), values=(workshop_id,))
            
            # Simple summary
            self.log_command_output(
                f"Mods: {len(mods)} | Workshop IDs: {len(workshop_ids)}\n"
                f"Double-click any Workshop ID to view on Steam Workshop."
            )
                    
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read mods: {str(e)}")
            
    def refresh_logs(self):
        """Refresh the server logs"""
        if not self.server_path.get() or not os.path.exists(self.server_path.get()):
            messagebox.showwarning("No Server Path", "Please set the server path to view logs")
            return
        
        try:
            server_path = Path(self.server_path.get())
            log_dir = server_path / 'Zomboid' / 'Logs'
            
            if not log_dir.exists():
                log_dir = server_path / 'Logs'
            
            if not log_dir.exists():
                messagebox.showwarning("Logs Not Found", "Could not find logs directory")
                return
            
            # Find most recent log file
            log_files = sorted(log_dir.glob('*.txt'), key=os.path.getmtime, reverse=True)
            
            if not log_files:
                messagebox.showinfo("No Logs", "No log files found")
                return
            
            # Read last N lines
            lines_to_read = int(self.log_lines_entry.get() or 100)
            
            with open(log_files[0], 'r', encoding='utf-8', errors='ignore') as f:
                all_lines = f.readlines()
                recent_lines = all_lines[-lines_to_read:]
            
            self.logs_text.delete(1.0, tk.END)
            self.logs_text.insert(tk.END, f"=== {log_files[0].name} (last {lines_to_read} lines) ===\n\n")
            self.logs_text.insert(tk.END, ''.join(recent_lines))
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read logs: {str(e)}")
    
    def toggle_live_logs(self):
        """Toggle live log streaming"""
        if self.live_logs_var.get():
            # Start live streaming
            if not self.server_path.get() or not os.path.exists(self.server_path.get()):
                messagebox.showwarning("No Server Path", "Please set the server path first")
                self.live_logs_var.set(False)
                return
            
            # Find log file
            server_path = Path(self.server_path.get())
            log_dir = server_path / 'Zomboid' / 'Logs'
            
            if not log_dir.exists():
                log_dir = server_path / 'Logs'
            
            if not log_dir.exists():
                messagebox.showwarning("Logs Not Found", "Could not find logs directory")
                self.live_logs_var.set(False)
                return
            
            # Find most recent log file
            log_files = sorted(log_dir.glob('*.txt'), key=os.path.getmtime, reverse=True)
            
            if not log_files:
                messagebox.showinfo("No Logs", "No log files found")
                self.live_logs_var.set(False)
                return
            
            self.current_log_file = log_files[0]
            
            # Clear the log display
            self.logs_text.delete(1.0, tk.END)
            self.logs_text.insert(tk.END, f"=== Live Streaming: {self.current_log_file.name} ===\n")
            self.logs_text.insert(tk.END, f"=== Log file: {self.current_log_file} ===\n\n")
            
            # Read last 50 lines first to show context
            try:
                with open(self.current_log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    all_lines = f.readlines()
                    recent_lines = all_lines[-50:] if len(all_lines) > 50 else all_lines
                    self.logs_text.insert(tk.END, ''.join(recent_lines))
                    self.logs_text.insert(tk.END, "\n--- [Live updates below] ---\n\n")
                    
                    # Set position to end of file
                    self.log_file_position = f.tell()
            except Exception as e:
                self.logs_text.insert(tk.END, f"Error reading initial log: {str(e)}\n")
                self.log_file_position = 0
            
            self.live_logs_active = True
            
            # Auto-scroll to bottom
            self.logs_text.see(tk.END)
            
            # Start streaming immediately
            self.after(100, self.stream_logs)
            
            self.log_command_output(f"Live log streaming started: {self.current_log_file}")
        else:
            # Stop live streaming
            self.live_logs_active = False
            self.log_command_output("Live log streaming stopped")
    
    def stream_logs(self):
        """Stream new log lines in real-time"""
        if not self.live_logs_active:
            return
        
        try:
            if self.current_log_file and self.current_log_file.exists():
                # Check current file size
                current_size = os.path.getsize(self.current_log_file)
                
                # If file was truncated/rotated, reset position
                if current_size < self.log_file_position:
                    self.log_file_position = 0
                    self.logs_text.insert(tk.END, "\n--- [Log file rotated/cleared] ---\n\n")
                
                with open(self.current_log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    # Seek to last read position
                    f.seek(self.log_file_position)
                    
                    # Read new lines
                    new_lines = f.readlines()
                    
                    if new_lines:
                        # Update position
                        self.log_file_position = f.tell()
                        
                        # Append new lines to text widget
                        self.logs_text.insert(tk.END, ''.join(new_lines))
                        
                        # Auto-scroll to bottom
                        self.logs_text.see(tk.END)
                        
                        # Limit total lines to prevent memory issues (keep last 1000 lines)
                        total_lines = int(self.logs_text.index('end-1c').split('.')[0])
                        if total_lines > 1000:
                            self.logs_text.delete('1.0', f'{total_lines - 1000}.0')
        except Exception as e:
            self.logs_text.insert(tk.END, f"\n[Live stream error: {str(e)}]\n")
            self.log_command_output(f"Live log streaming error: {str(e)}")
        
        # Schedule next check (every 1 second)
        if self.live_logs_active:
            self.after(1000, self.stream_logs)
    
    def refresh_banlist(self):
        """Refresh the ban list from server files"""
        # Clear existing items
        for item in self.banlist_tree.get_children():
            self.banlist_tree.delete(item)
        
        if not self.server_path.get() or not os.path.exists(self.server_path.get()):
            messagebox.showwarning("No Server Path", "Please set the server path to view ban list")
            return
        
        try:
            server_path = Path(self.server_path.get())
            
            # Try multiple possible locations for banlist
            banlist_paths = [
                server_path / 'Server' / 'banlist.txt',
                server_path / 'Zomboid' / 'Server' / 'banlist.txt',
                server_path / 'banlist.txt'
            ]
            
            banlist_file = None
            for path in banlist_paths:
                if path.exists():
                    banlist_file = path
                    break
            
            if not banlist_file:
                self.banlist_tree.insert('', tk.END, text='0',
                                        values=('No bans found', '', '', ''))
                self.log_command_output(f"Ban list file not found. Tried:\n" + 
                                       "\n".join(f"  - {p}" for p in banlist_paths))
                return
            
            # Read ban list
            with open(banlist_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            if not lines:
                self.banlist_tree.insert('', tk.END, text='0',
                                        values=('No bans', '', '', ''))
                return
            
            # Parse ban list - format varies, so we'll handle different formats
            count = 0
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Try to parse different formats
                # Format 1: username,ip,reason
                # Format 2: username
                parts = line.split(',')
                
                username = parts[0] if len(parts) > 0 else 'Unknown'
                ip = parts[1] if len(parts) > 1 else 'N/A'
                reason = parts[2] if len(parts) > 2 else 'No reason specified'
                date = 'N/A'  # Banlist doesn't typically store dates
                
                count += 1
                self.banlist_tree.insert('', tk.END, text=str(count),
                                        values=(username, ip, reason, date))
            
            self.log_command_output(f"Loaded {count} banned users from {banlist_file}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read ban list: {str(e)}")
    
    def unban_selected(self):
        """Unban the selected user from the list"""
        selection = self.banlist_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a user to unban")
            return
        
        # Get username from selected item
        item = selection[0]
        username = self.banlist_tree.item(item)['values'][0]
        
        if username in ['No bans found', 'No bans']:
            return
        
        # Confirm unban
        if not messagebox.askyesno("Confirm Unban", f"Unban user '{username}'?"):
            return
        
        self.unban_user(username)
    
    def unban_manual(self):
        """Unban user by manually entered username"""
        username = self.unban_username_entry.get().strip()
        if not username:
            messagebox.showwarning("No Username", "Please enter a username to unban")
            return
        
        self.unban_user(username)
    
    def unban_user(self, username):
        """Unban a user using RCON command"""
        if not self.rcon:
            messagebox.showwarning("Not Connected", "Please connect to the server first")
            return
        
        try:
            response = self.rcon.execute_command(f'unbanuser "{username}"')
            self.log_command_output(f"Unban command for '{username}':\n{response}")
            messagebox.showinfo("Success", f"Unbanned '{username}'\n\nRefresh the ban list to see changes.")
            
            # Clear the manual entry field
            self.unban_username_entry.delete(0, tk.END)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to unban user: {str(e)}")
    
    def clear_all_bans(self):
        """Clear all bans (with confirmation)"""
        # Count current bans
        ban_count = len([item for item in self.banlist_tree.get_children() 
                        if self.banlist_tree.item(item)['values'][0] not in ['No bans found', 'No bans']])
        
        if ban_count == 0:
            messagebox.showinfo("No Bans", "There are no bans to clear")
            return
        
        # Confirm
        if not messagebox.askyesno("Confirm Clear All Bans", 
                                   f"Are you sure you want to unban ALL {ban_count} users?\n\n"
                                   f"This action cannot be undone!",
                                   icon='warning'):
            return
        
        if not self.rcon:
            messagebox.showwarning("Not Connected", "Please connect to the server first")
            return
        
        try:
            # Get all usernames
            unbanned = []
            for item in self.banlist_tree.get_children():
                username = self.banlist_tree.item(item)['values'][0]
                if username not in ['No bans found', 'No bans']:
                    try:
                        self.rcon.execute_command(f'unbanuser "{username}"')
                        unbanned.append(username)
                    except Exception as e:
                        pass  # Continue trying to unban others
            
            self.log_command_output(f"Cleared all bans. Unbanned {len(unbanned)} users:\n" + 
                                   "\n".join(f"  - {u}" for u in unbanned))
            messagebox.showinfo("Success", f"Unbanned {len(unbanned)} users\n\nRefresh the ban list to verify.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clear bans: {str(e)}")
            
    def refresh_all(self):
        """Refresh all tabs"""
        self.refresh_players()
        self.get_server_info()
        self.refresh_mods()
        self.refresh_logs()
        self.refresh_banlist()
        
    def toggle_auto_refresh(self):
        """Toggle auto-refresh"""
        if self.auto_refresh_var.get():
            self.auto_refresh = True
            self.auto_refresh_loop()
        else:
            self.auto_refresh = False
            
    def auto_refresh_loop(self):
        """Auto-refresh loop"""
        if self.auto_refresh:
            self.refresh_all()
            self.after(30000, self.auto_refresh_loop)  # 30 seconds
            
    def browse_path(self):
        """Browse for server path"""
        from tkinter import filedialog
        path = filedialog.askdirectory(title="Select Project Zomboid Server Directory")
        if path:
            self.server_path.set(path)
    
    def auto_detect_path(self):
        """Try to auto-detect common server installation paths"""
        common_paths = [
            # Linux steamcmd installations
            os.path.expanduser("~/.steam/steamapps/common/Project Zomboid Dedicated Server"),
            os.path.expanduser("~/Steam/steamapps/common/Project Zomboid Dedicated Server"),
            "/home/pzserver/.steam/steamapps/common/Project Zomboid Dedicated Server",
            "/opt/pzserver",
            # Linux steam user installations
            os.path.expanduser("~/.local/share/Steam/steamapps/common/Project Zomboid Dedicated Server"),
            # Windows paths
            "C:/Program Files (x86)/Steam/steamapps/common/Project Zomboid Dedicated Server",
            "C:/pzserver",
            os.path.expanduser("~/pzserver"),
            # Look for Zomboid folder in common locations
            os.path.expanduser("~/Zomboid"),
            os.path.expanduser("~/.local/share/Zomboid"),
        ]
        
        found_paths = []
        for path in common_paths:
            if os.path.exists(path):
                found_paths.append(path)
        
        if not found_paths:
            messagebox.showinfo("Auto-Detect", 
                "Could not find server installation.\n\n" +
                "Common locations:\n" +
                "- Linux steamcmd: ~/.steam/steamapps/common/Project Zomboid Dedicated Server\n" +
                "- Linux data: ~/Zomboid or ~/.local/share/Zomboid\n" +
                "- Custom: /home/pzserver or /opt/pzserver\n\n" +
                "Use Browse to select manually.")
            return
        
        if len(found_paths) == 1:
            self.server_path.set(found_paths[0])
            messagebox.showinfo("Success", f"Found server at:\n{found_paths[0]}")
        else:
            # Show dialog to choose
            choice_window = tk.Toplevel(self)
            choice_window.title("Select Server Path")
            choice_window.geometry("600x300")
            
            ttk.Label(choice_window, text="Multiple server paths found. Select one:").pack(pady=10)
            
            listbox = tk.Listbox(choice_window, width=80, height=10)
            for path in found_paths:
                listbox.insert(tk.END, path)
            listbox.pack(pady=10, padx=10)
            
            def select_path():
                selection = listbox.curselection()
                if selection:
                    self.server_path.set(found_paths[selection[0]])
                    choice_window.destroy()
            
            ttk.Button(choice_window, text="Select", command=select_path).pack(pady=5)
            
    def add_scheduled_announcement(self):
        """Add a scheduled announcement"""
        dialog = tk.Toplevel(self)
        dialog.title("Add Scheduled Announcement")
        dialog.geometry("500x300")
        dialog.transient(self)
        dialog.grab_set()
        self.apply_dialog_theme(dialog)
        
        ttk.Label(dialog, text="Schedule Recurring Announcement", 
                 font=('TkDefaultFont', 10, 'bold')).pack(pady=10)
        
        # Message
        ttk.Label(dialog, text="Message:").pack(anchor=tk.W, padx=20)
        message_entry = ttk.Entry(dialog, width=60)
        message_entry.pack(padx=20, pady=5, fill=tk.X)
        
        # Interval
        ttk.Label(dialog, text="Repeat every:").pack(anchor=tk.W, padx=20, pady=(10, 0))
        
        interval_frame = ttk.Frame(dialog)
        interval_frame.pack(padx=20, pady=5)
        
        interval_spinbox = ttk.Spinbox(interval_frame, from_=1, to=999, width=10)
        interval_spinbox.insert(0, "30")
        interval_spinbox.pack(side=tk.LEFT, padx=5)
        
        unit_var = tk.StringVar(value="minutes")
        ttk.Radiobutton(interval_frame, text="Minutes", variable=unit_var, value="minutes").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(interval_frame, text="Hours", variable=unit_var, value="hours").pack(side=tk.LEFT, padx=5)
        
        def save_announcement():
            message = message_entry.get().strip()
            if not message:
                messagebox.showwarning("No Message", "Please enter a message")
                return
            
            interval_num = int(interval_spinbox.get())
            unit = unit_var.get()
            
            # Convert to seconds
            if unit == "minutes":
                interval_seconds = interval_num * 60
                interval_display = f"{interval_num} min"
            else:
                interval_seconds = interval_num * 3600
                interval_display = f"{interval_num} hr"
            
            task = {
                'type': 'announcement',
                'message': message,
                'interval': interval_seconds,
                'interval_display': interval_display,
                'enabled': True
            }
            
            self.scheduled_tasks.append(task)
            self.save_scheduled_tasks()
            self.refresh_scheduler_display()
            self.start_scheduled_task(len(self.scheduled_tasks) - 1)
            
            messagebox.showinfo("Success", f"Announcement scheduled every {interval_display}")
            dialog.destroy()
        
        ttk.Button(dialog, text="Add Announcement", command=save_announcement).pack(pady=20)
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).pack()
    
    def add_scheduled_command(self):
        """Add a scheduled command"""
        dialog = tk.Toplevel(self)
        dialog.title("Add Scheduled Command")
        dialog.geometry("500x350")
        dialog.transient(self)
        dialog.grab_set()
        self.apply_dialog_theme(dialog)
        
        ttk.Label(dialog, text="Schedule Recurring RCON Command", 
                 font=('TkDefaultFont', 10, 'bold')).pack(pady=10)
        
        # Command
        ttk.Label(dialog, text="RCON Command:").pack(anchor=tk.W, padx=20)
        command_entry = ttk.Entry(dialog, width=60)
        command_entry.pack(padx=20, pady=5, fill=tk.X)
        
        ttk.Label(dialog, text="Examples: save, players, servermsg \"Server saving...\"", 
                 font=('TkDefaultFont', 8), foreground='gray').pack(padx=20)
        
        # Interval
        ttk.Label(dialog, text="Repeat every:").pack(anchor=tk.W, padx=20, pady=(10, 0))
        
        interval_frame = ttk.Frame(dialog)
        interval_frame.pack(padx=20, pady=5)
        
        interval_spinbox = ttk.Spinbox(interval_frame, from_=1, to=999, width=10)
        interval_spinbox.insert(0, "60")
        interval_spinbox.pack(side=tk.LEFT, padx=5)
        
        unit_var = tk.StringVar(value="minutes")
        ttk.Radiobutton(interval_frame, text="Minutes", variable=unit_var, value="minutes").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(interval_frame, text="Hours", variable=unit_var, value="hours").pack(side=tk.LEFT, padx=5)
        
        def save_command():
            command = command_entry.get().strip()
            if not command:
                messagebox.showwarning("No Command", "Please enter a command")
                return
            
            interval_num = int(interval_spinbox.get())
            unit = unit_var.get()
            
            # Convert to seconds
            if unit == "minutes":
                interval_seconds = interval_num * 60
                interval_display = f"{interval_num} min"
            else:
                interval_seconds = interval_num * 3600
                interval_display = f"{interval_num} hr"
            
            task = {
                'type': 'command',
                'command': command,
                'interval': interval_seconds,
                'interval_display': interval_display,
                'enabled': True
            }
            
            self.scheduled_tasks.append(task)
            self.save_scheduled_tasks()
            self.refresh_scheduler_display()
            self.start_scheduled_task(len(self.scheduled_tasks) - 1)
            
            messagebox.showinfo("Success", f"Command scheduled every {interval_display}")
            dialog.destroy()
        
        ttk.Button(dialog, text="Add Command", command=save_command).pack(pady=20)
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).pack()
    
    def refresh_scheduler_display(self):
        """Refresh the scheduler task list"""
        for item in self.scheduler_tree.get_children():
            self.scheduler_tree.delete(item)
        
        for i, task in enumerate(self.scheduled_tasks):
            task_type = task['type'].title()
            interval = task['interval_display']
            
            if task['type'] == 'announcement':
                content = task['message'][:50] + "..." if len(task['message']) > 50 else task['message']
            else:
                content = task['command'][:50] + "..." if len(task['command']) > 50 else task['command']
            
            status = "Enabled" if task['enabled'] else "Disabled"
            
            self.scheduler_tree.insert('', tk.END, text=str(i+1), 
                                      values=(task_type, interval, content, status))
    
    def enable_scheduled_task(self):
        """Enable selected task"""
        selection = self.scheduler_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a task")
            return
        
        item = selection[0]
        index = int(self.scheduler_tree.item(item)['text']) - 1
        
        self.scheduled_tasks[index]['enabled'] = True
        self.save_scheduled_tasks()
        self.refresh_scheduler_display()
        self.start_scheduled_task(index)
        
        messagebox.showinfo("Success", "Task enabled")
    
    def disable_scheduled_task(self):
        """Disable selected task"""
        selection = self.scheduler_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a task")
            return
        
        item = selection[0]
        index = int(self.scheduler_tree.item(item)['text']) - 1
        
        self.scheduled_tasks[index]['enabled'] = False
        self.save_scheduled_tasks()
        self.refresh_scheduler_display()
        self.stop_scheduled_task(index)
        
        messagebox.showinfo("Success", "Task disabled")
    
    def remove_scheduled_task(self):
        """Remove selected task"""
        selection = self.scheduler_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a task")
            return
        
        item = selection[0]
        index = int(self.scheduler_tree.item(item)['text']) - 1
        
        if messagebox.askyesno("Confirm Remove", "Remove this scheduled task?"):
            self.stop_scheduled_task(index)
            del self.scheduled_tasks[index]
            self.save_scheduled_tasks()
            self.refresh_scheduler_display()
            messagebox.showinfo("Success", "Task removed")
    
    def start_scheduled_task(self, index):
        """Start a scheduled task timer"""
        if index in self.scheduler_timers:
            return  # Already running
        
        task = self.scheduled_tasks[index]
        if not task['enabled']:
            return
        
        def execute_task():
            if not task['enabled']:
                return
            
            try:
                if task['type'] == 'announcement':
                    if self.rcon:
                        cmd = f'servermsg "{task["message"]}"'
                        self.rcon.execute_command(cmd)
                        self.log_command_output(f"[Scheduled] Announcement: {task['message']}")
                elif task['type'] == 'command':
                    if self.rcon:
                        self.rcon.execute_command(task['command'])
                        self.log_command_output(f"[Scheduled] Command: {task['command']}")
            except Exception as e:
                self.log_command_output(f"[Scheduled Task Error] {str(e)}")
            
            # Reschedule
            if task['enabled']:
                timer_id = self.after(task['interval'] * 1000, execute_task)
                self.scheduler_timers[index] = timer_id
        
        # Start first execution
        timer_id = self.after(task['interval'] * 1000, execute_task)
        self.scheduler_timers[index] = timer_id
    
    def stop_scheduled_task(self, index):
        """Stop a scheduled task timer"""
        if index in self.scheduler_timers:
            self.after_cancel(self.scheduler_timers[index])
            del self.scheduler_timers[index]
    
    def save_scheduled_tasks(self):
        """Save scheduled tasks to file"""
        try:
            config_file = Path.home() / '.pz_admin_tool_scheduler.json'
            with open(config_file, 'w') as f:
                json.dump(self.scheduled_tasks, f, indent=2)
        except Exception as e:
            print(f"Failed to save scheduled tasks: {e}")
    
    def load_scheduled_tasks(self):
        """Load scheduled tasks from file"""
        try:
            config_file = Path.home() / '.pz_admin_tool_scheduler.json'
            if config_file.exists():
                with open(config_file, 'r') as f:
                    self.scheduled_tasks = json.load(f)
                
                # Start enabled tasks
                for i, task in enumerate(self.scheduled_tasks):
                    if task['enabled']:
                        self.start_scheduled_task(i)
                
                self.refresh_scheduler_display()
        except Exception as e:
            print(f"Failed to load scheduled tasks: {e}")
            self.scheduled_tasks = []
    
    def save_config(self):
        """Save configuration to file"""
        config = {
            'host': self.host_entry.get(),
            'port': self.port_entry.get(),
            'password': self.password_entry.get(),
            'server_path': self.server_path.get()
        }
        
        try:
            with open('pz_admin_config.json', 'w') as f:
                json.dump(config, f, indent=4)
            messagebox.showinfo("Success", "Configuration saved!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save config: {str(e)}")
            
    def load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists('pz_admin_config.json'):
                with open('pz_admin_config.json', 'r') as f:
                    config = json.load(f)
                
                self.host_entry.delete(0, tk.END)
                self.host_entry.insert(0, config.get('host', 'localhost'))
                
                self.port_entry.delete(0, tk.END)
                self.port_entry.insert(0, config.get('port', '16261'))
                
                self.password_entry.delete(0, tk.END)
                self.password_entry.insert(0, config.get('password', ''))
                
                self.server_path.set(config.get('server_path', ''))
        except (IOError, OSError, json.JSONDecodeError):
            pass  # Use defaults if can't load config
    
    def open_settings_editor(self):
        """Open the settings editor window"""
        if not self.server_path.get() or not os.path.exists(self.server_path.get()):
            messagebox.showwarning("No Server Path", "Please set the server path first")
            return
        
        # Try to auto-detect config files
        server_path = Path(self.server_path.get())
        
        # Search for .ini files
        ini_files = []
        server_dir = server_path / 'Server'
        if server_dir.exists():
            ini_files = list(server_dir.glob('*.ini'))
        
        # Search for _SandboxVars.lua files
        lua_files = []
        if server_dir.exists():
            lua_files = list(server_dir.glob('*_SandboxVars.lua'))
        
        # Show file selection dialog
        FileSelectionDialog(self, server_path, ini_files, lua_files)


class FileSelectionDialog(tk.Toplevel):
    """Dialog to select config files before opening settings editor"""
    
    def __init__(self, parent, server_path, ini_files, lua_files):
        super().__init__(parent)
        self.parent = parent
        self.server_path = server_path
        self.ini_files = ini_files
        self.lua_files = lua_files
        
        self.title("Select Configuration Files")
        self.geometry("700x500")  # Increased from 600x400
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        # Apply theme
        if hasattr(parent, 'current_theme'):
            theme = parent.current_theme.get()
            if theme == "dark":
                self.configure(bg="#2b2b2b")
            else:
                self.configure(bg="#f5f5f5")
        
        self.selected_ini = None
        self.selected_lua = None
        
        self.create_ui()
    
    def create_ui(self):
        """Create the file selection UI"""
        # Header
        header = ttk.Label(self, text="Select your server configuration files:", 
                          font=('TkDefaultFont', 10, 'bold'))
        header.pack(pady=10)
        
        # INI File Selection
        ini_frame = ttk.LabelFrame(self, text="Server INI File (Required)", padding=10)
        ini_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        if self.ini_files:
            ttk.Label(ini_frame, text="Found .ini files:").pack(anchor=tk.W, pady=5)
            
            self.ini_var = tk.StringVar(value=str(self.ini_files[0]))
            for ini_file in self.ini_files:
                ttk.Radiobutton(ini_frame, text=ini_file.name, 
                               variable=self.ini_var, value=str(ini_file)).pack(anchor=tk.W, padx=10)
        else:
            ttk.Label(ini_frame, text="No .ini files found in Server directory.", 
                     foreground='red').pack(pady=5)
        
        ttk.Button(ini_frame, text="Browse for .ini file...", 
                  command=self.browse_ini).pack(pady=5)
        
        # LUA File Selection
        lua_frame = ttk.LabelFrame(self, text="Sandbox Variables LUA File (Optional)", padding=10)
        lua_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        if self.lua_files:
            ttk.Label(lua_frame, text="Found _SandboxVars.lua files:").pack(anchor=tk.W, pady=5)
            
            self.lua_var = tk.StringVar(value=str(self.lua_files[0]))
            for lua_file in self.lua_files:
                ttk.Radiobutton(lua_frame, text=lua_file.name, 
                               variable=self.lua_var, value=str(lua_file)).pack(anchor=tk.W, padx=10)
        else:
            ttk.Label(lua_frame, text="No _SandboxVars.lua files found.", 
                     foreground='orange').pack(pady=5)
        
        ttk.Button(lua_frame, text="Browse for .lua file...", 
                  command=self.browse_lua).pack(pady=5)
        
        # Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(btn_frame, text="Open Settings Editor", 
                  command=self.open_editor).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", 
                  command=self.destroy).pack(side=tk.RIGHT, padx=5)
    
    def browse_ini(self):
        """Browse for .ini file manually"""
        from tkinter import filedialog
        filename = filedialog.askopenfilename(
            title="Select Server .ini File",
            initialdir=self.server_path / 'Server' if (self.server_path / 'Server').exists() else self.server_path,
            filetypes=[("INI files", "*.ini"), ("All files", "*.*")]
        )
        if filename:
            self.ini_var = tk.StringVar(value=filename)
            messagebox.showinfo("File Selected", f"Selected: {Path(filename).name}")
    
    def browse_lua(self):
        """Browse for .lua file manually"""
        from tkinter import filedialog
        filename = filedialog.askopenfilename(
            title="Select SandboxVars .lua File",
            initialdir=self.server_path / 'Server' if (self.server_path / 'Server').exists() else self.server_path,
            filetypes=[("LUA files", "*.lua"), ("All files", "*.*")]
        )
        if filename:
            self.lua_var = tk.StringVar(value=filename)
            messagebox.showinfo("File Selected", f"Selected: {Path(filename).name}")
    
    def open_editor(self):
        """Open the settings editor with selected files"""
        # Get selected files
        ini_file = None
        lua_file = None
        
        if hasattr(self, 'ini_var') and self.ini_var.get():
            ini_file = Path(self.ini_var.get())
        
        if hasattr(self, 'lua_var') and self.lua_var.get():
            lua_file = Path(self.lua_var.get())
        
        if not ini_file or not ini_file.exists():
            messagebox.showerror("Error", "Please select a valid .ini file")
            return
        
        # Close this dialog
        self.destroy()
        
        # Open settings editor
        SettingsEditorWindow(self.parent, self.server_path, ini_file, lua_file)


class SettingsEditorWindow(tk.Toplevel):
    """Separate window for editing server settings"""
    
    def __init__(self, parent, server_path, ini_file, lua_file):
        super().__init__(parent)
        self.parent = parent
        self.server_path = Path(server_path)
        self.ini_file = ini_file
        self.lua_file = lua_file
        
        self.title(f"Server Settings Editor - {ini_file.name if ini_file else 'No File'}")
        self.geometry("900x700")  # Increased from 800x600
        
        # Apply theme from parent
        if hasattr(parent, 'current_theme'):
            theme = parent.current_theme.get()
            if theme == "dark":
                self.configure(bg="#2b2b2b")
            else:
                self.configure(bg="#f5f5f5")
        
        # Store original values for comparison
        self.original_values = {}
        self.settings = {}
        
        if not self.ini_file or not self.ini_file.exists():
            messagebox.showerror("Error", "Invalid .ini file")
            self.destroy()
            return
        
        # Create UI
        self.create_ui()
        self.load_settings()
    
    def get_canvas_bg(self):
        """Get canvas background color based on theme"""
        if hasattr(self.parent, 'current_theme'):
            theme = self.parent.current_theme.get()
            if theme == "dark":
                return "#2b2b2b"
        return "#f5f5f5"
    
    def get_text_colors(self):
        """Get text widget colors based on theme"""
        theme = self.current_theme.get()
        if theme == "dark":
            return {
                'bg': "#404040",
                'fg': "#ffffff",
                'insertbackground': "#ffffff",
                'selectbackground': "#505050",
                'selectforeground': "#ffffff"
            }
        else:
            return {
                'bg': "#ffffff",
                'fg': "#000000",
                'insertbackground': "#000000",
                'selectbackground': "#0078d7",
                'selectforeground': "#ffffff"
            }
    
    def create_ui(self):
        """Create the settings editor UI"""
        # Notebook for categories
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Basic Server Settings
        basic_frame = ttk.Frame(notebook)
        notebook.add(basic_frame, text="Basic Server")
        self.create_basic_settings(basic_frame)
        
        # Gameplay Settings
        gameplay_frame = ttk.Frame(notebook)
        notebook.add(gameplay_frame, text="Gameplay")
        self.create_gameplay_settings(gameplay_frame)
        
        # Zombie Settings
        zombie_frame = ttk.Frame(notebook)
        notebook.add(zombie_frame, text="Zombies")
        self.create_zombie_settings(zombie_frame)
        
        # Advanced Settings
        advanced_frame = ttk.Frame(notebook)
        notebook.add(advanced_frame, text="Advanced")
        self.create_advanced_settings(advanced_frame)
        
        # Loot Details
        loot_frame = ttk.Frame(notebook)
        notebook.add(loot_frame, text="Loot Details")
        self.create_loot_details_settings(loot_frame)
        
        # World & Environment
        world_frame = ttk.Frame(notebook)
        notebook.add(world_frame, text="World & Environment")
        self.create_world_settings(world_frame)
        
        # Vehicles
        vehicles_frame = ttk.Frame(notebook)
        notebook.add(vehicles_frame, text="Vehicles")
        self.create_vehicles_settings(vehicles_frame)
        
        # Survival & Health
        survival_frame = ttk.Frame(notebook)
        notebook.add(survival_frame, text="Survival & Health")
        self.create_survival_settings(survival_frame)
        
        # Buttons at bottom
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(btn_frame, text="Save Changes", command=self.save_settings, 
                  style='Accent.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Reload", command=self.load_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="View Raw Files", command=self.view_raw_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Close", command=self.destroy).pack(side=tk.RIGHT, padx=5)
    
    def create_basic_settings(self, parent):
        """Create basic server settings controls"""
        canvas = tk.Canvas(parent, bg=self.get_canvas_bg(), highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Server Name
        self.add_text_setting(scrollable_frame, 'PublicName', 'Server Name:', 0)
        
        # Description
        self.add_text_setting(scrollable_frame, 'PublicDescription', 'Description:', 1)
        
        # Password
        self.add_text_setting(scrollable_frame, 'Password', 'Server Password:', 2)
        
        # Max Players
        self.add_number_setting(scrollable_frame, 'MaxPlayers', 'Max Players:', 3, 1, 100)
        
        # Public Server
        self.add_bool_setting(scrollable_frame, 'Public', 'Public Server:', 4)
        
        # Open Server
        self.add_bool_setting(scrollable_frame, 'Open', 'Open (No Whitelist):', 5)
        
        # PVP
        self.add_bool_setting(scrollable_frame, 'PVP', 'PVP Enabled:', 6)
        
        # Pause When Empty
        self.add_bool_setting(scrollable_frame, 'PauseEmpty', 'Pause When Empty:', 7)
        
        # Global Chat
        self.add_bool_setting(scrollable_frame, 'GlobalChat', 'Global Chat:', 8)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_gameplay_settings(self, parent):
        """Create gameplay settings controls"""
        canvas = tk.Canvas(parent, bg=self.get_canvas_bg(), highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        row = 0
        
        # Day Length (from SandboxVars.lua)
        self.add_choice_setting(scrollable_frame, 'DayLength', 'Day Length:', row, {
            '15 Minutes': 1, '30 Minutes': 2, '1 Hour': 3, '1 Hour 30 Min': 4,
            '2 Hours': 5, '3 Hours': 6, '4 Hours': 7, '5 Hours': 8
        }, is_lua=True)
        row += 1
        
        # Start Month
        self.add_choice_setting(scrollable_frame, 'StartMonth', 'Start Month:', row, {
            'January': 1, 'February': 2, 'March': 3, 'April': 4,
            'May': 5, 'June': 6, 'July': 7, 'August': 8,
            'September': 9, 'October': 10, 'November': 11, 'December': 12
        }, is_lua=True)
        row += 1
        
        # Start Day
        self.add_number_setting(scrollable_frame, 'StartDay', 'Start Day:', row, 1, 31, is_lua=True)
        row += 1
        
        # Start Time
        self.add_choice_setting(scrollable_frame, 'StartTime', 'Start Time:', row, {
            '7 AM': 1, '9 AM': 2, '12 PM': 3, '2 PM': 4,
            '5 PM': 5, '9 PM': 6, '12 AM': 7, '2 AM': 8, '5 AM': 9
        }, is_lua=True)
        row += 1
        
        # Water Shutoff
        self.add_choice_setting(scrollable_frame, 'WaterShut', 'Water Shutoff:', row, {
            'Instant': 1, '0-30 Days': 2, '0-2 Months': 3, '0-6 Months': 4,
            '0-1 Year': 5, '0-5 Years': 6, '2-6 Months': 7, '6-12 Months': 8, 'Never': 9
        }, is_lua=True)
        row += 1
        
        # Electricity Shutoff
        self.add_choice_setting(scrollable_frame, 'ElecShut', 'Electricity Shutoff:', row, {
            'Instant': 1, '0-30 Days': 2, '0-2 Months': 3, '0-6 Months': 4,
            '0-1 Year': 5, '0-5 Years': 6, '2-6 Months': 7, '6-12 Months': 8, 'Never': 9
        }, is_lua=True)
        row += 1
        
        # Loot Respawn
        self.add_bool_setting(scrollable_frame, 'LootRespawn', 'Loot Respawn:', row, is_lua=True)
        row += 1
        
        # Loot Abundance
        self.add_choice_setting(scrollable_frame, 'LootAbundance', 'Loot Abundance:', row, {
            'Extremely Rare': 1, 'Rare': 2, 'Normal': 3, 'Abundant': 4, 'Extremely Abundant': 5
        }, is_lua=True)
        row += 1
        
        # Food Loot
        self.add_choice_setting(scrollable_frame, 'FoodLoot', 'Food Loot:', row, {
            'Extremely Rare': 1, 'Rare': 2, 'Normal': 3, 'Abundant': 4, 'Extremely Abundant': 5
        }, is_lua=True)
        row += 1
        
        # Weapon Loot
        self.add_choice_setting(scrollable_frame, 'WeaponLoot', 'Weapon Loot:', row, {
            'Extremely Rare': 1, 'Rare': 2, 'Normal': 3, 'Abundant': 4, 'Extremely Abundant': 5
        }, is_lua=True)
        row += 1
        
        # Other Loot
        self.add_choice_setting(scrollable_frame, 'OtherLoot', 'Other Loot:', row, {
            'Extremely Rare': 1, 'Rare': 2, 'Normal': 3, 'Abundant': 4, 'Extremely Abundant': 5
        }, is_lua=True)
        row += 1
        
        # XP Multiplier
        self.add_choice_setting(scrollable_frame, 'XpMultiplier', 'XP Multiplier:', row, {
            '0.25x': 0.25, '0.5x': 0.5, '0.75x': 0.75, '1x (Normal)': 1.0,
            '1.5x': 1.5, '2x': 2.0, '3x': 3.0, '4x': 4.0, '5x': 5.0
        }, is_lua=True)
        row += 1
        
        # Farming Speed
        self.add_choice_setting(scrollable_frame, 'FarmingSpeed', 'Farming Speed:', row, {
            'Very Fast': 1, 'Fast': 2, 'Normal': 3, 'Slow': 4, 'Very Slow': 5
        }, is_lua=True)
        row += 1
        
        # Nature Abundance
        self.add_choice_setting(scrollable_frame, 'NatureAbundance', 'Nature Abundance (Foraging):', row, {
            'Very Poor': 1, 'Poor': 2, 'Normal': 3, 'Abundant': 4, 'Very Abundant': 5
        }, is_lua=True)
        row += 1
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_zombie_settings(self, parent):
        """Create zombie settings controls"""
        canvas = tk.Canvas(parent, bg=self.get_canvas_bg(), highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        row = 0
        
        # Zombie Population
        self.add_choice_setting(scrollable_frame, 'Zombies', 'Zombie Population:', row, {
            'Insane': 1, 'Very High': 2, 'High': 3, 'Normal': 4, 'Low': 5, 'None': 6
        }, is_lua=True)
        row += 1
        
        # Zombie Respawn
        self.add_choice_setting(scrollable_frame, 'ZombieRespawn', 'Zombie Respawn:', row, {
            'High': 1, 'Normal': 2, 'Low': 3, 'None': 4
        }, is_lua=True)
        row += 1
        
        # Zombie Migration
        self.add_bool_setting(scrollable_frame, 'ZombieMigrate', 'Zombie Migration:', row, is_lua=True)
        row += 1
        
        # Zombie Speed
        self.add_choice_setting(scrollable_frame, 'Speed', 'Zombie Speed:', row, {
            'Sprinters': 1, 'Fast Shamblers': 2, 'Shamblers': 3, 'Random': 4
        }, is_lua=True)
        row += 1
        
        # Zombie Strength
        self.add_choice_setting(scrollable_frame, 'Strength', 'Zombie Strength:', row, {
            'Superhuman': 1, 'Normal': 2, 'Weak': 3, 'Random': 4
        }, is_lua=True)
        row += 1
        
        # Zombie Toughness
        self.add_choice_setting(scrollable_frame, 'Toughness', 'Zombie Toughness:', row, {
            'Tough': 1, 'Normal': 2, 'Fragile': 3, 'Random': 4
        }, is_lua=True)
        row += 1
        
        # Zombie Transmission
        self.add_choice_setting(scrollable_frame, 'Transmission', 'Infection Transmission:', row, {
            'Blood + Saliva': 1, 'Saliva Only': 2, 'Everyone Infected': 3, 'None': 4
        }, is_lua=True)
        row += 1
        
        # Zombie Mortality
        self.add_choice_setting(scrollable_frame, 'Mortality', 'Infection Mortality:', row, {
            'Instant': 1, '0-30 Seconds': 2, '0-1 Minutes': 3, '0-12 Hours': 4,
            '2-3 Days': 5, '1-2 Weeks': 6, 'Never': 7
        }, is_lua=True)
        row += 1
        
        # Zombie Reanimate Time
        self.add_choice_setting(scrollable_frame, 'Reanimate', 'Reanimate Time:', row, {
            'Instant': 1, '0-30 Seconds': 2, '0-1 Minutes': 3, '0-12 Hours': 4,
            '2-3 Days': 5
        }, is_lua=True)
        row += 1
        
        # Zombie Cognition
        self.add_choice_setting(scrollable_frame, 'Cognition', 'Zombie Cognition:', row, {
            'Navigate + Use Doors': 1, 'Navigate': 2, 'Basic Navigation': 3, 'Random': 4
        }, is_lua=True)
        row += 1
        
        # Zombie Memory
        self.add_choice_setting(scrollable_frame, 'Memory', 'Zombie Memory:', row, {
            'Long': 1, 'Normal': 2, 'Short': 3, 'None': 4, 'Random': 5, 'Random (Normal-None)': 6
        }, is_lua=True)
        row += 1
        
        # Zombie Sight
        self.add_choice_setting(scrollable_frame, 'Sight', 'Zombie Sight:', row, {
            'Eagle': 1, 'Normal': 2, 'Poor': 3, 'Random': 4, 'Random (Normal-Poor)': 5
        }, is_lua=True)
        row += 1
        
        # Zombie Hearing
        self.add_choice_setting(scrollable_frame, 'Hearing', 'Zombie Hearing:', row, {
            'Pinpoint': 1, 'Normal': 2, 'Poor': 3, 'Random': 4, 'Random (Normal-Poor)': 5
        }, is_lua=True)
        row += 1
        
        # Zombie Active Time
        self.add_choice_setting(scrollable_frame, 'ActiveOnly', 'Zombies Active:', row, {
            'Both': 1, 'Night': 2, 'Day': 3
        }, is_lua=True)
        row += 1
        
        # Crawl Under Vehicle
        self.add_choice_setting(scrollable_frame, 'CrawlUnderVehicle', 'Crawl Under Vehicles:', row, {
            'Crawlers Only': 1, 'Extremely Rare': 2, 'Rare': 3, 'Sometimes': 4,
            'Often': 5, 'Very Often': 6, 'Always': 7
        }, is_lua=True)
        row += 1
        
        # Distribution
        self.add_choice_setting(scrollable_frame, 'Distribution', 'Zombie Distribution:', row, {
            'Urban Focused': 1, 'Uniform': 2
        }, is_lua=True)
        row += 1
        
        ttk.Separator(scrollable_frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky='ew', pady=10)
        row += 1
        
        ttk.Label(scrollable_frame, text="Advanced Zombie Options", 
                 font=('TkDefaultFont', 9, 'bold')).grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # Spotted Logic (stealth)
        self.add_bool_setting(scrollable_frame, 'SpottedLogic', 'Advanced Stealth Mechanics:', row, is_lua=True)
        row += 1
        
        # Thump No Chasing
        self.add_bool_setting(scrollable_frame, 'ThumpNoChasing', 'Attack Doors While Roaming:', row, is_lua=True)
        row += 1
        
        # Thump On Construction
        self.add_bool_setting(scrollable_frame, 'ThumpOnConstruction', 'Destroy Player Constructions:', row, is_lua=True)
        row += 1
        
        # Trigger House Alarm
        self.add_bool_setting(scrollable_frame, 'TriggerHouseAlarm', 'Trigger House Alarms:', row, is_lua=True)
        row += 1
        
        # Zombies Drag Down
        self.add_bool_setting(scrollable_frame, 'ZombiesDragDown', 'Can Drag Down Player:', row, is_lua=True)
        row += 1
        
        # Crawlers Drag Down
        self.add_bool_setting(scrollable_frame, 'ZombiesCrawlersDragDown', 'Crawlers Can Drag Down:', row, is_lua=True)
        row += 1
        
        # Fence Lunge
        self.add_bool_setting(scrollable_frame, 'ZombiesFenceLunge', 'Fence/Window Lunge:', row, is_lua=True)
        row += 1
        
        # Fake Dead
        self.add_choice_setting(scrollable_frame, 'DisableFakeDead', 'Fake Dead Zombies:', row, {
            'World Zombies': 1, 'World and Combat': 2, 'Never': 3
        }, is_lua=True)
        row += 1
        
        # Sprinter Percentage (for random speed)
        self.add_slider_setting(scrollable_frame, 'SprinterPercentage', 'Sprinter % (if Random Speed):', row, 0, 100, 1, is_lua=True)
        row += 1
        
        # Zombie Armor Factor
        self.add_slider_setting(scrollable_frame, 'ZombiesArmorFactor', 'Zombie Armor Effectiveness:', row, 0, 100, 0.1, is_lua=True)
        row += 1
        
        # Zombie Max Defense
        self.add_number_setting(scrollable_frame, 'ZombiesMaxDefense', 'Max Zombie Defense %:', row, 0, 100, is_lua=True)
        row += 1
        
        # Chance of Attached Weapon
        self.add_number_setting(scrollable_frame, 'ChanceOfAttachedWeapon', 'Attached Weapon Chance %:', row, 0, 100, is_lua=True)
        row += 1
        
        # Zombie Fall Damage
        self.add_slider_setting(scrollable_frame, 'ZombiesFallDamage', 'Zombie Fall Damage Multiplier:', row, 0, 100, 0.1, is_lua=True)
        row += 1
        
        # Player Spawn Zombie Removal
        self.add_choice_setting(scrollable_frame, 'PlayerSpawnZombieRemoval', 'Zombie-Free Spawn Area:', row, {
            'Building + Around': 1, 'Inside Building': 2, 'Inside Room': 3, 'Spawn Anywhere': 4
        }, is_lua=True)
        row += 1
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_advanced_settings(self, parent):
        """Create advanced settings controls"""
        canvas = tk.Canvas(parent, bg=self.get_canvas_bg(), highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # RCON Port
        self.add_number_setting(scrollable_frame, 'RCONPort', 'RCON Port:', 0, 0, 65535)
        
        # Default Port
        self.add_number_setting(scrollable_frame, 'DefaultPort', 'Default Port:', 1, 0, 65535)
        
        # UDP Port
        self.add_number_setting(scrollable_frame, 'UDPPort', 'UDP Port:', 2, 0, 65535)
        
        # Ping Limit
        self.add_number_setting(scrollable_frame, 'PingLimit', 'Ping Limit (ms):', 3, 0, 10000)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_loot_details_settings(self, parent):
        """Create detailed loot category settings"""
        canvas = tk.Canvas(parent, bg=self.get_canvas_bg(), highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        row = 0
        
        ttk.Label(scrollable_frame, text="Loot Abundance by Category (0.0 = None, 4.0 = Maximum)",
                 font=('TkDefaultFont', 9, 'bold')).grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=5, pady=10)
        row += 1
        
        # All detailed loot categories
        self.add_slider_setting(scrollable_frame, 'FoodLootNew', 'Food (Fresh):', row, 0, 4, 0.1, is_lua=True)
        row += 1
        self.add_slider_setting(scrollable_frame, 'CannedFoodLootNew', 'Canned Food:', row, 0, 4, 0.1, is_lua=True)
        row += 1
        self.add_slider_setting(scrollable_frame, 'LiteratureLootNew', 'Literature (Books, Magazines):', row, 0, 4, 0.1, is_lua=True)
        row += 1
        self.add_slider_setting(scrollable_frame, 'MedicalLootNew', 'Medical Supplies:', row, 0, 4, 0.1, is_lua=True)
        row += 1
        self.add_slider_setting(scrollable_frame, 'SurvivalGearsLootNew', 'Survival Gear (Camping):', row, 0, 4, 0.1, is_lua=True)
        row += 1
        self.add_slider_setting(scrollable_frame, 'WeaponLootNew', 'Weapons (Melee):', row, 0, 4, 0.1, is_lua=True)
        row += 1
        self.add_slider_setting(scrollable_frame, 'RangedWeaponLootNew', 'Ranged Weapons & Attachments:', row, 0, 4, 0.1, is_lua=True)
        row += 1
        self.add_slider_setting(scrollable_frame, 'AmmoLootNew', 'Ammunition:', row, 0, 4, 0.1, is_lua=True)
        row += 1
        self.add_slider_setting(scrollable_frame, 'MechanicsLootNew', 'Mechanics & Car Parts:', row, 0, 4, 0.1, is_lua=True)
        row += 1
        self.add_slider_setting(scrollable_frame, 'ClothingLootNew', 'Clothing:', row, 0, 4, 0.1, is_lua=True)
        row += 1
        self.add_slider_setting(scrollable_frame, 'ContainerLootNew', 'Containers (Bags):', row, 0, 4, 0.1, is_lua=True)
        row += 1
        self.add_slider_setting(scrollable_frame, 'KeyLootNew', 'Keys & Locks:', row, 0, 4, 0.1, is_lua=True)
        row += 1
        self.add_slider_setting(scrollable_frame, 'MediaLootNew', 'Media (VHS, CDs):', row, 0, 4, 0.1, is_lua=True)
        row += 1
        self.add_slider_setting(scrollable_frame, 'MementoLootNew', 'Mementos (Collectibles):', row, 0, 4, 0.1, is_lua=True)
        row += 1
        self.add_slider_setting(scrollable_frame, 'CookwareLootNew', 'Cookware:', row, 0, 4, 0.1, is_lua=True)
        row += 1
        self.add_slider_setting(scrollable_frame, 'MaterialLootNew', 'Materials (Crafting):', row, 0, 4, 0.1, is_lua=True)
        row += 1
        self.add_slider_setting(scrollable_frame, 'FarmingLootNew', 'Farming Tools:', row, 0, 4, 0.1, is_lua=True)
        row += 1
        self.add_slider_setting(scrollable_frame, 'ToolLootNew', 'Tools (General):', row, 0, 4, 0.1, is_lua=True)
        row += 1
        self.add_slider_setting(scrollable_frame, 'OtherLootNew', 'Other Items:', row, 0, 4, 0.1, is_lua=True)
        row += 1
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_world_settings(self, parent):
        """Create world and environment settings"""
        canvas = tk.Canvas(parent, bg=self.get_canvas_bg(), highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        row = 0
        
        # Day/Night Cycle
        self.add_choice_setting(scrollable_frame, 'DayNightCycle', 'Day/Night Cycle:', row, {
            'Normal': 1, 'Endless Day': 2, 'Endless Night': 3
        }, is_lua=True)
        row += 1
        
        # Climate Cycle
        self.add_choice_setting(scrollable_frame, 'ClimateCycle', 'Weather Cycle:', row, {
            'Normal': 1, 'No Weather': 2, 'Endless Rain': 3, 'Endless Storm': 4,
            'Endless Snow': 5, 'Endless Blizzard': 6
        }, is_lua=True)
        row += 1
        
        # Fog Cycle
        self.add_choice_setting(scrollable_frame, 'FogCycle', 'Fog Cycle:', row, {
            'Normal': 1, 'No Fog': 2, 'Endless Fog': 3
        }, is_lua=True)
        row += 1
        
        # Temperature
        self.add_choice_setting(scrollable_frame, 'Temperature', 'Temperature:', row, {
            'Very Cold': 1, 'Cold': 2, 'Normal': 3, 'Hot': 4
        }, is_lua=True)
        row += 1
        
        # Rain
        self.add_choice_setting(scrollable_frame, 'Rain', 'Rain Amount:', row, {
            'Very Dry': 1, 'Dry': 2, 'Normal': 3, 'Rainy': 4, 'Very Rainy': 5
        }, is_lua=True)
        row += 1
        
        # Erosion
        self.add_choice_setting(scrollable_frame, 'ErosionSpeed', 'Erosion Speed:', row, {
            'Very Fast (20 Days)': 1, 'Fast (50 Days)': 2, 'Normal (100 Days)': 3,
            'Slow (200 Days)': 4, 'Very Slow (500 Days)': 5, 'None': 6
        }, is_lua=True)
        row += 1
        
        # Locked Houses
        self.add_choice_setting(scrollable_frame, 'LockedHouses', 'Locked Houses:', row, {
            'None': 1, 'Very Low': 2, 'Low': 3, 'Normal': 4, 'High': 5, 'Very High': 6
        }, is_lua=True)
        row += 1
        
        # Alarm Frequency
        self.add_choice_setting(scrollable_frame, 'Alarm', 'House Alarms:', row, {
            'Never': 1, 'Extremely Rare': 2, 'Rare': 3, 'Sometimes': 4, 'Often': 5, 'Very Often': 6
        }, is_lua=True)
        row += 1
        
        # Fire Spread
        self.add_bool_setting(scrollable_frame, 'FireSpread', 'Fire Spreads:', row, is_lua=True)
        row += 1
        
        # Max Fog Intensity
        self.add_choice_setting(scrollable_frame, 'MaxFogIntensity', 'Max Fog Intensity:', row, {
            'Normal': 1, 'Moderate': 2, 'Dense': 3
        }, is_lua=True)
        row += 1
        
        # Max Rain Intensity
        self.add_choice_setting(scrollable_frame, 'MaxRainFxIntensity', 'Max Rain Intensity:', row, {
            'Normal': 1, 'Moderate': 2, 'Heavy': 3
        }, is_lua=True)
        row += 1
        
        # Snow on Ground
        self.add_bool_setting(scrollable_frame, 'EnableSnowOnGround', 'Snow on Ground:', row, is_lua=True)
        row += 1
        
        # Survivor Houses
        self.add_choice_setting(scrollable_frame, 'SurvivorHouseChance', 'Survivor House Chance:', row, {
            'Never': 1, 'Extremely Rare': 2, 'Rare': 3, 'Sometimes': 4, 'Often': 5, 'Very Often': 6
        }, is_lua=True)
        row += 1
        
        # Annotated Map Chance
        self.add_choice_setting(scrollable_frame, 'AnnotatedMapChance', 'Annotated Map Chance:', row, {
            'Never': 1, 'Extremely Rare': 2, 'Rare': 3, 'Sometimes': 4, 'Often': 5, 'Always': 6
        }, is_lua=True)
        row += 1
        
        # Generator Spawning
        self.add_choice_setting(scrollable_frame, 'GeneratorSpawning', 'Generator Spawning:', row, {
            'Extremely Rare': 1, 'Rare': 2, 'Sometimes': 3, 'Often': 4, 'Very Often': 5
        }, is_lua=True)
        row += 1
        
        # Generator Fuel Consumption
        self.add_slider_setting(scrollable_frame, 'GeneratorFuelConsumption', 'Generator Fuel Usage:', row, 0, 10, 0.1, is_lua=True)
        row += 1
        
        # Allow Exterior Generators
        self.add_bool_setting(scrollable_frame, 'AllowExteriorGenerator', 'Allow Exterior Generators:', row, is_lua=True)
        row += 1
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_vehicles_settings(self, parent):
        """Create vehicle settings"""
        canvas = tk.Canvas(parent, bg=self.get_canvas_bg(), highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        row = 0
        
        # Enable Vehicles
        self.add_bool_setting(scrollable_frame, 'EnableVehicles', 'Enable Vehicles:', row, is_lua=True)
        row += 1
        
        # Car Spawn Rate
        self.add_choice_setting(scrollable_frame, 'CarSpawnRate', 'Vehicle Spawn Rate:', row, {
            'None': 1, 'Very Low': 2, 'Low': 3, 'Normal': 4, 'High': 5
        }, is_lua=True)
        row += 1
        
        # Vehicle Easy Use
        self.add_bool_setting(scrollable_frame, 'VehicleEasyUse', 'Easy Use (No Keys/Hotwire):', row, is_lua=True)
        row += 1
        
        # Locked Cars
        self.add_choice_setting(scrollable_frame, 'LockedCar', 'Locked Cars Frequency:', row, {
            'Never': 1, 'Extremely Rare': 2, 'Rare': 3, 'Sometimes': 4, 'Often': 5, 'Very Often': 6
        }, is_lua=True)
        row += 1
        
        # Car General Condition
        self.add_choice_setting(scrollable_frame, 'CarGeneralCondition', 'Vehicle Condition:', row, {
            'Very Low': 1, 'Low': 2, 'Normal': 3, 'High': 4, 'Very High': 5
        }, is_lua=True)
        row += 1
        
        # Recently Survivor Vehicles
        self.add_choice_setting(scrollable_frame, 'RecentlySurvivorVehicles', 'Well-Maintained Vehicles:', row, {
            'None': 1, 'Low': 2, 'Normal': 3, 'High': 4
        }, is_lua=True)
        row += 1
        
        # Car Gas Consumption
        self.add_slider_setting(scrollable_frame, 'CarGasConsumption', 'Gas Consumption:', row, 0, 100, 0.1, is_lua=True)
        row += 1
        
        # Zombie Attraction Multiplier
        self.add_slider_setting(scrollable_frame, 'ZombieAttractionMultiplier', 'Engine Noise (Zombie Attraction):', row, 0, 100, 0.1, is_lua=True)
        row += 1
        
        # Traffic Jam
        self.add_bool_setting(scrollable_frame, 'TrafficJam', 'Traffic Jams on Roads:', row, is_lua=True)
        row += 1
        
        # Car Alarm
        self.add_choice_setting(scrollable_frame, 'CarAlarm', 'Car Alarms Frequency:', row, {
            'Never': 1, 'Extremely Rare': 2, 'Rare': 3, 'Sometimes': 4, 'Often': 5, 'Very Often': 6
        }, is_lua=True)
        row += 1
        
        # Siren Shutoff Hours
        self.add_slider_setting(scrollable_frame, 'SirenShutoffHours', 'Siren Auto-Shutoff (Hours):', row, 0, 168, 1, is_lua=True)
        row += 1
        
        ttk.Separator(scrollable_frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky='ew', pady=10)
        row += 1
        
        ttk.Label(scrollable_frame, text="Vehicle Damage Settings", 
                 font=('TkDefaultFont', 9, 'bold')).grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # Car Damage on Impact
        self.add_choice_setting(scrollable_frame, 'CarDamageOnImpact', 'Damage to Vehicle on Crash:', row, {
            'Very Low': 1, 'Low': 2, 'Normal': 3, 'High': 4, 'Very High': 5
        }, is_lua=True)
        row += 1
        
        # Damage to Player from Hit by Car
        self.add_choice_setting(scrollable_frame, 'DamageToPlayerFromHitByACar', 'Damage to Player Hit by Car:', row, {
            'None': 1, 'Low': 2, 'Normal': 3, 'High': 4, 'Very High': 5
        }, is_lua=True)
        row += 1
        
        # Player Damage from Crash
        self.add_bool_setting(scrollable_frame, 'PlayerDamageFromCrash', 'Player Injured in Crash:', row, is_lua=True)
        row += 1
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_survival_settings(self, parent):
        """Create survival and health settings"""
        canvas = tk.Canvas(parent, bg=self.get_canvas_bg(), highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        row = 0
        
        # Stats Decrease
        self.add_choice_setting(scrollable_frame, 'StatsDecrease', 'Stats Decrease Rate:', row, {
            'Very Fast': 1, 'Fast': 2, 'Normal': 3, 'Slow': 4, 'Very Slow': 5
        }, is_lua=True)
        row += 1
        
        # Nutrition
        self.add_bool_setting(scrollable_frame, 'Nutrition', 'Nutrition System:', row, is_lua=True)
        row += 1
        
        # Food Rot Speed
        self.add_choice_setting(scrollable_frame, 'FoodRotSpeed', 'Food Rot Speed:', row, {
            'Very Fast': 1, 'Fast': 2, 'Normal': 3, 'Slow': 4, 'Very Slow': 5
        }, is_lua=True)
        row += 1
        
        # Fridge Effectiveness
        self.add_choice_setting(scrollable_frame, 'FridgeFactor', 'Fridge Effectiveness:', row, {
            'Very Low': 1, 'Low': 2, 'Normal': 3, 'High': 4, 'Very High': 5
        }, is_lua=True)
        row += 1
        
        # Injury Severity
        self.add_choice_setting(scrollable_frame, 'InjurySeverity', 'Injury Severity:', row, {
            'Low': 1, 'Normal': 2, 'High': 3
        }, is_lua=True)
        row += 1
        
        # Bone Fractures
        self.add_bool_setting(scrollable_frame, 'BoneFracture', 'Bone Fractures:', row, is_lua=True)
        row += 1
        
        # Endurance Regeneration
        self.add_choice_setting(scrollable_frame, 'EndRegen', 'Endurance Regeneration:', row, {
            'Very Fast': 1, 'Fast': 2, 'Normal': 3, 'Slow': 4, 'Very Slow': 5
        }, is_lua=True)
        row += 1
        
        # Starter Kit
        self.add_bool_setting(scrollable_frame, 'StarterKit', 'Starter Kit (Beginner Items):', row, is_lua=True)
        row += 1
        
        # Character Free Points
        self.add_number_setting(scrollable_frame, 'CharacterFreePoints', 'Character Free Points:', row, 0, 100, is_lua=True)
        row += 1
        
        # Construction Bonus Points
        self.add_number_setting(scrollable_frame, 'ConstructionBonusPoints', 'Construction Bonus Points:', row, 0, 100, is_lua=True)
        row += 1
        
        # Night Darkness
        self.add_choice_setting(scrollable_frame, 'NightDarkness', 'Night Darkness:', row, {
            'Pitch Black': 1, 'Dark': 2, 'Normal': 3, 'Bright': 4
        }, is_lua=True)
        row += 1
        
        # Night Length
        self.add_choice_setting(scrollable_frame, 'NightLength', 'Night Length:', row, {
            'Always Day': 1, 'Short': 2, 'Normal': 3, 'Long': 4, 'Always Night': 5
        }, is_lua=True)
        row += 1
        
        # Zombie Health Impact
        self.add_choice_setting(scrollable_frame, 'ZombieHealthImpact', 'Zombie Health Impact on Player:', row, {
            'None': 1, 'Low': 2, 'Normal': 3, 'High': 4
        }, is_lua=True)
        row += 1
        
        # Decaying Corpse Health Impact
        self.add_choice_setting(scrollable_frame, 'DecayingCorpseHealthImpact', 'Decaying Corpse Health Impact:', row, {
            'None': 1, 'Low': 2, 'Normal': 3, 'High': 4
        }, is_lua=True)
        row += 1
        
        # Blood Level
        self.add_choice_setting(scrollable_frame, 'BloodLevel', 'Blood Level:', row, {
            'None': 1, 'Low': 2, 'Normal': 3, 'High': 4, 'Ultra Gore': 5
        }, is_lua=True)
        row += 1
        
        # Clothing Degradation
        self.add_choice_setting(scrollable_frame, 'ClothingDegradation', 'Clothing Degradation:', row, {
            'Disabled': 1, 'Slow': 2, 'Normal': 3, 'Fast': 4
        }, is_lua=True)
        row += 1
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def add_slider_setting(self, parent, key, label, row, min_val, max_val, step, is_lua=False):
        """Add a slider setting for decimal values with entry box for precise input"""
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        
        var = tk.DoubleVar(value=(min_val + max_val) / 2)
        
        scale = ttk.Scale(frame, from_=min_val, to=max_val, orient=tk.HORIZONTAL,
                         variable=var, length=200)
        scale.pack(side=tk.LEFT, padx=(0, 10))
        
        # Entry box for precise input
        entry = ttk.Entry(frame, width=8)
        entry.insert(0, f"{var.get():.1f}")
        entry.pack(side=tk.LEFT, padx=5)
        
        def update_from_slider(*args):
            """Update entry when slider moves"""
            entry.delete(0, tk.END)
            entry.insert(0, f"{var.get():.1f}")
        
        def update_from_entry(*args):
            """Update slider when entry changes"""
            try:
                value = float(entry.get())
                # Clamp to min/max
                value = max(min_val, min(max_val, value))
                var.set(value)
            except ValueError:
                pass  # Invalid input, ignore
        
        var.trace('w', update_from_slider)
        entry.bind('<Return>', update_from_entry)
        entry.bind('<FocusOut>', update_from_entry)
        
        self.settings[key] = {'widget': scale, 'var': var, 'type': 'slider', 'is_lua': is_lua}
    
    def add_text_setting(self, parent, key, label, row, is_lua=False):
        """Add a text input setting"""
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        entry = ttk.Entry(parent, width=40)
        entry.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        self.settings[key] = {'widget': entry, 'type': 'text', 'is_lua': is_lua}
    
    def add_number_setting(self, parent, key, label, row, min_val, max_val, is_lua=False):
        """Add a number input setting"""
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        spinbox = ttk.Spinbox(parent, from_=min_val, to=max_val, width=10)
        spinbox.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        self.settings[key] = {'widget': spinbox, 'type': 'number', 'is_lua': is_lua}
    
    def add_bool_setting(self, parent, key, label, row, is_lua=False):
        """Add a boolean checkbox setting"""
        var = tk.BooleanVar()
        check = ttk.Checkbutton(parent, text=label, variable=var)
        check.grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        self.settings[key] = {'widget': check, 'var': var, 'type': 'bool', 'is_lua': is_lua}
    
    def add_choice_setting(self, parent, key, label, row, choices, is_lua=False):
        """Add a dropdown choice setting"""
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        var = tk.StringVar()
        combo = ttk.Combobox(parent, textvariable=var, values=list(choices.keys()), state='readonly', width=20)
        combo.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        self.settings[key] = {'widget': combo, 'var': var, 'type': 'choice', 'choices': choices, 'is_lua': is_lua}
    
    def load_settings(self):
        """Load settings from config files"""
        # Load .ini file
        if self.ini_file and self.ini_file.exists():
            with open(self.ini_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        if key in self.settings and not self.settings[key]['is_lua']:
                            self.original_values[key] = value
                            widget_info = self.settings[key]
                            
                            if widget_info['type'] == 'text' or widget_info['type'] == 'number':
                                widget_info['widget'].delete(0, tk.END)
                                widget_info['widget'].insert(0, value)
                            elif widget_info['type'] == 'bool':
                                widget_info['var'].set(value.lower() == 'true')
        
        # Load .lua file (basic parsing)
        if self.lua_file and self.lua_file.exists():
            with open(self.lua_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                for key in self.settings:
                    if self.settings[key]['is_lua']:
                        # Simple regex to find setting
                        pattern = rf'{key}\s*=\s*([^,\n]+)'
                        match = re.search(pattern, content)
                        if match:
                            value = match.group(1).strip().rstrip(',')
                            self.original_values[key] = value
                            widget_info = self.settings[key]
                            
                            if widget_info['type'] == 'number':
                                widget_info['widget'].delete(0, tk.END)
                                widget_info['widget'].insert(0, value)
                            elif widget_info['type'] == 'bool':
                                widget_info['var'].set(value.lower() == 'true')
                            elif widget_info['type'] == 'slider':
                                # Set slider value
                                try:
                                    widget_info['var'].set(float(value))
                                except ValueError:
                                    pass
                            elif widget_info['type'] == 'choice':
                                # Find the choice that matches the value
                                # Try as int first, then float
                                try:
                                    if '.' in value:
                                        float_val = float(value)
                                        for choice_name, choice_val in widget_info['choices'].items():
                                            if choice_val == float_val:
                                                widget_info['var'].set(choice_name)
                                                break
                                    else:
                                        int_val = int(value)
                                        for choice_name, choice_val in widget_info['choices'].items():
                                            if choice_val == int_val:
                                                widget_info['var'].set(choice_name)
                                                break
                                except ValueError:
                                    pass
    
    def save_settings(self):
        """Save settings back to config files"""
        if not messagebox.askyesno("Confirm Save", 
                                   "Save changes to server configuration?\n\n"
                                   "Server must be restarted for changes to take effect.",
                                   icon='warning'):
            return
        
        try:
            # Backup original files
            import shutil
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if self.ini_file:
                backup = self.ini_file.with_suffix(f'.ini.backup_{timestamp}')
                shutil.copy2(self.ini_file, backup)
            
            if self.lua_file:
                backup = self.lua_file.with_suffix(f'.lua.backup_{timestamp}')
                shutil.copy2(self.lua_file, backup)
            
            # Save .ini file
            if self.ini_file:
                with open(self.ini_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                new_lines = []
                for line in lines:
                    written = False
                    for key in self.settings:
                        if not self.settings[key]['is_lua'] and line.strip().startswith(f'{key}='):
                            widget_info = self.settings[key]
                            
                            if widget_info['type'] == 'text':
                                new_value = widget_info['widget'].get()
                            elif widget_info['type'] == 'number':
                                new_value = widget_info['widget'].get()
                            elif widget_info['type'] == 'bool':
                                new_value = 'true' if widget_info['var'].get() else 'false'
                            
                            new_lines.append(f"{key}={new_value}\n")
                            written = True
                            break
                    
                    if not written:
                        new_lines.append(line)
                
                with open(self.ini_file, 'w', encoding='utf-8') as f:
                    f.writelines(new_lines)
            
            # Save .lua file
            if self.lua_file and self.lua_file.exists():
                with open(self.lua_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Update each Lua setting
                for key in self.settings:
                    if self.settings[key]['is_lua']:
                        widget_info = self.settings[key]
                        
                        # Get new value
                        if widget_info['type'] == 'number':
                            new_value = widget_info['widget'].get()
                        elif widget_info['type'] == 'bool':
                            new_value = 'true' if widget_info['var'].get() else 'false'
                        elif widget_info['type'] == 'slider':
                            # Get slider value, rounded to 1 decimal place
                            new_value = f"{widget_info['var'].get():.1f}"
                        elif widget_info['type'] == 'choice':
                            selected = widget_info['var'].get()
                            # Skip if no selection or invalid selection
                            if not selected or selected not in widget_info['choices']:
                                continue
                            new_value = str(widget_info['choices'][selected])
                        else:
                            continue
                        
                        # Replace in content using regex
                        pattern = rf'({key}\s*=\s*)([^,\n]+)'
                        replacement = rf'\g<1>{new_value}'
                        content = re.sub(pattern, replacement, content)
                
                # Write back
                with open(self.lua_file, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            messagebox.showinfo("Success", 
                               f"Settings saved!\n\n"
                               f"Backups created with timestamp {timestamp}\n\n"
                               f"Server must be restarted for changes to take effect.")
            
            self.parent.log_command_output(f"Settings saved. Backups created: {timestamp}")
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            messagebox.showerror("Error", f"Failed to save settings:\n\n{str(e)}\n\nDetails:\n{error_details}")
            print(f"Save error: {error_details}")  # Also print to console
    
    def view_raw_files(self):
        """Open raw config files in text editor"""
        RawFileViewer(self, self.ini_file, self.lua_file)
    


class ModManagerWindow(tk.Toplevel):
    """Simple window for editing mods and workshop IDs"""
    
    def __init__(self, parent, ini_file, server_path):
        super().__init__(parent)
        self.parent = parent
        self.ini_file = ini_file
        self.server_path = Path(server_path)
        
        self.title("Mod Manager - Simple Editor")
        self.geometry("900x600")
        
        self.create_ui()
        self.load_mods()
    
    def create_ui(self):
        """Create the simple mod editor UI"""
        # Header
        header = ttk.Label(self, text="Edit your server mods directly", 
                          font=('TkDefaultFont', 10, 'bold'))
        header.pack(pady=10)
        
        # Create two side-by-side panels
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Left panel - Mods
        left_frame = ttk.LabelFrame(main_frame, text="Mod IDs (one per line)", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        ttk.Label(left_frame, text="These are the mod folder names", 
                 foreground='gray', font=('TkDefaultFont', 8)).pack(anchor=tk.W, pady=(0, 5))
        
        self.mods_text = scrolledtext.ScrolledText(left_frame, wrap=tk.WORD, width=40)
        self.mods_text.pack(fill=tk.BOTH, expand=True)
        
        # Right panel - Workshop IDs
        right_frame = ttk.LabelFrame(main_frame, text="Workshop IDs (one per line)", padding=10)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        ttk.Label(right_frame, text="Steam Workshop item numbers", 
                 foreground='gray', font=('TkDefaultFont', 8)).pack(anchor=tk.W, pady=(0, 5))
        
        self.workshop_text = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD, width=40)
        self.workshop_text.pack(fill=tk.BOTH, expand=True)
        
        # Info label
        info_frame = ttk.Frame(self)
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        info_text = ("Note: These lists don't align 1:1. One Workshop ID can provide multiple mods.\n"
                    "Leading backslashes (\\) will be added automatically when saving.")
        ttk.Label(info_frame, text=info_text, foreground='blue', 
                 font=('TkDefaultFont', 8)).pack(anchor=tk.W)
        
        # Bottom buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(btn_frame, text="Save to Config", 
                  command=self.save_mods).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Reload from Config", 
                  command=self.load_mods).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Close", 
                  command=self.destroy).pack(side=tk.RIGHT, padx=5)
    
    def load_mods(self):
        """Load current mods from ini file"""
        self.mods_text.delete(1.0, tk.END)
        self.workshop_text.delete(1.0, tk.END)
        
        if not self.ini_file.exists():
            return
        
        with open(self.ini_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if line.startswith('Mods='):
                    mods_str = line.split('=', 1)[1].strip()
                    # Split by semicolon and clean up
                    mods = [m.strip().lstrip('\\') for m in mods_str.split(';') if m.strip()]
                    self.mods_text.insert(tk.END, '\n'.join(mods))
                    
                elif line.startswith('WorkshopItems='):
                    workshop_str = line.split('=', 1)[1].strip()
                    # Split by semicolon
                    workshop_ids = [w.strip() for w in workshop_str.split(';') if w.strip()]
                    self.workshop_text.insert(tk.END, '\n'.join(workshop_ids))
    
    def save_mods(self):
        """Save mods back to ini file"""
        if not messagebox.askyesno("Confirm Save", 
                                   "Save mod changes to server configuration?\n\n"
                                   "Server must be restarted for changes to take effect."):
            return
        
        try:
            # Get text from both boxes
            mods_content = self.mods_text.get(1.0, tk.END).strip()
            workshop_content = self.workshop_text.get(1.0, tk.END).strip()
            
            # Parse into lists (one per line)
            mods = [line.strip() for line in mods_content.split('\n') if line.strip()]
            workshop_ids = [line.strip() for line in workshop_content.split('\n') if line.strip()]
            
            # Backup original
            import shutil
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup = self.ini_file.with_suffix(f'.ini.backup_{timestamp}')
            shutil.copy2(self.ini_file, backup)
            
            # Read file
            with open(self.ini_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # Update lines
            new_lines = []
            for line in lines:
                if line.strip().startswith('Mods='):
                    # Rebuild Mods= line with backslashes and semicolons
                    mods_str = ';'.join(['\\' + m for m in mods]) + ';'
                    new_lines.append(f"Mods={mods_str}\n")
                elif line.strip().startswith('WorkshopItems='):
                    # Rebuild WorkshopItems= line with semicolons
                    workshop_str = ';'.join(workshop_ids)
                    new_lines.append(f"WorkshopItems={workshop_str}\n")
                else:
                    new_lines.append(line)
            
            # Write back
            with open(self.ini_file, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            
            messagebox.showinfo("Success", 
                               f"Mods saved!\n\n"
                               f"Mods: {len(mods)}\n"
                               f"Workshop IDs: {len(workshop_ids)}\n\n"
                               f"Backup: {backup.name}")
            
            if hasattr(self.parent, 'parent') and hasattr(self.parent.parent, 'log_command_output'):
                self.parent.parent.log_command_output(f"Mods configuration saved. Backup: {timestamp}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save mods: {str(e)}")


class RawFileViewer(tk.Toplevel):
    """Simple text viewer for raw config files"""
    
    def __init__(self, parent, ini_file, lua_file):
        super().__init__(parent)
        self.ini_file = ini_file
        self.lua_file = lua_file
        
        self.title("Raw Configuration Files")
        self.geometry("900x700")
        
        # Apply theme
        if hasattr(parent, 'current_theme'):
            theme = parent.current_theme.get()
            if theme == "dark":
                self.configure(bg="#2b2b2b")
                text_bg = "#404040"
                text_fg = "#ffffff"
                select_bg = "#505050"
            else:
                self.configure(bg="#f5f5f5")
                text_bg = "#ffffff"
                text_fg = "#000000"
                select_bg = "#0078d7"
        else:
            self.configure(bg="#f5f5f5")
            text_bg = "#ffffff"
            text_fg = "#000000"
            select_bg = "#0078d7"
        
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        if ini_file and ini_file.exists():
            ini_frame = ttk.Frame(notebook)
            notebook.add(ini_frame, text=ini_file.name)
            
            text = scrolledtext.ScrolledText(ini_frame, wrap=tk.WORD,
                                            bg=text_bg, fg=text_fg,
                                            insertbackground=text_fg,
                                            selectbackground=select_bg,
                                            selectforeground="#ffffff" if select_bg == "#0078d7" else "#ffffff")
            text.pack(fill=tk.BOTH, expand=True)
            
            with open(ini_file, 'r', encoding='utf-8', errors='ignore') as f:
                text.insert(tk.END, f.read())
        
        if lua_file and lua_file.exists():
            lua_frame = ttk.Frame(notebook)
            notebook.add(lua_frame, text=lua_file.name)
            
            text = scrolledtext.ScrolledText(lua_frame, wrap=tk.WORD,
                                            bg=text_bg, fg=text_fg,
                                            insertbackground=text_fg,
                                            selectbackground=select_bg,
                                            selectforeground="#ffffff" if select_bg == "#0078d7" else "#ffffff")
            text.pack(fill=tk.BOTH, expand=True)
            
            with open(lua_file, 'r', encoding='utf-8', errors='ignore') as f:
                text.insert(tk.END, f.read())
        
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Button(btn_frame, text="Close", command=self.destroy).pack(side=tk.RIGHT)


if __name__ == "__main__":
    import tkinter.simpledialog
    app = PZServerAdmin()
    app.mainloop()
