# orca_teleop

Repo for teleoperating the ORCA Hand consisting of an Ingress Source (for example Mediapipe, Apple Vision Pro, Rokoko Gloves, etc.) and a URDF-based Retargeter.

The repository follows a standard `src/` layout:

```text
src/orca_teleop/
tests/
```

## Setup

1. Install with `uv`. The `teleop` extra pulls everything the webcam-to-hand
   pipeline and the 3D viewer need:

   ```bash
   uv sync --extra teleop --extra test
   ```

2. Get the hand models. On v2 the retargeter solves on
   `v2/models/urdf/orcahand_right_sem.urdf`, which for now exists only on the
   `release/15-10-26` branch of
   [orcahand_description](https://github.com/orcahand/orcahand_description).
   Check that branch out in a folder named exactly `orcahand_description` (the
   3D viewer finds the meshes by that name):

   ```bash
   git clone -b release/15-10-26 git@github.com:orcahand/orcahand_description.git ~/Documents/orcahand_description
   ```

   `~/Documents/orcahand_description` is the default location. For another
   location, set `ORCAHAND_DESCRIPTION_DIR` to that folder. Without the `_sem`
   file, v2 falls back to the CAD-named URDF and fails with a message about
   `joint_name_aliases`.

3. Calibrate the hand before the first teleop session, with orca_ui or
   orca_core's `scripts/calibrate.py`. On an uncalibrated hand,
   `orca-teleop-hand` starts the full calibration by itself.

## Run

Check the webcam tracking in the 3D viewer first, with no hand attached:

```bash
uv run --extra teleop orca-teleop-urdf --show-video
```

Then drive the hand. `--model_path` is the path of the hand's `config.yaml`
(orca_core stores the calibration next to it); orca_ui keeps it in
`~/.orca_ui/hands/<hand>/config.yaml`. Only one program can hold the hand's
serial port, so press Disconnect in orca_ui first.

```bash
uv run --extra teleop orca-teleop-hand --model_path ~/.orca_ui/hands/orcahand-right/config.yaml --show-video
```

Useful flags: `--dry-run` runs everything except the hand; `--home` moves the
hand to its neutral pose on connect; `--camera-index N` picks another camera
(often needed on Linux). Quitting drives the hand back to its zero pose before
torque goes off, so keep it clear of objects.

## Retargeting

The default teleop backend is `adaptive_analytical`, an Orca-native port of the Wuji-style
analytical retargeting strategy. It uses the full MediaPipe hand pose, explicit Orca frame
mappings from YAML, Pinocchio forward kinematics/Jacobians, and `nlopt` for bounded
per-frame optimization.

It loads `src/orca_teleop/retargeting/configs/adaptive_analytical_orca_tuned.yaml` by
default. Pass `--retarget-config path/to/config.yaml` to experiment with frame maps or
weights. `--retargeter rmsprop` selects the legacy fingertip key-vector retargeter for
comparison.

Run the test suite from the repository root with:

```bash
uv run --extra teleop --extra test pytest
```

## Record Quest WebXR demonstrations on a physical OrcaHand

The dataset recorder includes the complete Quest ingress: it serves its own
WebXR page, receives 25 hand joints from Quest Browser over a WebSocket, maps
them to the same 21-point layout used by the original in-hand MuJoCo
demonstrations, retargets them, and drives the physical hand.

Start by installing the recording stack (cameras, Quest WebXR, adaptive
retargeter, and LeRobot):

```bash
uv sync --extra learning
```

First validate the motion with the simulated sink:

```bash
uv run python scripts/record_dataset.py \
  --repo-id "$HF_USERNAME/orca-quest-safety-check" \
  --task "check WebXR retargeting" \
  --backend sim \
  --source metaquest \
  --local \
  --hand right \
  --episode-end space \
  --num-episodes 1
```

For the real hand, run:

```bash
uv run python scripts/record_dataset.py \
  --repo-id "$HF_USERNAME/orca-quest-hardware" \
  --task "pick up the block" \
  --backend hardware \
  --source metaquest \
  --local \
  --hand right \
  --episode-end space \
  --num-episodes 20 \
  --camera front:0
```

Hold the hand still while the retargeter calibrates. Press Space to save the
current episode and begin the next; press `q` or Escape to finish. The command
records measured hardware joint positions as `observation.state`, commanded
joint positions as `action`, and each configured camera as
`observation.images.<name>`.

The command hosts the Quest page on port `8765`. WebXR requires a secure
context, so expose it in a second terminal:

```bash
ngrok http 8765
```

Open the resulting HTTPS URL in Quest Browser and tap **Start hand tracking**.
For a wired setup, use:

```bash
adb reverse tcp:8765 tcp:8765
```

Then open `http://localhost:8765` in Quest Browser; browsers treat localhost as
a secure context.

For a split-machine setup, omit `--local` on the robot and run the publisher on
the Quest-side machine:

```bash
uv run python -m orca_teleop.ingress.metaquest.publisher \
  --server ROBOT_IP:50051 \
  --hand right
```

The publisher machine hosts the WebXR page and forwards the reduced landmarks
to the robot over gRPC. Keep `--source metaquest` on the recorder so it treats
the incoming frames as the WebXR convention. The live adapter deliberately
does not apply the legacy HTS/Unity handedness flip.
