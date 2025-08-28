import json
import os

from .report import Report

class Logger:

    def __init__(self, filepath: str = "log.txt", encoding: str = "utf-8"):
        self.filepath = filepath
        self.encoding = encoding

    def write_report(self, report: Report, separator: str = "-" * 80, flush: bool = True) -> None:
        report_id = report.bug_id
        if not isinstance(report, Report):
            raise TypeError("write_report expects a Report instance.")

        lines = report.to_log_lines()
        try:
            with open(self.filepath, "a", encoding=self.encoding) as f:
                for line in lines:
                    if "{" in line:
                        package_dir = os.path.dirname(__file__)
                        joined_path = os.path.join(
                            package_dir,
                            "json_state_saves",
                            f"bug_report{report_id}.json"
                                                   )
                        with open(joined_path,"w+") as file:
                            line = json.loads(line[line.index("{"):])
                            data = json.dumps(line,indent=2)
                            file.write(data)
                    else:
                        f.write(line + "\n")
                f.write(separator + "\n")
                if flush:
                    f.flush()
        except Exception as e:
            raise

    def create_json_file(self, ):
        pass

    def write_lines(self, lines: list, separator: str = "-" * 80) -> None:
        try:
            with open(self.filepath, "a", encoding=self.encoding) as f:
                for line in lines:
                    f.write(str(line) + "\n")
                f.write(separator + "\n")
                f.flush()
        except Exception as e:
            raise