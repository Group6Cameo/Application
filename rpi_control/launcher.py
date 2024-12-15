import os
import sys
import multiprocessing
import uvicorn
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def ensure_venv():
    """Ensure we're running in the correct virtual environment"""
    if not hasattr(sys, 'cameo') and not sys.base_prefix != sys.prefix:
        logger.warning("Not running in a virtual environment!")
        return False
    return True


def run_api():
    """Run the FastAPI server"""
    from rpi_control.api.main import app
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )


def run_gui():
    """Run the PyQt GUI application"""
    from rpi_control.main import main as gui_main
    gui_main()


def main():
    # Verify virtual environment
    if not ensure_venv():
        logger.warning("Consider running this in your virtual environment")

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create processes
    api_process = multiprocessing.Process(target=run_api)
    gui_process = multiprocessing.Process(target=run_gui)

    try:
        logger.info("Starting API server...")
        api_process.start()

        logger.info("Starting GUI application...")
        gui_process.start()

        # Wait for processes
        api_process.join()
        gui_process.join()

    except KeyboardInterrupt:
        logger.info("\nShutting down gracefully...")
        if api_process.is_alive():
            api_process.terminate()
        if gui_process.is_alive():
            gui_process.terminate()

        api_process.join()
        gui_process.join()
        logger.info("Shutdown complete")


if __name__ == "__main__":
    main()
