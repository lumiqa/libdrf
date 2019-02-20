import multiprocessing
from importlib import import_module

from django.conf import settings

DEFAULTS = {
    "PASS_HEADERS": ["HTTP_USER_AGENT", "HTTP_COOKIE"],
    "DEFAULT_CONTENT_TYPE": "application/json",
    "USE_HTTPS": False,
    "EXECUTE_PARALLEL": False,
    "CONCURRENT_EXECUTOR": "libdrf.batch.executors.ThreadBasedExecutor",
    "NUM_WORKERS": multiprocessing.cpu_count() * 4,
    "ADD_DURATION_HEADER": True,
    "DURATION_HEADER_NAME": "libdrf.batch.duration",
    "MAX_LIMIT": 20,
}


USER_DEFINED_SETTINGS = getattr(settings, "LIBDRF_BATCH", {})


def import_class(class_path):
    """
        Imports the class for the given class name.
    """
    module_name, class_name = class_path.rsplit(".", 1)
    module = import_module(module_name)
    cls = getattr(module, class_name)
    return cls


class BatchSettings(object):

    """
        Allow API settings to be accessed as properties.
    """

    def __init__(self, user_settings=None, defaults=None):
        self.user_settings = user_settings or {}
        self.defaults = defaults or {}
        self.executor = self._executor()

    def _executor(self):
        """
            Creating an ExecutorPool is a costly operation. Executor needs to be instantiated only once.
        """
        if self.EXECUTE_PARALLEL is False:
            executor_path = "libdrf.batch.executors.SequentialExecutor"
            executor_class = import_class(executor_path)
            return executor_class()
        else:
            executor_path = self.CONCURRENT_EXECUTOR
            executor_class = import_class(executor_path)
            return executor_class(self.NUM_WORKERS)

    def __getattr__(self, attr):
        """
            Override the attribute access behavior.
        """

        if attr not in self.defaults.keys():
            raise AttributeError("Invalid API setting: '%s'" % attr)

        try:
            # Check if present in user settings
            val = self.user_settings[attr]
        except KeyError:
            # Fall back to defaults
            val = self.defaults[attr]

        # Cache the result
        setattr(self, attr, val)
        return val


batch_settings = BatchSettings(USER_DEFINED_SETTINGS, DEFAULTS)
