import os
import shutil
from datetime import datetime, timedelta
import threading
import time
from config import BASE_DIR
from scripts.error_handling import logger

def cleanup_sessions(days_to_keep=2):
    """
    Clean up session directories older than specified days
    """
    sessions_dir = os.path.join(BASE_DIR, "output_data", "sessions")
    if not os.path.exists(sessions_dir):
        logger.info("No sessions directory found")
        return

    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    
    try:
        for session_name in os.listdir(sessions_dir):
            session_path = os.path.join(sessions_dir, session_name)
            
            # Extract timestamp from session directory name
            # Format: session_XXXXXXXX_YYYYMMDD_HHMMSS
            try:
                timestamp_str = '_'.join(session_name.split('_')[2:])  # Get YYYYMMDD_HHMMSS
                session_date = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                
                if session_date < cutoff_date:
                    shutil.rmtree(session_path)
                    logger.info(f"Deleted old session: {session_name}")
            
            except (IndexError, ValueError) as e:
                logger.warning(f"Could not parse date from session directory: {session_name}. Error: {str(e)}")
                continue
            except Exception as e:
                logger.error(f"Error processing session {session_name}: {str(e)}")
                continue
                
    except Exception as e:
        logger.error(f"Error during session cleanup: {str(e)}")

def periodic_cleanup(interval_days=3):
    while True:
        cleanup_sessions()
        time.sleep(interval_days * 24 * 60 * 60)

def start_cleanup_thread():
    cleanup_thread = threading.Thread(target=periodic_cleanup, daemon=True)
    cleanup_thread.start()

if __name__ == "__main__":
    start_cleanup_thread()
