# custom_logger.py

import datetime
import sys
import os

class CustomLogger:
    def __init__(self, log_file='app.log'):
        self.log_level = os.getenv('LOG_LEVEL').upper() if os.getenv('LOG_LEVEL') else 'INFO' # type: ignore
        self.write_log = str(os.getenv('WRITE_LOG')).lower()
        if self.write_log == 'true': # type: ignore
            path = os.getenv('LOG_PATH')
            if path:
                self.log_file = os.path.join(path, log_file)
            else:
                self.log_file = log_file

    def _log(self, level, message):
        levels = {'DEBUG': 3,'INFO': 2, 'WARN': 1, 'ERROR': 0, 'FATAL': -1 }
        if levels[level.upper()] <= levels[self.log_level]:
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            log_message = f"[{timestamp}] - {level.upper()} - PID: {os.getpid()} - {message}"
            print(log_message)
            
            if self.write_log == 'true': # type: ignore
                with open(self.log_file, 'a') as file:
                    file.write(log_message + '\n')

    def debug(self, message):
        self._log('debug', message)
        
    def info(self, message):
        self._log('info', message)

    def warn(self, message):
        self._log('warn', message)

    def error(self, message):
        self._log('error', message)
    
    def fatal(self, message):
        self._log('fatal', message)
        sys.exit()
