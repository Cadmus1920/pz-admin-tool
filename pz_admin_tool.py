"""
Project Zomboid Server Administration Tool
A comprehensive GUI tool for managing Project Zomboid servers
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import socket
import struct
import threading
import time
import sqlite3
import os
from pathlib import Path
from datetime import datetime
import json


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
            except:
                pass
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
        
        self.create_widgets()
        self.load_config()
        
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
        ttk.Button(actions_frame, text="Teleport to Me", command=lambda: self.player_action('teleport')).grid(row=0, column=4, padx=5)
        
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
        
        self.info_text = scrolledtext.ScrolledText(info_text_frame, wrap=tk.WORD, height=20)
        self.info_text.pack(fill=tk.BOTH, expand=True)
        
        btn_frame = ttk.Frame(self.info_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text="Get Server Info", command=self.get_server_info).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Get Server Stats", command=self.get_server_stats).pack(side=tk.LEFT, padx=5)
        
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
        
        self.command_output = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, height=15)
        self.command_output.pack(fill=tk.BOTH, expand=True)
        
    def create_mods_tab(self):
        """Create the mods information tab"""
        # Mods list
        list_frame = ttk.Frame(self.mods_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        columns = ('Name', 'Workshop ID')
        self.mods_tree = ttk.Treeview(list_frame, columns=columns, show='tree headings')
        self.mods_tree.heading('#0', text='#')
        self.mods_tree.heading('Name', text='Mod Name')
        self.mods_tree.heading('Workshop ID', text='Workshop ID')
        
        self.mods_tree.column('#0', width=50)
        self.mods_tree.column('Name', width=400)
        self.mods_tree.column('Workshop ID', width=150)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.mods_tree.yview)
        self.mods_tree.configure(yscrollcommand=scrollbar.set)
        
        self.mods_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        btn_frame = ttk.Frame(self.mods_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text="Refresh Mods", command=self.refresh_mods).pack(side=tk.LEFT, padx=5)
        
    def create_logs_tab(self):
        """Create the logs viewer tab"""
        log_frame = ttk.Frame(self.logs_frame)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.logs_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD)
        self.logs_text.pack(fill=tk.BOTH, expand=True)
        
        btn_frame = ttk.Frame(self.logs_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text="Refresh Logs", command=self.refresh_logs).pack(side=tk.LEFT, padx=5)
        ttk.Label(btn_frame, text="Lines:").pack(side=tk.LEFT, padx=5)
        self.log_lines_entry = ttk.Entry(btn_frame, width=10)
        self.log_lines_entry.insert(0, "100")
        self.log_lines_entry.pack(side=tk.LEFT, padx=5)
        
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
                cmd = f'teleport "{username}"'
            else:
                return
            
            response = self.rcon.execute_command(cmd)
            self.log_command_output(f"Action: {action}\nCommand: {cmd}\nResponse: {response}")
            messagebox.showinfo("Success", f"Action '{action}' executed for {username}")
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
            
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
        
    def refresh_mods(self):
        """Refresh the mods list from server files"""
        # Clear existing items
        for item in self.mods_tree.get_children():
            self.mods_tree.delete(item)
        
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
                                mods = [m.strip() for m in line.split('=')[1].strip().split(';') if m.strip()]
                            elif line.startswith('WorkshopItems='):
                                workshop_ids = [w.strip() for w in line.split('=')[1].strip().split(';') if w.strip()]
                    break
            
            # Display mods with their workshop IDs
            for i, mod in enumerate(mods):
                workshop_id = workshop_ids[i] if i < len(workshop_ids) else 'N/A'
                self.mods_tree.insert('', tk.END, text=str(i+1),
                                    values=(mod, workshop_id))
            
            # Display orphaned workshop IDs (IDs without corresponding mod names)
            if len(workshop_ids) > len(mods):
                for i in range(len(mods), len(workshop_ids)):
                    self.mods_tree.insert('', tk.END, text=str(i+1),
                                        values=('(Orphaned - No Mod ID)', workshop_ids[i]))
                    
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
            
    def refresh_all(self):
        """Refresh all tabs"""
        self.refresh_players()
        self.get_server_info()
        self.refresh_mods()
        self.refresh_logs()
        
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
        except:
            pass


if __name__ == "__main__":
    import tkinter.simpledialog
    app = PZServerAdmin()
    app.mainloop()
