const int motorDirPin[6] = {2,4,7,8,10,12};
const int motorStepPin[6] = {3,5,6,9,11,13};

// number of steps to make one revolution, change to match your motor
const int stepsPerRevolution = 200;

void setup() {
  for (int pin = 2; pin<13; pin++){
    pinMode(pin,OUTPUT);
  }
}

void motorMove(int motorNumber,int direction,int stepsPerRevolution,int delay){
  // set rotation to clockwise
  digitalWrite(motorDirPin[motorNumber], direction);
  // spin motor slowly for one revolution
  for (int step = 0; step < stepsPerRevolution; step++) {
    digitalWrite(motorStepPin[motorNumber], HIGH);
    delayMicroseconds(delay);
    digitalWrite(motorStepPin[motorNumber], LOW);
    delayMicroseconds(delay);
  }
  delayMicroseconds(1000);
}

void loop() {
  int delay = 2000;
  //Motors go from 0 to 4

  //For motor 1
  //Clockwise
  motorMove(0,HIGH,stepsPerRevolution,delay);
  //Counter-Clockwise
  motorMove(0,LOW,stepsPerRevolution,delay);

  //For motor 2
  //Clockwise
  motorMove(1,HIGH,stepsPerRevolution,delay);
  //Counter-Clockwise
  motorMove(1,LOW,stepsPerRevolution,delay);

  //For motor 3
  //Clockwise
  motorMove(2,HIGH,stepsPerRevolution,delay);
  //Counter-Clockwise
  motorMove(2,LOW,stepsPerRevolution,delay);

  //For motor 4
  //Clockwise
  motorMove(3,HIGH,stepsPerRevolution,delay);
  //Counter-Clockwise
  motorMove(3,LOW,stepsPerRevolution,delay);

  //For motor 5
  //Clockwise
  motorMove(4,HIGH,stepsPerRevolution,delay);
  //Counter-Clockwise
  motorMove(4,LOW,stepsPerRevolution,delay);
  
  //For motor 6
  //Clockwise
  motorMove(6,HIGH,stepsPerRevolution,delay);
  //Counter-Clockwise
  motorMove(6,LOW,stepsPerRevolution,delay);
}