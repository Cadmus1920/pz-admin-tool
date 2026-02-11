"""Utility functions for the Project Zomboid Server Admin Tool.

Includes file parsing (mods, banlists, config) and path detection helpers.
"""

import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def parse_mods_and_workshop(ini_file):
    """Parse mods and workshop items from server INI file.
    
    Args:
        ini_file (Path): Path to server .ini file
        
    Returns:
        tuple: (mods_list, workshop_list) where each is a list of strings
    """
    mods = []
    workshop_ids = []
    
    try:
        with open(ini_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
            for line in content.split('\n'):
                if line.startswith('Mods='):
                    mods_str = line.split('=', 1)[1].strip()
                    mods = [m.strip() for m in mods_str.split(';') if m.strip()]
                elif line.startswith('WorkshopItems='):
                    workshop_str = line.split('=', 1)[1].strip()
                    workshop_ids = [w.strip() for w in workshop_str.split(';') if w.strip()]
    except Exception as e:
        logger.error("Failed to parse mods from %s: %s", ini_file, e)
    
    return mods, workshop_ids


def parse_banlist(banlist_file):
    """Parse ban list from banlist.txt file.
    
    Args:
        banlist_file (Path): Path to banlist.txt
        
    Returns:
        list: List of tuples (username, ip, reason, date) where date is 'N/A'
    """
    bans = []
    
    try:
        with open(banlist_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Parse format: username,ip,reason or just username
                parts = line.split(',')
                username = parts[0] if len(parts) > 0 else 'Unknown'
                ip = parts[1] if len(parts) > 1 else 'N/A'
                reason = parts[2] if len(parts) > 2 else 'No reason specified'
                date = 'N/A'
                
                bans.append((username, ip, reason, date))
    except Exception as e:
        logger.error("Failed to parse banlist from %s: %s", banlist_file, e)
    
    return bans


def find_server_path(start_path):
    """Auto-detect Project Zomboid server paths.
    
    Searches common installation and data directories for the server.
    Prioritizes data directories with actual config files.
    
    Args:
        start_path (Path): Starting directory to search from
        
    Returns:
        Path or None: Most likely server path, or None if not found
    """
    data_paths = [
        Path.home() / "Zomboid",
        Path.home() / ".local" / "share" / "Zomboid",
    ]
    
    install_paths = [
        Path.home() / ".steam" / "steamapps" / "common" / "Project Zomboid Dedicated Server",
        Path.home() / "Steam" / "steamapps" / "common" / "Project Zomboid Dedicated Server",
        Path("/home/pzserver/.steam/steamapps/common/Project Zomboid Dedicated Server"),
        Path("/opt/pzserver"),
        Path.home() / ".local" / "share" / "Steam" / "steamapps" / "common" / "Project Zomboid Dedicated Server",
    ]
    
    # Check data directories for actual config files
    for path in data_paths:
        server_dir = path / 'Server'
        if server_dir.exists():
            has_ini = any(f.endswith('.ini') for f in os.listdir(server_dir) 
                         if os.path.isfile(os.path.join(server_dir, f)))
            if has_ini:
                logger.info("Found server data with config at %s", path)
                return path
    
    # Check install paths
    for path in install_paths:
        if path.exists():
            logger.info("Found server installation at %s", path)
            return path
    
    logger.debug("No server path found")
    return None


def find_config_file(server_path):
    """Find the server .ini config file.
    
    Searches multiple locations: Server/, direct path, ~/Zomboid/Server/, etc.
    
    Args:
        server_path (Path): Server root path
        
    Returns:
        Path or None: Path to .ini file, or None if not found
    """
    search_dirs = [
        server_path / 'Server',
        server_path,
        Path.home() / 'Zomboid' / 'Server',
        Path.home() / '.local' / 'share' / 'Zomboid' / 'Server',
    ]
    
    for search_dir in search_dirs:
        if search_dir.exists():
            for ini_file in search_dir.glob('*.ini'):
                logger.debug("Found config file at %s", ini_file)
                return ini_file
    
    logger.warning("No config file found in %s", server_path)
    return None


def find_log_file(server_path):
    """Find the server log file.
    
    Searches multiple locations: Logs/, direct path, ~/Zomboid/Logs/, etc.
    
    Args:
        server_path (Path): Server root path
        
    Returns:
        Path or None: Path to most recent log directory, or None if not found
    """
    log_locations = [
        server_path / 'Logs',
        server_path.parent / 'Logs',
        Path.home() / 'Zomboid' / 'Logs',
        Path.home() / '.local' / 'share' / 'Zomboid' / 'Logs',
    ]
    
    for log_dir in log_locations:
        if log_dir.exists() and log_dir.is_dir():
            logger.debug("Found log directory at %s", log_dir)
            return log_dir
    
    logger.warning("No log directory found")
    return None
