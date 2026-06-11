import logging

logger = logging.getLogger('etl')


class BaseETLComponent:
    def __init__(self, execution_id=None):
        self.execution_id = execution_id

    def log(self, level, message, phase='', details=None):
        log_data = {
            'execution_id': self.execution_id,
            'level': level,
            'phase': phase,
            'message': message,
            'details': details,
        }
        getattr(logger, level, logger.info)(f"[{phase}] {message}")
        return log_data
