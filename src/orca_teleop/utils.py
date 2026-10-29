import os
import time
from pathlib import Path

ORCAHAND_DESCRIPTION_DIR_ENV = "ORCAHAND_DESCRIPTION_DIR"
ORCAHAND_DESCRIPTION_DIR_DEFAULT = os.path.join(
    os.path.expanduser("~"), "Documents", "orcahand_description"
)


def infer_model_version(path: "str | os.PathLike | None") -> str:
    """Read the embodiment version out of an orca_core model path."""
    if path is None:
        return "v2"
    for part in Path(path).parts:
        if part.startswith("v") and part[1:].isdigit():
            return part
    return "v2"


def default_urdf_path(hand_type: str, version: str = "v2") -> str:
    """Resolve a hand URDF from the orcahand_description checkout.

    An ``_sem`` sibling wins when present: the published v2 export names joints
    after CAD parts, which nothing addressing ``<side>_<joint_id>`` can resolve.
    """
    base = os.environ.get(ORCAHAND_DESCRIPTION_DIR_ENV, ORCAHAND_DESCRIPTION_DIR_DEFAULT)
    urdf_dir = Path(base) / version / "models" / "urdf"
    for name in (f"orcahand_{hand_type}_sem.urdf", f"orcahand_{hand_type}.urdf"):
        candidate = urdf_dir / name
        if candidate.exists():
            return str(candidate)
    raise FileNotFoundError(
        f"No {hand_type} {version} URDF under {urdf_dir}. Clone "
        "https://github.com/orcahand/orcahand_description there, set "
        f"{ORCAHAND_DESCRIPTION_DIR_ENV}, or pass a URDF path explicitly."
    )


class RateTicker:
    """Sleep to maintain a fixed loop rate.

    Usage::

        RENDER_FPS = 30
        limiter = RateLimiter(dt=1 / RENDER_FPS)
        while running:  # loops at RENDER_FPS
            # ... do work here
            limiter.tick()
    """

    def __init__(self, dt: float) -> None:
        self._dt = dt
        self._next_tick = time.perf_counter()

    def tick(self) -> None:
        """Sleep until the next scheduled tick, then advance the schedule.

        If the deadline was missed the schedule resets to now, preventing
        a spiral of back-to-back zero-sleep ticks.
        """
        self._next_tick += self._dt
        now = time.perf_counter()
        sleep_s = self._next_tick - now
        if sleep_s > 0:
            time.sleep(sleep_s)
        else:
            self._next_tick = now
