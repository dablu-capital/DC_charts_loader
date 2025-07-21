"""File selection logic for CLI interface."""

import json
from pathlib import Path
from typing import List, Optional
from src.logger import logger


class FileSelector:
    """Handles file selection and management for the CLI interface."""
    
    def __init__(self, data_dir: str = "data", config_file: str = "config.json"):
        self.data_dir = Path(data_dir)
        self.config_file = Path(config_file)
        
    def get_available_files(self) -> List[str]:
        """
        Get main data files, excluding _data.feather and _min_data.feather.
        
        Returns:
            List of available .feather files (sorted)
        """
        try:
            if not self.data_dir.exists():
                logger.warning(f"Data directory {self.data_dir} does not exist")
                return []
            
            all_files = list(self.data_dir.glob("*.feather"))
            
            # Filter out files ending with _data.feather and _min_data.feather
            main_files = [
                f.name for f in all_files 
                if not (f.name.endswith("_data.feather") or f.name.endswith("_min_data.feather"))
            ]
            
            return sorted(main_files)
            
        except Exception as e:
            logger.error(f"Error scanning data directory: {e}")
            return []
    
    def load_last_file(self) -> Optional[str]:
        """
        Load last selected file from config.
        
        Returns:
            Last selected filename or None if not found/error
        """
        try:
            if not self.config_file.exists():
                return None
                
            with open(self.config_file, "r") as f:
                config_data = json.load(f)
                
            return config_data.get("cli", {}).get("last_file")
            
        except Exception as e:
            logger.warning(f"Could not load last file from config: {e}")
            return None
    
    def save_last_file(self, filename: str) -> None:
        """
        Save last selected file to config.
        
        Args:
            filename: The filename to save as last selected
        """
        try:
            # Load existing config
            config_data = {}
            if self.config_file.exists():
                with open(self.config_file, "r") as f:
                    config_data = json.load(f)
            
            # Update CLI section
            if "cli" not in config_data:
                config_data["cli"] = {}
            
            config_data["cli"]["last_file"] = filename
            
            # Save back to file
            with open(self.config_file, "w") as f:
                json.dump(config_data, f, indent=4)
                
            logger.info(f"Saved last selected file: {filename}")
            
        except Exception as e:
            logger.error(f"Could not save last file to config: {e}")
    
    def display_file_menu(self, files: List[str], default: str = None) -> str:
        """
        Display file selection menu and return selected file.
        
        Args:
            files: List of available files
            default: Default file to suggest (usually last selected)
            
        Returns:
            Selected filename
        """
        if not files:
            print("❌ No data files found in the data directory!")
            return ""
            
        print("\n📁 Available data files:")
        for i, filename in enumerate(files, 1):
            marker = " (default)" if filename == default else ""
            print(f"{i:2d}. {filename}{marker}")
        
        while True:
            prompt = f"\nSelect file [1-{len(files)}]"
            if default:
                prompt += f" or press Enter for default ({default})"
            prompt += ": "
            
            choice = input(prompt).strip()
            
            # Handle Enter for default
            if not choice and default:
                return default
            
            # Handle numeric selection
            try:
                choice_num = int(choice)
                if 1 <= choice_num <= len(files):
                    selected_file = files[choice_num - 1]
                    return selected_file
                else:
                    print(f"❌ Invalid selection. Please enter a number between 1 and {len(files)}")
                    
            except ValueError:
                print("❌ Invalid input. Please enter a number or press Enter for default")
    
    def get_file_selection(self) -> str:
        """
        Main method to handle complete file selection workflow.
        
        Returns:
            Selected filename or empty string if no selection made
        """
        files = self.get_available_files()
        last_file = self.load_last_file()
        
        # Validate that last_file is still available
        if last_file and last_file not in files:
            logger.warning(f"Last selected file '{last_file}' no longer available")
            last_file = None
        
        # If no last file, use the first available file as default
        if not last_file and files:
            last_file = files[0]
        
        selected_file = self.display_file_menu(files, last_file)
        
        if selected_file:
            self.save_last_file(selected_file)
            
        return selected_file