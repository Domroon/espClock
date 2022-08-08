CRITICAL = 50
ERROR = 40
WARNING = 30
INFO = 20
DEBUG = 10

class Logger:
    def __init__(self, log_level=INFO):
        self.log_level = log_level

    def build_string(self, *args):
        output_str = ""

        for arg in args:
            output_str = output_str + " " + str(arg)

        return output_str

    def critical(self, *args):
        if self.log_level <= CRITICAL:
            print("[CRITICAL]", self.build_string(*args))

    def error(self, *args):
        if self.log_level <= ERROR:
            print("[ERROR]", self.build_string(*args))

    def warning(self, *args):
        if self.log_level <= WARNING:
            print("[WARNING]", self.build_string(*args))

    def info(self, *args):
        if self.log_level <= INFO:
            print("[INFO]", self.build_string(*args))

    def debug(self, *args):
        if self.log_level <= DEBUG:
            print("[DEBUG]", self.build_string(*args))
