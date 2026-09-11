from typing import Any
from pathlib import Path
from csv import DictWriter


class Logger:
    def __init__(self, logfile: Path, header: list[str]) -> None:
        if not logfile.suffix == ".csv":
            raise ValueError("`logfile` must be of type '.csv'.")

        self.logfile: Path = logfile
        self.__header: list[str] = header
        self.data: list[dict[str, Any]] = []

    def record(self, entry: dict[str, Any]) -> None:
        for key, _ in entry.items():
            if key not in self.__header:
                raise RuntimeError("Header mismatch: unrecognized key '%s'" % (key))

        _entry: dict[str, Any] = {}
        for key in self.__header:
            _entry[key] = entry[key]
        self.data.append(_entry)
    
    def dump(self) -> None:
        with open(self.logfile, "w", newline="", encoding="utf-8") as file:
            writer: DictWriter = DictWriter(file, self.__header)
            writer.writeheader()
            writer.writerows(self.data)
