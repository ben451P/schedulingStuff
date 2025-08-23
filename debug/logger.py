from typing import Callable

from .report import Report

class Logger:
    """
    Responsible only for writing text logs. Keeps I/O concerns separate from Report.
    """

    def __init__(self, filepath: str = "log.txt", encoding: str = "utf-8"):
        self.filepath = filepath
        self.encoding = encoding

    def write_report(self, report: Report, separator: str = "-" * 80, flush: bool = True) -> None:
        if not isinstance(report, Report):
            raise TypeError("write_report expects a Report instance.")

        lines = report.to_log_lines()
        try:
            with open(self.filepath, "a", encoding=self.encoding) as f:
                for line in lines:
                    f.write(line + "\n")
                f.write(separator + "\n")
                if flush:
                    f.flush()
        except Exception as e:
            raise

    def write_lines(self, lines: list, separator: str = "-" * 80) -> None:
        """
        Generic writer for a list of strings.
        """
        try:
            with open(self.filepath, "a", encoding=self.encoding) as f:
                for line in lines:
                    f.write(str(line) + "\n")
                f.write(separator + "\n")
                f.flush()
        except Exception as e:
            raise