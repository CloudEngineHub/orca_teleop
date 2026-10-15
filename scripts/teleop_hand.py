"""Teleoperate a physical ORCA hand.

This runs the same ingress + retargeter stack as ``teleop_urdf.py``, but the
sink dispatches joint commands to a connected ``OrcaHand`` instead of a viewer.
Start with ``--dry-run`` to validate the camera, gRPC and retargeter path
without dispatching anything to the motors.

The retargeter clamps every command to the model's joint ranges, but nothing
moves the hand before streaming starts. Park the hand near the pose you will
hold when the stream begins: the first dispatched command is a single step, so
a large gap between the hand's pose and the first retargeted pose is taken in
one jump.

Examples:
    # Validate the whole stack without moving the hand.
    python scripts/teleop_hand.py --local --dry-run

    # Teleoperate a right v2 hand from the local webcam.
    python scripts/teleop_hand.py --local \
        --model_path /path/to/v2/orcahand-right/config.yaml \
        --urdf_path /path/to/v2/models/urdf/orcahand_right_sem.urdf \
        --retarget-config src/orca_teleop/retargeting/configs/adaptive_analytical_orca.yaml

    # Wait for an external publisher instead of starting one.
    python scripts/teleop_hand.py --port 50052
"""

from __future__ import annotations

import argparse
import logging

from orca_teleop.ingress.server import DEFAULT_PORT
from orca_teleop.pipeline import OrcaHandSink, run, run_local

logger = logging.getLogger("teleop_hand")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Orca Hand teleoperation pipeline against a physical hand."
    )
    parser.add_argument("--model_path", default=None, help="OrcaHand model config")
    parser.add_argument(
        "--urdf_path", default=None, help="Hand URDF the retargeter solves against"
    )
    parser.add_argument(
        "--port", type=int, default=DEFAULT_PORT, help=f"gRPC port (default: {DEFAULT_PORT})"
    )
    parser.add_argument(
        "--hand",
        default="right",
        choices=["left", "right"],
        help="Hand side the local publisher tracks (default: right)",
    )
    parser.add_argument(
        "--home",
        action="store_true",
        help=(
            "Let initialisation drive the hand to its configured neutral pose. "
            "Off by default: that move is a real motion and can stall tendons if "
            "the hand starts far from neutral."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run the full stack but do not connect or dispatch to the motors",
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help="Also launch a local MediaPipe publisher for one-command teleop",
    )
    parser.add_argument(
        "--confidence", type=float, default=0.7, help="MediaPipe confidence (default: 0.7)"
    )
    parser.add_argument("--show-video", action="store_true", help="Show webcam feed with landmarks")
    parser.add_argument(
        "--retargeter",
        default="adaptive_analytical",
        choices=["rmsprop", "adaptive_analytical"],
        help="Retargeter backend (default: adaptive_analytical)",
    )
    parser.add_argument(
        "--retarget-config",
        default=None,
        help="YAML config for --retargeter adaptive_analytical",
    )
    parser.add_argument(
        "--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"]
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )

    sink = OrcaHandSink(
        model_path=args.model_path,
        connect_hardware=not args.dry_run,
        move_to_neutral=args.home,
    )
    if not args.dry_run and not args.home:
        logger.info(
            "Streaming to the motors. The hand is not pre-positioned; it holds its "
            "current pose until the first retargeted frame arrives."
        )

    if sink.handedness != args.hand:
        parser.error(
            f"Model is a {sink.handedness} hand but --hand is {args.hand}. "
            "The publisher would track the wrong hand."
        )

    if args.local:
        run_local(
            model_path=args.model_path,
            urdf_path=args.urdf_path,
            port=args.port,
            handedness=args.hand,
            confidence=args.confidence,
            show_video=args.show_video,
            sink=sink,
            retargeter_backend=args.retargeter,
            retargeter_config_path=args.retarget_config,
        )
    else:
        run(
            model_path=args.model_path,
            urdf_path=args.urdf_path,
            port=args.port,
            sink=sink,
            retargeter_backend=args.retargeter,
            retargeter_config_path=args.retarget_config,
        )


if __name__ == "__main__":
    main()
