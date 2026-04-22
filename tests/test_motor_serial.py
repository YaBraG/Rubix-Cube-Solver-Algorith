from types import SimpleNamespace

import pytest

from rubiks_solver.motor_serial import (
    DEFAULT_COLOR_TO_MOTOR_MAP,
    MotorSerialError,
    drain_startup_lines,
    format_config_command,
    format_move_command,
    format_set_step_delay_command,
    list_serial_ports,
    ping_arduino,
    request_arduino_config,
    resolve_color_motor,
    send_color_angle_commands,
    send_move,
    set_step_delay,
    validate_angle,
    validate_step_delay,
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


class FakeSerialTimeoutThenPong(FakeSerial):
    def __init__(self):
        super().__init__(["OK READY", "", "OK PONG"])


def test_command_formatting():
    assert format_move_command(0, 90) == "MOVE 0 90"
    assert format_move_command(5, -180) == "MOVE 5 -180"
    assert format_config_command() == "CONFIG?"
    assert format_set_step_delay_command(2000) == "SET_STEP_DELAY 2000"


def test_angle_validation():
    assert validate_angle(90) == 90
    with pytest.raises(MotorSerialError):
        validate_angle(45)


def test_step_delay_validation():
    assert validate_step_delay(2000) == 2000
    with pytest.raises(MotorSerialError):
        validate_step_delay(50)


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


def test_send_color_angle_commands_waits_between_moves(monkeypatch):
    fake = FakeSerial(
        [
            "OK MOVING 0 90 50",
            "OK DONE",
            "OK MOVING 1 -90 50",
            "OK DONE",
        ]
    )
    delays = []
    monkeypatch.setattr("rubiks_solver.motor_serial.time.sleep", lambda seconds: delays.append(seconds))

    send_color_angle_commands(fake, [("white", 90), ("red", -90)], delay_between_commands_ms=250)

    assert delays == [0.25]


def test_request_config_reads_ok_config_response():
    fake = FakeSerial(
        [
            "OK CONFIG MOTOR_FULL_STEPS_PER_REV=400 MICROSTEPS=1 STEPS_PER_REV=400 STEPS_PER_90=100 STEP_DELAY_US=2000",
        ]
    )

    response = request_arduino_config(fake)

    assert response.startswith("OK CONFIG")
    assert fake.writes == ["CONFIG?\n"]


def test_set_step_delay_reads_ok_response():
    fake = FakeSerial(["OK STEP_DELAY_US 1800"])

    response = set_step_delay(fake, 1800)

    assert response == "OK STEP_DELAY_US 1800"
    assert fake.writes == ["SET_STEP_DELAY 1800\n"]


def test_ping_handles_ok_ready_then_ok_pong():
    fake = FakeSerial(["OK READY", "OK PONG"])

    response = ping_arduino(fake)

    assert response == "OK PONG"
    assert fake.writes == ["PING\n"]


def test_ping_retries_after_timeout_then_succeeds():
    fake = FakeSerialTimeoutThenPong()

    response = ping_arduino(fake)

    assert response == "OK PONG"
    assert fake.writes == ["PING\n", "PING\n"]


def test_timeout_error_includes_serial_monitor_warning():
    fake = FakeSerial(["", "", ""])

    with pytest.raises(MotorSerialError) as exc:
        ping_arduino(fake)

    assert "close Arduino Serial Monitor" in str(exc.value)


def test_drain_startup_lines_collects_ready_message():
    fake = FakeSerial(["OK READY", "OK CONFIG TEST", ""])

    lines = drain_startup_lines(fake)

    assert lines == ["OK READY", "OK CONFIG TEST"]


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
