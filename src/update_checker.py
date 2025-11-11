"""
Update Checker Service
Polls API for updates and performs rolling updates
"""

import os
import sys
import time
import subprocess
import requests
from pathlib import Path
from src.config import Config
from src.logger import setup_logger
from src.api_client import APIClient

logger = setup_logger(__name__)


class UpdateChecker:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.current_version = self._get_current_version()
        self.api_client = APIClient()

    def _get_current_version(self):
        """Get current git commit hash"""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            return result.stdout.strip()
        except:
            return 'unknown'

    def check_for_update(self):
        """Check API if update is available"""
        current_version = self.current_version
        logger.info(f"Current version: {current_version}")
        
        # Use APIClient to check for updates
        update_available, target_version = self.api_client.check_update(current_version)
        
        if update_available:
            logger.info(f"Update available: {target_version}")
        else:
            logger.debug("No updates available")
        
        return update_available, target_version

    def perform_update(self, target_version=None):
        """Perform git pull and restart services"""
        logger.info("Starting update process...")

        try:
            # 1. Stop services gracefully
            logger.info("Stopping services...")
            subprocess.run(['sudo', 'systemctl', 'stop', 'bacnet-reader.service'])
            subprocess.run(['sudo', 'systemctl', 'stop', 'heartbeat.service'])

            # 2. Backup current state
            logger.info("Creating backup...")
            subprocess.run(['git', 'stash'], cwd=self.project_root)

            # 3. Pull updates
            logger.info("Pulling updates from git...")
            result = subprocess.run(
                ['git', 'pull', 'origin', 'master'],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                logger.error(f"Git pull failed: {result.stderr}")
                self._rollback()
                return False

            # 4. Update dependencies if requirements changed
            logger.info("Updating dependencies...")
            subprocess.run([
                sys.executable, '-m', 'pip',
                'install', '-r', 'requirements.txt'
            ], cwd=self.project_root)

            # 5. Restart services
            logger.info("Restarting services...")
            subprocess.run(['sudo', 'systemctl', 'start', 'bacnet-reader.service'])
            subprocess.run(['sudo', 'systemctl', 'start', 'heartbeat.service'])

            # 6. Report success
            logger.info("✓ Update completed successfully")
            # self._report_update_status(True, self._get_current_version())
            return True

        except Exception as e:
            logger.error(f"Update failed: {e}")
            self._rollback()
            self._report_update_status(False, str(e))
            return False

    def _rollback(self):
        """Rollback to previous version"""
        logger.warning("Rolling back to previous version...")
        try:
            subprocess.run(['git', 'stash', 'pop'], cwd=self.project_root)
            subprocess.run(['sudo', 'systemctl', 'start', 'bacnet-reader.service'])
            subprocess.run(['sudo', 'systemctl', 'start', 'heartbeat.service'])
        except Exception as e:
            logger.error(f"Rollback failed: {e}")

    def _report_update_status(self, success, version_or_error):
        """Report update result to API"""
        try:
            requests.post(
                Config.API_URL + "update-status",
                json={
                    'device_id': Config.DEVICE_NAME,
                    'success': success,
                    'version': version_or_error if success else None,
                    'error': None if success else version_or_error
                },
                timeout=10
            )
        except:
            pass

    def run(self):
        """Main loop - check for updates every 5 minutes"""
        logger.info("Update checker started")

        while True:
            try:
                update_available, target_version = self.check_for_update()

                if update_available:
                    logger.info(f"Update available: {target_version}")
                    # self.perform_update(target_version)
                else:
                    logger.debug("No updates available")

            except Exception as e:
                logger.error(f"Update check error: {e}")

            time.sleep(300)  # Check every 5 minutes


def main():
    checker = UpdateChecker()
    checker.run()


if __name__ == "__main__":
    main()
