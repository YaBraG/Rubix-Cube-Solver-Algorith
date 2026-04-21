"""Serial helpers for sending motor commands to the Arduino controller."""

from __future__ import annotations

import argparse
import time
from typing import Any


BAUD_RATE = 115200
SERIAL_TIMEOUT = 2.0
VALID_MOTOR_INDEXES = tuple(range(6))
VALID_ANGLES = (-180, -90, 90, 180)
DEFAULT_COLOR_TO_MOTOR_MAP = {
    "white": 0,
    "red": 1,
    "green": 2,
    "yellow": 3,
    "orange": 4,
    "blue": 5,
}


class MotorSerialError(RuntimeError):
    """Raised when serial motor communication fails."""


def _load_serial_module() -> Any:
    try:
        import serial  # type: ignore
        import serial.tools.list_ports  # type: ignore
    except ImportError as exc:  # pragma: no cover - depends on local env
        raise MotorSerialError("pyserial is required for motor serial control.") from exc
    return serial


def validate_motor_index(motor_index: int) -> int:
    if motor_index not in VALID_MOTOR_INDEXES:
        raise MotorSerialError(f"Invalid motor index: {motor_index}. Use 0 through 5.")
    return motor_index


def validate_angle(angle: int) -> int:
    if angle not in VALID_ANGLES:
        raise MotorSerialError(f"Invalid angle: {angle}. Use -180, -90, 90, or 180.")
    return angle


def format_ping_command() -> str:
    return "PING"


def format_config_command() -> str:
    return "CONFIG?"


def format_move_command(motor_index: int, angle: int) -> str:
    validate_motor_index(motor_index)
    validate_angle(angle)
    return f"MOVE {motor_index} {angle}"


def list_serial_ports() -> list[str]:
    serial = _load_serial_module()
    return [port.device for port in serial.tools.list_ports.comports()]


def open_serial_connection(port: str, *, timeout: float = SERIAL_TIMEOUT) -> Any:
    serial = _load_serial_module()
    try:
        connection = serial.Serial(port=port, baudrate=BAUD_RATE, timeout=timeout, write_timeout=timeout)
    except Exception as exc:
        raise MotorSerialError(f"Could not open serial port {port}.") from exc
    time.sleep(1.5)
    if hasattr(connection, "reset_input_buffer"):
        connection.reset_input_buffer()
    return connection


def _write_command(connection: Any, command: str) -> None:
    connection.write((command.strip() + "\n").encode("utf-8"))
    if hasattr(connection, "flush"):
        connection.flush()


def _read_response(connection: Any) -> str:
    raw = connection.readline()
    if isinstance(raw, bytes):
        text = raw.decode("utf-8", errors="replace").strip()
    else:
        text = str(raw).strip()
    if not text:
        raise MotorSerialError("Timed out waiting for Arduino response.")
    return text


def _expect_ok(response: str) -> str:
    if response.startswith("ERR"):
        raise MotorSerialError(response)
    if not response.startswith("OK"):
        raise MotorSerialError(f"Unexpected Arduino response: {response}")
    return response


def ping_arduino(connection: Any) -> str:
    _write_command(connection, format_ping_command())
    response = _expect_ok(_read_response(connection))
    if response != "OK PONG":
        raise MotorSerialError(f"Unexpected ping response: {response}")
    return response


def request_arduino_config(connection: Any) -> str:
    _write_command(connection, format_config_command())
    response = _expect_ok(_read_response(connection))
    if not response.startswith("OK CONFIG"):
        raise MotorSerialError(f"Unexpected config response: {response}")
    return response


def send_move(connection: Any, motor_index: int, angle: int) -> list[str]:
    command = format_move_command(motor_index, angle)
    _write_command(connection, command)
    moving = _expect_ok(_read_response(connection))
    done = _expect_ok(_read_response(connection))
    if not moving.startswith("OK MOVING"):
        raise MotorSerialError(f"Unexpected move response: {moving}")
    if done != "OK DONE":
        raise MotorSerialError(f"Unexpected move completion response: {done}")
    return [moving, done]


def resolve_color_motor(color: str, color_to_motor_map: dict[str, int] | None = None) -> int:
    mapping = color_to_motor_map or DEFAULT_COLOR_TO_MOTOR_MAP
    normalized = color.lower()
    if normalized not in mapping:
        raise MotorSerialError(f"Unmapped color command: {color}.")
    return validate_motor_index(mapping[normalized])


def send_color_angle_commands(
    connection: Any,
    commands: list[tuple[str, int]],
    *,
    color_to_motor_map: dict[str, int] | None = None,
) -> list[list[str]]:
    responses: list[list[str]] = []
    for color, angle in commands:
        motor_index = resolve_color_motor(color, color_to_motor_map)
        responses.append(send_move(connection, motor_index, angle))
    return responses


def ping_arduino_port(port: str, *, timeout: float = SERIAL_TIMEOUT) -> str:
    connection = open_serial_connection(port, timeout=timeout)
    try:
        return ping_arduino(connection)
    finally:
        connection.close()


def request_config_on_port(port: str, *, timeout: float = SERIAL_TIMEOUT) -> str:
    connection = open_serial_connection(port, timeout=timeout)
    try:
        return request_arduino_config(connection)
    finally:
        connection.close()


def move_motor_on_port(port: str, motor_index: int, angle: int, *, timeout: float = SERIAL_TIMEOUT) -> list[str]:
    connection = open_serial_connection(port, timeout=timeout)
    try:
        return send_move(connection, motor_index, angle)
    finally:
        connection.close()


def send_commands_on_port(
    port: str,
    commands: list[tuple[str, int]],
    *,
    timeout: float = SERIAL_TIMEOUT,
    color_to_motor_map: dict[str, int] | None = None,
) -> list[list[str]]:
    connection = open_serial_connection(port, timeout=timeout)
    try:
        return send_color_angle_commands(connection, commands, color_to_motor_map=color_to_motor_map)
    finally:
        connection.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rubiks-motor-serial",
        description="List serial ports and send simple motor commands to the Arduino motor controller.",
    )
    parser.add_argument("--list", action="store_true", help="List available serial ports.")
    parser.add_argument("--port", help="Serial port such as COM3.")
    parser.add_argument("--ping", action="store_true", help="Ping the Arduino on the selected port.")
    parser.add_argument("--config", action="store_true", help="Read Arduino motor configuration.")
    parser.add_argument(
        "--move",
        nargs=2,
        metavar=("MOTOR", "ANGLE"),
        help="Send one move command like --move 0 90.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.list:
            for port in list_serial_ports():
                print(port)
            return 0

        if args.ping:
            if not args.port:
                parser.error("--ping requires --port.")
            print(ping_arduino_port(args.port))
            return 0

        if args.config:
            if not args.port:
                parser.error("--config requires --port.")
            print(request_config_on_port(args.port))
            return 0

        if args.move:
            if not args.port:
                parser.error("--move requires --port.")
            motor_index = int(args.move[0])
            angle = int(args.move[1])
            for line in move_motor_on_port(args.port, motor_index, angle):
                print(line)
            return 0

        parser.print_help()
        return 1
    except MotorSerialError as exc:
        print(f"Error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
