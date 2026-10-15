"""Thin wrapper; the entry point lives in ``orca_teleop.cli``.

Installed as the ``orca-teleop-urdf`` console script, so this file is
only for running from a source checkout.
"""

from orca_teleop.cli import teleop_urdf

if __name__ == "__main__":
    teleop_urdf()
