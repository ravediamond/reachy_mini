"""MCP server for Reachy Mini daemon.

Single-file, self-contained. Zero changes to existing code.
Enable with: reachy-mini-daemon --enable-mcp
Requires: pip install reachy_mini[openclaw]
"""

from __future__ import annotations

import math
from collections.abc import Callable
from uuid import UUID

import numpy as np
from fastmcp import FastMCP

from reachy_mini.daemon.backend.abstract import Backend
from reachy_mini.io.protocol import MotorControlMode
from reachy_mini.motion.recorded_move import RecordedMoves

from ..models import XYZRPYPose
from .move import create_move_task, stop_move_task

mcp = FastMCP("reachy-mini")

_get_backend: Callable[[], Backend] | None = None


def init(get_backend: Callable[[], Backend]) -> None:
    """Wire up backend access. Called once after daemon.start() in lifespan."""
    global _get_backend  # noqa: PLW0603
    _get_backend = get_backend


def _backend() -> Backend:
    if _get_backend is None:
        raise RuntimeError("MCP server not initialized — call mcp_server.init() first")
    return _get_backend()


# --- Movement ---


@mcp.tool()
async def goto(
    duration: float,
    head_yaw: float | None = None,
    head_pitch: float | None = None,
    head_roll: float | None = None,
    body_yaw: float | None = None,
    left_antenna: float | None = None,
    right_antenna: float | None = None,
) -> dict:
    """Move the robot. All angles in degrees. Returns the move UUID.

    Safety limits: head pitch/roll ±40°, head yaw ±180°, body yaw ±160°.
    """
    b = _backend()

    head = None
    if any(v is not None for v in [head_yaw, head_pitch, head_roll]):
        pose = XYZRPYPose(
            yaw=math.radians(head_yaw or 0.0),
            pitch=math.radians(head_pitch or 0.0),
            roll=math.radians(head_roll or 0.0),
        )
        head = pose.to_pose_array()

    antennas = None
    if left_antenna is not None or right_antenna is not None:
        antennas = np.array(
            [
                math.radians(left_antenna or 0.0),
                math.radians(right_antenna or 0.0),
            ]
        )

    body = math.radians(body_yaw) if body_yaw is not None else None

    task = create_move_task(
        b.goto_target(head=head, antennas=antennas, body_yaw=body, duration=duration)
    )
    return {"uuid": str(task.uuid)}


@mcp.tool()
async def wake_up() -> dict:
    """Wake up the robot."""
    task = create_move_task(_backend().wake_up())
    return {"uuid": str(task.uuid)}


@mcp.tool()
async def goto_sleep() -> dict:
    """Put the robot to sleep."""
    task = create_move_task(_backend().goto_sleep())
    return {"uuid": str(task.uuid)}


@mcp.tool()
async def stop_move(uuid: str) -> dict:
    """Stop a running move by its UUID."""
    return await stop_move_task(UUID(uuid))


@mcp.tool()
async def play_recorded_move(dataset: str, move_name: str) -> dict:
    """Play a named recorded move from a HuggingFace dataset.

    Example: dataset='pollen-robotics/reachy-mini-emotions-library', move_name='happy'
    """
    moves = RecordedMoves(dataset)
    move = moves.get(move_name)
    task = create_move_task(_backend().play_move(move))
    return {"uuid": str(task.uuid)}


# --- State ---


@mcp.tool()
async def get_state() -> dict:
    """Get the current robot state. All angles returned in degrees."""
    b = _backend()
    pose = XYZRPYPose.from_pose_array(b.get_present_head_pose())
    antennas = b.get_present_antenna_joint_positions()
    return {
        "head": {
            "x": pose.x,
            "y": pose.y,
            "z": pose.z,
            "roll": math.degrees(pose.roll),
            "pitch": math.degrees(pose.pitch),
            "yaw": math.degrees(pose.yaw),
        },
        "body_yaw": math.degrees(b.get_present_body_yaw()),
        "antennas": {
            "left": math.degrees(antennas[0]),
            "right": math.degrees(antennas[1]),
        },
        "control_mode": b.get_motor_control_mode().value,
    }


# --- Motors ---


@mcp.tool()
async def get_motor_status() -> dict:
    """Get the current motor control mode."""
    return {"mode": _backend().get_motor_control_mode().value}


@mcp.tool()
async def set_motor_mode(mode: str) -> dict:
    """Set motor mode: 'enabled', 'disabled', or 'gravity_compensation'."""
    _backend().set_motor_control_mode(MotorControlMode(mode))
    return {"status": f"motors set to {mode}"}
