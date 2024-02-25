import os
import sys
import json
import difflib

from zpool_status import ZPool

for name in os.listdir("test_data"):
    test_path = os.path.join("test_data", name)
    result_path = os.path.join("test_results", name)

    with open(test_path) as fobj:
        output = ZPool.get_status_from_output(fobj.read())
        a = json.dumps(output, indent=2).splitlines()

    with open(result_path) as fobj:
        b = fobj.read().splitlines()

    diff = list(difflib.unified_diff(a, b, fromfile=test_path, tofile=result_path))
    if diff:
        text = "\n".join(line.rstrip() for line in diff)

        try:
            from rich.console import Console
            from rich.syntax import Syntax
        except ImportError:
            print(text)
        else:
            console = Console()
            syntax = Syntax(text, "diff", theme="ansi_light")
            console.print(syntax)

        sys.exit(1)
