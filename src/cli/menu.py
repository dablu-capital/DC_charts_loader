"""Main menu system for CLI interface."""

import sys
import subprocess
from pathlib import Path
from typing import Optional
from src.logger import logger


class MainMenu:
    """Handles the main CLI menu system and user interaction."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
    
    def display_welcome(self) -> None:
        """Display welcome message and application info."""
        print("=" * 50)
        print("🚀 Welcome to DC Charts Loader CLI!")
        print("=" * 50)
    
    def display_main_menu(self) -> str:
        """
        Display main options menu and return user selection.
        
        Returns:
            User's menu choice ('1', '2', or '3')
        """
        print("\n📋 Main Options:")
        print("1. 📊 Load charts")
        print("2. 📸 Save project screenshots")
        print("3. 🚪 Exit")
        
        while True:
            choice = input("\nSelect option [1-3]: ").strip()
            
            if choice in ['1', '2', '3']:
                return choice
            else:
                print("❌ Invalid selection. Please enter 1, 2, or 3")
    
    def load_charts(self, data_filename: str) -> bool:
        """
        Load charts using the selected data file.
        
        Args:
            data_filename: The selected data file name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"\n🔄 Loading charts with file: {data_filename}")
            
            # Update config temporarily for main.py
            from src.config import config
            
            # Get the original filename to restore later
            original_filename = config.general.data_filename
            
            # Temporarily update the config
            config.general.data_filename = data_filename
            
            # Import and run main chart loading logic
            from src.models import ChartsDailyData
            from src.ui.models import SingleChartPlotter, DualChartPlotter
            
            path = Path.cwd() / config.general.data_path
            dict_filename = path / data_filename
            data_filename_full = dict_filename.with_name(dict_filename.stem + "_data.feather")
            
            # Check if files exist
            if not dict_filename.exists():
                print(f"❌ Dictionary file not found: {dict_filename}")
                return False
                
            if not data_filename_full.exists():
                print(f"❌ Data file not found: {data_filename_full}")
                return False
            
            chart_data = ChartsDailyData(dict_filename, data_filename_full)
            logger.info(f"Loading chart data from {data_filename_full}")
            
            # Choose between single chart or dual chart grid
            use_dual_chart = config.chart.use_intraday_tf
            
            if use_dual_chart:
                chart_plotter = DualChartPlotter(chart_data)
            else:
                chart_plotter = SingleChartPlotter(chart_data)
                
            chart_plotter.setup()
            chart = chart_plotter.chart
            
            print("✅ Charts loaded successfully! Close the chart window to return to menu.")
            chart.show(block=True)
            
            # Restore original config
            config.general.data_filename = original_filename
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading charts: {e}")
            print(f"❌ Error loading charts: {e}")
            return False
    
    def save_screenshots(self) -> bool:
        """
        Save project screenshots using the existing save_project.py script.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            print("\n📸 Starting screenshot save process...")
            
            # Get project name from user
            project_name = input("Enter project name (default: test): ").strip() or "test"
            
            # Run save_project.py with the project name
            save_script = self.project_root / "save_project.py"
            
            if not save_script.exists():
                print(f"❌ Screenshot script not found: {save_script}")
                return False
            
            print(f"🔄 Saving screenshots for project: {project_name}")
            
            # Create a modified environment with the project name
            import os
            env = os.environ.copy()
            
            # Run the script with automatic input
            process = subprocess.Popen(
                [sys.executable, str(save_script)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(self.project_root)
            )
            
            # Send the project name as input
            stdout, stderr = process.communicate(input=project_name + "\n")
            
            if process.returncode == 0:
                print("✅ Screenshots saved successfully!")
                # Display output from save_project.py
                if stdout:
                    print("\n📋 Output:")
                    print(stdout)
                return True
            else:
                print(f"❌ Error saving screenshots:")
                if stderr:
                    print(stderr)
                return False
                
        except Exception as e:
            logger.error(f"Error saving screenshots: {e}")
            print(f"❌ Error saving screenshots: {e}")
            return False
    
    def run_menu_loop(self, selected_file: str) -> None:
        """
        Run the main menu loop.
        
        Args:
            selected_file: The selected data file name
        """
        while True:
            choice = self.display_main_menu()
            
            if choice == '1':
                self.load_charts(selected_file)
                
            elif choice == '2':
                self.save_screenshots()
                
            elif choice == '3':
                print("\n👋 Goodbye!")
                sys.exit(0)
    
    def handle_no_file_selected(self) -> None:
        """Handle the case when no file was selected."""
        print("\n❌ No file selected. Exiting...")
        sys.exit(1)