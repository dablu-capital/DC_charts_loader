"""Main menu system for CLI interface."""

import sys
import subprocess
from pathlib import Path
from src.logger import logger
from src.config import config


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

            if choice in ["1", "2", "3"]:
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

            # Get the original filename to restore later
            original_filename = config.general.data_filename

            # Temporarily update the config
            config.general.data_filename = data_filename

            # Import and run main chart loading logic
            from src.models import ChartsDailyData
            from src.ui.models import SingleChartPlotter, DualChartPlotter

            path = Path.cwd() / config.general.data_path
            dict_filename = path / data_filename
            data_filename_full = dict_filename.with_name(
                dict_filename.stem + "_data.feather"
            )

            # Check if files exist
            if not dict_filename.exists():
                logger.error(f"❌ Dictionary file not found: {dict_filename}")
                return False

            if not data_filename_full.exists():
                logger.error(f"❌ Data file not found: {data_filename_full}")
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

            logger.info(
                "✅ Charts loaded successfully! Close the chart window to return to menu."
            )
            chart.show(block=True)

            # Restore original config
            config.general.data_filename = original_filename

            return True

        except TypeError as e:
            logger.error(f"Error loading charts: {e}")

            return False

    def save_screenshots(self) -> bool:
        """
        Save project screenshots using the existing save_project.py script.

        Returns:
            True if successful, False otherwise
        """
        try:
            print("\n📸 Starting screenshot save process...")

            # Check and create screenshots directory if needed
            screenshots_dir = self.project_root / "screenshots"
            if not screenshots_dir.exists():
                print("📁 Creating screenshots directory...")
                screenshots_dir.mkdir(exist_ok=True)
                logger.info(f"Created screenshots directory: {screenshots_dir}")

            # Check if there are any PNG files in the screenshots directory
            png_files = list(screenshots_dir.glob("*.png"))
            if not png_files:
                print("⚠️  No screenshots found in the screenshots directory!")
                print(f"📍 Screenshots directory: {screenshots_dir}")
                print("\n💡 To use this feature:")
                print("   1. Take screenshots of your charts (manually or via chart export)")
                print("   2. Save them as PNG files in the screenshots/ directory")
                print("   3. Run this option again to upload them to Imgur and organize them")
                return False

            print(f"📊 Found {len(png_files)} screenshot(s) to process:")
            for png_file in png_files:
                print(f"   • {png_file.name}")

            # Get project name from user
            project_name = (
                input("\nEnter project name (default: test): ").strip() or "test"
            )

            # Check Imgur configuration
            if config.imgur.client_id == "my_client_id":
                print("⚠️  Imgur configuration required!")
                print("Please set your Imgur client_id in config.json.")
                print("You can get it from https://api.imgur.com/oauth2/addclient")
                return False

            # Run save_project.py with the project name
            save_script = self.project_root / "save_project.py"

            if not save_script.exists():
                logger.error(f"❌ Screenshot script not found: {save_script}")
                return False

            print(f"🔄 Processing screenshots for project: {project_name}")

            # Run the script with automatic input
            process = subprocess.Popen(
                [sys.executable, str(save_script)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(self.project_root),
            )

            # Send the project name as input
            stdout, stderr = process.communicate(input=project_name + "\n")

            if process.returncode == 0:
                print("✅ Screenshots processed successfully!")
                # Display output from save_project.py
                if stdout:
                    print("\n📋 Output:")
                    print(stdout)
                return True
            else:
                print(f"❌ Error processing screenshots:")
                if stderr:
                    print(stderr)
                if "No such file or directory" in stderr:
                    print("\n💡 This might be because:")
                    print("   • Screenshots were moved during processing")
                    print("   • Imgur authentication failed")
                    print("   • Network connectivity issues")
                return False

        except Exception as e:
            logger.error(f"Error saving screenshots: {e}")
            print(f"❌ Error saving screenshots: {e}")
            print("\n💡 Please check:")
            print("   • Screenshots are present in the screenshots/ directory")
            print("   • Imgur configuration is correct in config.json")
            print("   • Network connectivity for Imgur upload")
            return False

    def run_menu_loop(self, selected_file: str) -> None:
        """
        Run the main menu loop.

        Args:
            selected_file: The selected data file name
        """
        while True:
            choice = self.display_main_menu()

            if choice == "1":
                self.load_charts(selected_file)

            elif choice == "2":
                self.save_screenshots()

            elif choice == "3":
                print("\n👋 Goodbye!")
                sys.exit(0)

    def handle_no_file_selected(self) -> None:
        """Handle the case when no file was selected."""
        print("\n❌ No file selected. Exiting...")
        sys.exit(1)
