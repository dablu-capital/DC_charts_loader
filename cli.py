#!/usr/bin/env python3
"""
Interactive CLI for DC Charts Loader.

This script provides an interactive command-line interface for:
1. Selecting data files for chart loading
2. Loading charts with the selected data
3. Managing project screenshots

Usage:
    python cli.py
    python -m src.cli
"""

import sys
import argparse
from pathlib import Path
from src.cli import FileSelector, MainMenu
from src.logger import logger


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Interactive CLI for DC Charts Loader",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py                    # Start interactive CLI
  python cli.py --file data.feather  # Load specific file directly
        """
    )
    
    parser.add_argument(
        "--file",
        type=str,
        help="Specify data file directly (bypasses file selection menu)"
    )
    
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data",
        help="Data directory path (default: data)"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        default="config.json",
        help="Config file path (default: config.json)"
    )
    
    return parser.parse_args()


def validate_file_path(file_path: str, data_dir: str) -> bool:
    """
    Validate that the specified file exists and is a .feather file.
    
    Args:
        file_path: The file path to validate
        data_dir: The data directory path
        
    Returns:
        True if valid, False otherwise
    """
    full_path = Path(data_dir) / file_path
    
    if not full_path.exists():
        print(f"❌ File not found: {full_path}")
        return False
    
    if not full_path.suffix == ".feather":
        print(f"❌ Invalid file type. Expected .feather file, got: {full_path.suffix}")
        return False
    
    # Check for corresponding _data.feather file
    data_file = full_path.with_name(full_path.stem + "_data.feather")
    if not data_file.exists():
        print(f"❌ Corresponding data file not found: {data_file}")
        return False
    
    return True


def main():
    """Main CLI application entry point."""
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        # Initialize components
        file_selector = FileSelector(data_dir=args.data_dir, config_file=args.config)
        menu = MainMenu()
        
        # Display welcome message
        menu.display_welcome()
        
        # Handle direct file specification
        if args.file:
            if validate_file_path(args.file, args.data_dir):
                print(f"📁 Using specified file: {args.file}")
                selected_file = args.file
                # Save as last selected file for future use
                file_selector.save_last_file(selected_file)
            else:
                print("❌ Invalid file specified. Exiting...")
                sys.exit(1)
        else:
            # Interactive file selection
            selected_file = file_selector.get_file_selection()
            
            if not selected_file:
                menu.handle_no_file_selected()
        
        # Run main menu loop
        print(f"\n✅ Selected file: {selected_file}")
        menu.run_menu_loop(selected_file)
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Operation cancelled by user. Goodbye!")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error in CLI: {e}")
        print(f"\n❌ Unexpected error: {e}")
        print("Please check the logs for more details.")
        sys.exit(1)


if __name__ == "__main__":
    main()