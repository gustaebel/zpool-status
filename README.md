# zpool-status

Parse output from the `zpool status` ZFS command in Python.

## About

This project contains:

1. A Python module `zpool_status.py` that converts `zpool status` output into a
   Python datastructure.
2. A Python script `zpool-status` that serves as a drop-in replacement
   for the `zpool status` command that produces JSON output.

## Install

Install `zpool-status` using pip:

```sh
$ pip install zpool-status
```

## Command-line interface

The `zpool-status` script provides a command-line interface that is identical
to the one of `zpool-status(1)`. The only difference is that `zpool-status`
produces JSON output.

```
zpool-status [-c [script1[,script2]...]] [-igLpPstv] [-T d|u] [pool] ... [interval [count]]
```

> [!NOTE]
> The `-D` and `-x` options are not supported.

## Example

Suppose we get the following output from `zpool status`:

```
$ zpool status -v tank
  pool: tank
 state: UNAVAIL
status: One or more devices are faulted in response to IO failures.
action: Make sure the affected devices are connected, then run 'zpool clear'.
   see: http://www.sun.com/msg/ZFS-8000-HC
 scrub: scrub completed after 0h0m with 0 errors on Tue Feb  2 13:08:42 2010
config:

        NAME        STATE     READ WRITE CKSUM
        tank        UNAVAIL      0     0     0  insufficient replicas
          c1t0d0    ONLINE       0     0     0
          c1t1d0    UNAVAIL      4     1     0  cannot open

errors: Permanent errors have been detected in the following files: 

/tank/data/aaa
/tank/data/bbb
/tank/data/ccc
```

The following shell command line:

```sh
$ zpool-status -v tank
```

is identical to the this Python code:

```python
import json
from zpool_status import ZPool

zpool = ZPool("tank", options=["-v"])
status = zpool.get_status()

print(json.dumps(status, indent=2))
```

Both produce this output:

```json
{
  "pool": "tank",
  "state": "UNAVAIL",
  "status": "One or more devices are faulted in response to IO failures.",
  "action": "Make sure the affected devices are connected, then run 'zpool clear'.",
  "see": "http://www.sun.com/msg/ZFS-8000-HC",
  "scrub": "scrub completed after 0h0m with 0 errors on Tue Feb 2 13:08:42 2010",
  "config": [
    {
      "name": "tank",
      "state": "UNAVAIL",
      "read": 0,
      "write": 0,
      "cksum": 0,
      "message": "insufficient replicas",
      "type": "pool",
      "devices": [
        {
          "name": "c1t0d0",
          "state": "ONLINE",
          "read": 0,
          "write": 0,
          "cksum": 0,
          "type": "device"
        },
        {
          "name": "c1t1d0",
          "state": "UNAVAIL",
          "read": 4,
          "write": 1,
          "cksum": 0,
          "message": "cannot open",
          "type": "device"
        }
      ]
    }
  ],
  "errors": [
    "Permanent errors have been detected in the following files:",
    "",
    "/tank/data/aaa",
    "/tank/data/bbb",
    "/tank/data/ccc"
  ]
}
```
