"""Thin wrapper; the entry point lives in ``orca_teleop.cli``.

Installed as the ``orca-teleop-hand`` console script, so this file is
only for running from a source checkout.
"""

from orca_teleop.cli import teleop_hand

if __name__ == "__main__":
    teleop_hand()
