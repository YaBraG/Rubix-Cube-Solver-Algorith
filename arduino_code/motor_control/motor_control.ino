// pin connections
const int dirPin1 = 2;
const int stepPin1 = 3;
const int dirPin2 = 4;
const int stepPin2 = 5;
const int dirPin3 = 7;
const int stepPin3 = 6;
const int dirPin4 = 8 ;
const int stepPin4 = 9;
const int dirPin5 = 10;
const int stepPin5 = 11;

const int motorDirPin[5] = {2,4,7,8,10};
const int motorStepPin[5] = {3,5,6,9,11};

// number of steps to make one revolution, change to match your motor
const int stepsPerRevolution = 200;

void setup() {
  for (int pin =2; pin<12; pin++){
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

  
  // set rotation to clockwise
  // digitalWrite(dirPin1, HIGH);
  // // spin motor slowly for one revolution
  // for (int step = 0; step < stepsPerRevolution; step++) {
  //   digitalWrite(stepPin1, HIGH);
  //   delayMicroseconds(5000);
  //   digitalWrite(stepPin1, LOW);
  //   delayMicroseconds(5000);
  // }
  // delay(2000);

  // rotate counter-clockwise
//   digitalWrite(dirPin1, LOW);
//   // spin motor faster for one revolution
//   for (int step = 0; step < stepsPerRevolution; step++) {
//     digitalWrite(stepPin1, HIGH);
//     delayMicroseconds(2000);
//     digitalWrite(stepPin1, LOW);
//     delayMicroseconds(2000);    
//   }
//   delay(2000);
   
   
//    //For motor 2

//   // set rotation to clockwise
//   digitalWrite(dirPin2, HIGH);
//   // spin motor slowly for one revolution
//   for (int step = 0; step < stepsPerRevolution; step++) {
//     digitalWrite(stepPin2, HIGH);
//     delayMicroseconds(5000);
//     digitalWrite(stepPin2, LOW);
//     delayMicroseconds(5000);
//   }
//   delay(2000);

//   // rotate counter-clockwise
//   digitalWrite(dirPin2, LOW);
//   // spin motor faster for one revolution
//   for (int step = 0; step < stepsPerRevolution; step++) {
//     digitalWrite(stepPin2, HIGH);
//     delayMicroseconds(2000);
//     digitalWrite(stepPin2, LOW);
//     delayMicroseconds(2000);    
//   }
//   delay(2000);

//   //For Motor 3

//   // set rotation to clockwise
//   digitalWrite(dirPin3, HIGH);
//   // spin motor slowly for one revolution
//   for (int step = 0; step < stepsPerRevolution; step++) {
//     digitalWrite(stepPin3, HIGH);
//     delayMicroseconds(5000);
//     digitalWrite(stepPin3, LOW);
//     delayMicroseconds(5000);
//   }
//   delay(2000);

//   // rotate counter-clockwise
//   digitalWrite(dirPin3, LOW);
//   // spin motor faster for one revolution
//   for (int step = 0; step < stepsPerRevolution; step++) {
//     digitalWrite(stepPin3, HIGH);
//     delayMicroseconds(2000);
//     digitalWrite(stepPin3, LOW);
//     delayMicroseconds(2000);    
//   }
//   delay(2000);

//   //For Motor 4 
//    // set rotation to clockwise
//   digitalWrite(dirPin4, HIGH);
//   // spin motor slowly for one revolution
//   for (int step = 0; step < stepsPerRevolution; step++) {
//     digitalWrite(stepPin4, HIGH);
//     delayMicroseconds(5000);
//     digitalWrite(stepPin4, LOW);
//     delayMicroseconds(5000);
//   }
//   delay(2000);

//   // rotate counter-clockwise
//   digitalWrite(dirPin4, LOW);
//   // spin motor faster for one revolution
//   for (int step = 0; step < stepsPerRevolution; step++) {
//     digitalWrite(stepPin4, HIGH);
//     delayMicroseconds(2000);
//     digitalWrite(stepPin4, LOW);
//     delayMicroseconds(2000);    
//   }
//   delay(2000);
 
//  //For Motor 5 
//   // set rotation to clockwise
//   digitalWrite(dirPin4, HIGH);
//   // spin motor slowly for one revolution
//   for (int step = 0; step < stepsPerRevolution; step++) {
//     digitalWrite(stepPin5, HIGH);
//     delayMicroseconds(5000);
//     digitalWrite(stepPin5, LOW);
//     delayMicroseconds(5000);
//   }
//   delay(2000);

//   // rotate counter-clockwise
//   digitalWrite(dirPin4, LOW);
//   // spin motor faster for one revolution
//   for (int step = 0; step < stepsPerRevolution; step++) {
//     digitalWrite(stepPin5, HIGH);
//     delayMicroseconds(2000);
//     digitalWrite(stepPin5, LOW);
//     delayMicroseconds(2000);    
//   }
//   delay(2000);
}