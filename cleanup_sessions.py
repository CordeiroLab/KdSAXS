import os
import shutil
from datetime import datetime, timedelta
from config import BASE_DIR
from scripts.error_handling import logger

def cleanup_old_sessions(days_to_keep=3):
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

if __name__ == "__main__":
    logger.info("Starting session cleanup")
    cleanup_old_sessions()
    logger.info("Session cleanup completed")
