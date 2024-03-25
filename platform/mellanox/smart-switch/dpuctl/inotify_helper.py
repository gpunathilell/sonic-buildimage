"""Helper code for Inotify Implementation for reading file until timeout"""
import os
import errno
import inotify.adapters

try:
    from sonic_py_common.logger import Logger
    from sonic_platform import utils
except ImportError as e:
    raise ImportError(str(e) + '- required module not found') from e

logger = Logger()

class InotifyHelper():
    """Helper Code for Inotify Implmentation"""
    def __init__(self,file_path):
        self.file_path = file_path
        self.inotify_obj = inotify.adapters.Inotify()
        if not self.inotify_obj:
            logger.log_error("INOTIFY adapter error!")
            raise AssertionError ("INOTIFY is not present!")
        if not os.path.exists(self.file_path):
            logger.log_error(f"{self.file_path} does not exist")
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), self.file_path)

    def add_watch(self,timeout,expected_value):
        """Waits for changes in file until specified time and
          compares written value to expected value"""
        self.inotify_obj.add_watch(self.file_path, mask=inotify.constants.IN_CLOSE_WRITE)
        for event in self.inotify_obj.event_gen(timeout_s = timeout,yield_nones = False):
            read_value = utils.read_int_from_file(self.file_path,raise_exception=True)
            if read_value == expected_value:
                return read_value
        read_value = utils.read_int_from_file(self.file_path,raise_exception=True)
        if read_value != expected_value:
            return None
        return read_value
