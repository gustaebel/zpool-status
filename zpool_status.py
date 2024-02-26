# Inspired by: https://github.com/dev-sngy/zpool_status
#
# Cp. zpool-status(1), zpoolconcepts(7).
#
# Copyright (c) 2024, Lars Gustäbel <lars@gustaebel.de>

"""Parse output from 'zpool status'.
"""

import re
import sys
import enum
import json
import subprocess
import collections


class MissingPoolError(Exception):
    """Raised if the respective pool is not imported.
    """

DeviceRow = collections.namedtuple("DeviceRow", "indent name data")

class DeviceState(enum.StrEnum):
    """Device health/state.
    """
    DEGRADED = "DEGRADED"
    FAULTED = "FAULTED"
    OFFLINE = "OFFLINE"
    ONLINE = "ONLINE"
    REMOVED = "REMOVED"
    UNAVAIL = "UNAVAIL"


class ZPool:
    """Class representing a (possibly imported) zpool.
    """

    virtual_devices = ("mirror", "raidz", "draid", "spare", "logs", "dedup", "special", "cache",
                       "replacing")
    default_options = ["-v", "-p", "-c", "lsblk"]

    def __init__(self, name, options=None, check_name=True):
        if check_name and name not in self.list_names():
            raise MissingPoolError(f"pool {name!r} does not exist")

        self.options = options if options is not None else self.default_options
        self.name = name

    @classmethod
    def get_status_from_output(cls, output):
        """Parse 'zpool status' output from a string.
        """
        assert isinstance(output, str)
        for line in output.splitlines():
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if key == "pool":
                name = value
                break
        else:
            raise MissingPoolError("unable to get pool name from output")

        return cls(name, check_name=False).parse_status_output(output)

    @classmethod
    def list_names(cls):
        """Return a list of names from imported pools.
        """
        return [name.split()[0]
                for name in subprocess.check_output(["zpool", "list", "-H"], text=True)\
                        .splitlines()]

    def walk(self, config=None):
        """Walk over all virtual and regular devices in the pool.
        """
        if config is None:
            config = self.get_status()["config"]

        for device in config:
            yield device
            for key in "virtual devices", "devices":
                if key in device:
                    yield from self.walk(device[key])

    def get_status(self):
        """Return the output of 'zpool status <name>' as a dictionary.
        """
        return self.parse_status_output(self.get_status_output())

    def get_status_output(self):
        """Return the output of 'zpool status <name>' as a string.
        """
        return subprocess.check_output(["zpool", "status"] + self.options + [self.name],
                                       text=True)

    def parse_status_output(self, output):
        """Parse output from 'zpool status <pool>' and return a dictionary.
        """
        # Split the output into a list of [key, value, key, value, key, ...]
        data = [part for part in re.split(r"^\s*([a-z]+):", output, flags=re.MULTILINE)
                if part.strip()]

        # Combine the key-value list into a dictionary and clean up the values.
        result = {key: self._clean_up_value(key, value)
                  for key, value in zip(data[0::2], data[1::2])}

        result["state"] = DeviceState[result["state"]]
        if "config" in result:
            result["config"] = self._parse_config_lines(result["config"])

        return result

    def _clean_up_value(self, key, value):
        """Preprocess a value depending on its key.
        """
        # pylint:disable=no-else-return
        if key == "config":
            # Return a list of lines with indentation untouched.
            return value.strip("\n").splitlines()
        elif key in ("scan", "errors"):
            # Return a list of normalized lines.
            return [line.strip() for line in value.splitlines()]
        else:
            # Fold newlines and multiple whitespaces into single spaces.
            return re.sub(r"\s+", " ", value).strip()

    def _strip_config_lines(self, lines):
        """Strip leading whitespace from a list of config lines without changing their indentation.
           Usually, config lines start with a TAB or 8 spaces.
        """
        lines = [line.replace("\t", "        ") for line in lines]

        header_line = lines[0]
        leading_whitespace = re.match(r"(\s*)", header_line).group(1)

        result = []
        for line in lines:
            if line.startswith(leading_whitespace):
                result.append(line[len(leading_whitespace):])
            else:
                raise ValueError(f"malformed left whitespace in line: {line!r}")
        return result

    def _parse_number(self, value):
        """Convert a number string to an integer.
        """
        multiplier = 1
        if value[-1] == "K":
            multiplier = 1024
        elif value[-1] == "M":
            multiplier = 1024**2
        elif value[-1] == "G":
            multiplier = 1024**3
        elif value[-1] == "T":
            multiplier = 1024**4
        elif value[-1] == "P":
            multiplier = 1024**5

        value = value.rstrip("KMGTP")
        return int(float(value) * multiplier)

    def _detect_indent(self, line):
        """Return the number of leading spaces of a line.
        """
        return len(line) - len(line.lstrip())

    def _get_name(self, line):
        """Extract the device name from a config line.
        """
        return line.split()[0]

    def _process_config_line(self, header_line, line):
        """Process a device line from the config and return a dictionary with prepared values.
        """
        device_info = {}
        for name, start, end in self._get_header_columns(header_line, line):
            value = line[start:end].strip()

            if not value:
                # Do not include empty values in the device info.
                pass

            elif value == "-":
                device_info[name] = None

            elif name in ("read", "write", "cksum", "size"):
                try:
                    device_info[name] = self._parse_number(value)
                except ValueError:
                    device_info[name] = value

            else:
                device_info[name] = value

        return device_info

    def _parse_config_lines(self, config_lines):
        """Parse a list of config lines and return a hierarchy of (virtual) devices as a dictionary.
        """
        lines = self._strip_config_lines(config_lines)

        # Normally, the headers are NAME STATE READ WRITE CKSUM, but there may be more columns
        # in case the -c option was used. The last column is optional and contains a per-device
        # message (e.g. "not found", "resilvering" etc.).
        header_line = lines.pop(0)
        rows = [DeviceRow(self._detect_indent(line),
                          self._get_name(line),
                          self._process_config_line(header_line, line))
                for line in lines]

        return self._parse_config_rows(rows)

    def _get_header_columns(self, header_line, line):
        """Split a single device line into columns based on the config header line.
        """
        matches_header = list(re.finditer(r"(\S+)", header_line))
        matches_line = list(re.finditer(r"(\S+)", line))

        columns = []
        for i, match in enumerate(matches_header):
            name = match.group(1).lower()
            try:
                if name == "name":
                    # The NAME column is left-justified and its width is variable depending on the
                    # size of the device name. The next column STATE is left-justified as well, so
                    # we take the start of STATE's header name as the end of the NAME column.
                    start = match.start(1)
                    end = matches_header[i+1].start(1)

                elif name == "state":
                    # The STATE column is left-justified, but the next column READ is
                    # right-justified, so we split at the end of the STATE columns' value.
                    start = match.start(1)
                    end = matches_line[i].end(1)

                elif name == "read":
                    # The READ column is the first right-justified column. We use the end of the
                    # value of the STATE column as the starting point.
                    start = matches_line[i-1].end(1)
                    end = match.end(1)

                else:
                    # All other columns are right justified, so it should be safe to use the end of
                    # the previous column's header as the starting point.
                    start = matches_header[i-1].end(1)
                    end = match.end(1)

                columns.append((name, start, end))

            except IndexError:
                break

        # Append the optional per-device message column starting from the end of the previous
        # column.
        columns.append(("message", end, len(line)))

        return columns

    def _parse_config_rows(self, rows, level=0):
        """Parse a list of device lines (DeviceRow objects) and organize them into a hierarchy of
           (virtual) devices. The relation between devices is based on the indentation level of
           each device line.
        """
        config = []
        while rows and rows[0].indent >= level:
            row = rows.pop(0)

            # If the NAME of the row is the same as the pool name, this is the pool root device.
            # Otherwise the NAME will be a virtual device like mirror, raidz1, logs, cache,
            # replacing etc. or the path of a block device or file.
            if row.name == self.name or row.name.startswith(self.virtual_devices):
                row.data["type"] = "pool" if row.name == self.name else "virtual device"

                # Check if there are device rows following this with a deeper indentation level.
                devices = self._parse_config_rows(rows, row.indent + 1)
                if devices:
                    if devices[0]["type"] == "virtual device":
                        row.data["virtual devices"] = devices
                    else:
                        row.data["devices"] = devices

            else:
                if row.name.startswith("/dev") or not row.name.startswith("/"):
                    row.data["type"] = "device"
                else:
                    row.data["type"] = "file"

            if "state" in row.data:
                row.data["state"] = DeviceState[row.data["state"]]

            config.append(row.data)

        return config


if __name__ == "__main__":
    # Read zpool status output from stdin. This is just for testing purposes.
    status = ZPool.get_status_from_output(sys.stdin.read())
    print(json.dumps(status, indent=2))
