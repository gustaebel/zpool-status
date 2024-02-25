# zpool_status.py

Parse output from `zpool-status(1)`.

## About

The `zpool_status.py` Python module calls the `zpool status` command, parses
its output and returns the information as a dictionary.

## Install

Install `zpool_status.py` using pip:

```sh
$ pip install zpool-status
```

## Command-line interface

`zpool_status.py` provides a limited command-line interface. For each pool name
argument it prints the pool information as a json object. When called with no
arguments, it prints pool information for all imported pools.

```sh
$ python -m zpool_status tank
```

## Example

```sh
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

```python
import zpool_status

zpool = ZPool("tank")
status = zpool.get_status()

print(json.dumps(status, indent=2))
```

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
