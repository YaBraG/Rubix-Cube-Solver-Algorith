const int MOTOR_COUNT = 6;
const int motorDirPin[MOTOR_COUNT] = {2, 4, 7, 8, 10, 12};
const int motorStepPin[MOTOR_COUNT] = {3, 5, 6, 9, 11, 13};

// Motor wiring reference for this stepper:
// BLK = A+, BLU = A-, GRN = B+, RED = B-
//
// Hardware warnings:
// - This motor is rated around 1.5A per phase.
// - A4988 current limit must be set physically on the driver.
// - Use cooling or heatsinks if the driver runs hot.
// - RESET and SLEEP must be held high if they are not controlled elsewhere.
// - Arduino, driver, and power supply must share a common ground.
//
// A4988 microstep options:
// 1 = full step, 2 = half step, 4 = quarter step,
// 8 = eighth step, 16 = sixteenth step.
const int MOTOR_FULL_STEPS_PER_REV = 400;  // 0.90 degree motor
const int MICROSTEPS = 1;                  // Edit to match A4988 jumper setting
const int STEPS_PER_REV = MOTOR_FULL_STEPS_PER_REV * MICROSTEPS;
// Tune this live with SET_STEPS90 if 90 degrees needs more or fewer steps.
int currentStepsPer90 = STEPS_PER_REV / 4;
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
  return (abs(angle) / 90) * currentStepsPer90;
}

void printConfig() {
  Serial.print("OK CONFIG ");
  Serial.print("MOTOR_FULL_STEPS_PER_REV=");
  Serial.print(MOTOR_FULL_STEPS_PER_REV);
  Serial.print(" MICROSTEPS=");
  Serial.print(MICROSTEPS);
  Serial.print(" STEPS_PER_REV=");
  Serial.print(STEPS_PER_REV);
  Serial.print(" STEPS_PER_90=");
  Serial.print(currentStepsPer90);
  Serial.print(" STEP_DELAY_US=");
  Serial.println(STEP_DELAY_US);
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

  if (command == "CONFIG?") {
    printConfig();
    return;
  }

  if (command == "STOP") {
    stopRequested = true;
    Serial.println("OK DONE");
    return;
  }

  if (command.startsWith("SET_STEPS90 ")) {
    int stepsPer90 = 0;
    if (sscanf(command.c_str(), "SET_STEPS90 %d", &stepsPer90) != 1) {
      Serial.println("ERR bad SET_STEPS90 format");
      return;
    }
    if (stepsPer90 <= 0) {
      Serial.println("ERR invalid STEPS_PER_90");
      return;
    }
    currentStepsPer90 = stepsPer90;
    Serial.print("OK STEPS_PER_90 ");
    Serial.println(currentStepsPer90);
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
