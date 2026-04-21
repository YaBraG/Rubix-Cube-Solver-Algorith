const int MOTOR_COUNT = 6;
const int motorDirPin[MOTOR_COUNT] = {2, 4, 7, 8, 10, 12};
const int motorStepPin[MOTOR_COUNT] = {3, 5, 6, 9, 11, 13};

// Tune this if your driver or motor uses a different step count.
const int STEPS_PER_REV = 200;
// Tune this after hardware testing if 90 degrees needs more or fewer steps.
const int STEPS_PER_90 = STEPS_PER_REV / 4;
// Tune this delay to make the motor faster or more reliable.
const int STEP_DELAY_US = 2000;

bool stopRequested = false;

bool isValidMotor(int motorIndex) {
  return motorIndex >= 0 && motorIndex < MOTOR_COUNT;
}

bool isValidAngle(int angle) {
  return angle == -180 || angle == -90 || angle == 90 || angle == 180;
}

int computeSteps(int angle) {
  return (abs(angle) / 90) * STEPS_PER_90;
}

bool pollStopCommand() {
  if (!Serial.available()) {
    return false;
  }

  String command = Serial.readStringUntil('\n');
  command.trim();
  command.toUpperCase();
  if (command == "STOP") {
    stopRequested = true;
    return true;
  }

  Serial.println("ERR busy");
  return false;
}

void moveMotor(int motorIndex, int angle) {
  const int steps = computeSteps(angle);
  const int directionPinValue = angle > 0 ? HIGH : LOW;

  stopRequested = false;
  digitalWrite(motorDirPin[motorIndex], directionPinValue);
  Serial.print("OK MOVING ");
  Serial.print(motorIndex);
  Serial.print(" ");
  Serial.print(angle);
  Serial.print(" ");
  Serial.println(steps);

  for (int step = 0; step < steps; step++) {
    if (pollStopCommand()) {
      break;
    }
    digitalWrite(motorStepPin[motorIndex], HIGH);
    delayMicroseconds(STEP_DELAY_US);
    digitalWrite(motorStepPin[motorIndex], LOW);
    delayMicroseconds(STEP_DELAY_US);
  }

  Serial.println("OK DONE");
}

void handleCommand(String command) {
  command.trim();
  if (command.length() == 0) {
    return;
  }

  command.toUpperCase();

  if (command == "PING") {
    Serial.println("OK PONG");
    return;
  }

  if (command == "STOP") {
    stopRequested = true;
    Serial.println("OK DONE");
    return;
  }

  if (!command.startsWith("MOVE ")) {
    Serial.println("ERR unknown command");
    return;
  }

  int motorIndex = -1;
  int angle = 0;
  if (sscanf(command.c_str(), "MOVE %d %d", &motorIndex, &angle) != 2) {
    Serial.println("ERR bad move format");
    return;
  }

  if (!isValidMotor(motorIndex)) {
    Serial.println("ERR invalid motor index");
    return;
  }

  if (!isValidAngle(angle)) {
    Serial.println("ERR invalid angle");
    return;
  }

  moveMotor(motorIndex, angle);
}

void setup() {
  for (int index = 0; index < MOTOR_COUNT; index++) {
    pinMode(motorDirPin[index], OUTPUT);
    pinMode(motorStepPin[index], OUTPUT);
    digitalWrite(motorStepPin[index], LOW);
  }
  Serial.begin(115200);
}

void loop() {
  if (!Serial.available()) {
    return;
  }

  String command = Serial.readStringUntil('\n');
  handleCommand(command);
}
