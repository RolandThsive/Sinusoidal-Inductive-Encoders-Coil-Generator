"""The generator package (Run, Checks, Stator, Rotor, Core).  Importing it puts the Parameters folder, which
sits next to the Generator folder, on the import path, so every module can `import Parameters`.  It also stops at
once, with a clear message, on a Python older than 3.11 (the Dual Coil Set Generator imports this package too)."""
import os
import sys

if sys.version_info < (3, 11):
    raise SystemExit(f"The coil generators need Python 3.11 or newer; this is Python {sys.version.split()[0]}. "
                     f"See requirements.txt.")

_PARAMETERS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Parameters")
if _PARAMETERS not in sys.path:
    sys.path.insert(0, _PARAMETERS)
