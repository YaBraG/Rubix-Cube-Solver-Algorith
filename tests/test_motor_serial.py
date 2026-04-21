from types import SimpleNamespace

import pytest

from rubiks_solver.motor_serial import (
    DEFAULT_COLOR_TO_MOTOR_MAP,
    MotorSerialError,
    format_config_command,
    format_move_command,
    list_serial_ports,
    request_arduino_config,
    resolve_color_motor,
    send_color_angle_commands,
    send_move,
    validate_angle,
)


class FakeSerial:
    def __init__(self, responses):
        self.responses = [response.encode("utf-8") for response in responses]
        self.writes = []

    def write(self, data):
        self.writes.append(data.decode("utf-8"))

    def flush(self):
        return None

    def readline(self):
        if self.responses:
            return self.responses.pop(0)
        return b""


def test_command_formatting():
    assert format_move_command(0, 90) == "MOVE 0 90"
    assert format_move_command(5, -180) == "MOVE 5 -180"
    assert format_config_command() == "CONFIG?"


def test_angle_validation():
    assert validate_angle(90) == 90
    with pytest.raises(MotorSerialError):
        validate_angle(45)


def test_color_to_motor_mapping():
    assert resolve_color_motor("white") == 0
    assert resolve_color_motor("blue") == 5
    assert DEFAULT_COLOR_TO_MOTOR_MAP["green"] == 2


def test_unmapped_color_error():
    with pytest.raises(MotorSerialError):
        resolve_color_motor("purple")


def test_fake_serial_send_sequence():
    fake = FakeSerial(["OK MOVING 0 90 50", "OK DONE"])

    responses = send_move(fake, 0, 90)

    assert responses == ["OK MOVING 0 90 50", "OK DONE"]
    assert fake.writes == ["MOVE 0 90\n"]


def test_send_color_angle_command_list_uses_mapping():
    fake = FakeSerial(
        [
            "OK MOVING 0 90 50",
            "OK DONE",
            "OK MOVING 1 -90 50",
            "OK DONE",
        ]
    )

    responses = send_color_angle_commands(fake, [("white", 90), ("red", -90)])

    assert len(responses) == 2
    assert fake.writes == ["MOVE 0 90\n", "MOVE 1 -90\n"]


def test_request_config_reads_ok_config_response():
    fake = FakeSerial(
        [
            "OK CONFIG MOTOR_FULL_STEPS_PER_REV=400 MICROSTEPS=1 STEPS_PER_REV=400 STEPS_PER_90=100 STEP_DELAY_US=2000",
        ]
    )

    response = request_arduino_config(fake)

    assert response.startswith("OK CONFIG")
    assert fake.writes == ["CONFIG?\n"]


def test_list_ports_uses_serial_tools(monkeypatch):
    fake_serial_module = SimpleNamespace(
        tools=SimpleNamespace(
            list_ports=SimpleNamespace(
                comports=lambda: [SimpleNamespace(device="COM3"), SimpleNamespace(device="COM7")]
            )
        )
    )
    monkeypatch.setattr("rubiks_solver.motor_serial._load_serial_module", lambda: fake_serial_module)

    ports = list_serial_ports()

    assert ports == ["COM3", "COM7"]
