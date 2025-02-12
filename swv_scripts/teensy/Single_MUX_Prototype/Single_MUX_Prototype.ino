/*
  Blink

  Turns an LED on for one second, then off for one second, repeatedly.

  Most Arduinos have an on-board LED you can control. On the UNO, MEGA and ZERO
  it is attached to digital pin 13, on MKR1000 on pin 6. LED_BUILTIN is set to
  the correct LED pin independent of which board is used.
  If you want to know what pin the on-board LED is connected to on your Arduino
  model, check the Technical Specs of your board at:
  https://www.arduino.cc/en/Main/Products

  modified by 12 Feb 2025
  by Sadman Sakib, Adam Mak
*/

// include the SPI and Bounce libraries
#include <SPI.h> 
#include <Bounce.h>

// Raspberry Pi Communication Pins
// Teensy IN::used to command teensy to change MUX channel
const int chChangePin = 18; 
// Teensy OUT:: used to acknowledge channel change
const int chChangeAckPin = 19; 
// Teensy OUT:: used to achnowledge finishing of full electrode change cycle
const int cycleAckPin = 20; 

// slave select Pins used in 3-wire SPI communication
// SYNC signals for the ADG731 MUX chips
const int selectPin1 = 9;
// SPI settings -> frequency, significant bit polarity and mode
SPISettings spiconfig(30000000, MSBFIRST, SPI_MODE2);

// ADG731 SPI channel select addresses
// MSB:: !EN !CS X A4 A3 A2 A1 A0 :: LSB
const byte chnls[] = {
  0b00011111,  // 32
  0b00011110,  // 31
  0b00011101,  // 30
  0b00011100,  // 29
  0b00011011,  // 28
  0b00011010,  // 27 
  0b00011001,  // 26
  0b00011000   // 25
};
// All switches off
const byte muxChipOff = 0b1000000;
// Retain previous switch condition
const byte keepChnl = 0b01000000;

int chnlIndex = 0;
const int totalChnls = 8;

volatile bool triggerFunction = false;  // Flag to indicate interrupt occurred

// ISR for when signal is received
void handleInterrupt() {
  triggerFunction = true;
}

// the setup function runs once when you press reset or power the board
void setup() {

  // Raspberry Pi Communication Pins
  pinMode(chChangePin, INPUT);
  pinMode(chChangeAckPin, OUTPUT);
  pinMode(cycleAckPin, OUTPUT);

  // set slave select pins as outputs
  pinMode(selectPin1, OUTPUT);

  // initiate MUX channel switch when receiving pulse from RPi
  attachInterrupt(digitalPinToInterrupt(chChangePin), handleInterrupt, RISING);

  // initialize SPI and Serial communication
  SPI.begin();
  Serial.begin(38400);

}

// the loop function runs over and over again forever
void loop() {

  SPI.beginTransaction(spiconfig);
  digitalWrite(selectPin1, LOW);
  SPI.transfer(keepChnl);
  digitalWrite(selectPin1, HIGH);
  SPI.endTransaction();

  // check to see if the pushbutton has been pressed
  // commands Teensy to change MUX channel
  if (triggerFunction) {
    triggerFunction = false;  // reset the flag
    Serial.println("Teensy: Sending instruction to MUX");

    chnlIndex = (chnlIndex + 1) % totalChnls;  // Cycle through channels

    SPI.beginTransaction(spiconfig);
    digitalWrite(selectPin1, LOW);
    SPI.transfer(chnls[chnlIndex]);  // send new chnl selection
    digitalWrite(selectPin1, HIGH);
    SPI.endTransaction();

    if (chnlIndex == totalChnls - 1){
      Serial.println("Teensy: Fulll cycle completed. Sending signal to RPi to finish.");
      cycleCompleteAck();
    } else {
      Serial.println("Teensy: Completed. Sending signal to RPi to start next measurement.");
      chnlChangeAck();
    }
  }
}

void chnlChangeAck() {
  // Acknowledgement signal that MUX channel has been changed
  // A 10s 3.3 V pulse -> RPi to detect rising edge
  digitalWrite(chChangeAckPin, HIGH);
  delay(10);
  digitalWrite(chChangeAckPin, LOW);
  Serial.println(chnlIndex);
  Serial.println("Channel Changed!");
  delay(1000);
}

void cycleCompleteAck() {
  // Acknowledgement signal that MUX has cycled through all available chnls
  // A 10s 3.3 V pulse -> RPi to detect rising edge
  digitalWrite(cycleAckPin, HIGH);
  delay(10);
  digitalWrite(cycleAckPin, LOW);
  Serial.println("Cycle Complete!");
  delay(1000);
}
