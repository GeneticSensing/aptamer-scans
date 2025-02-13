/*
  MUX Channel Switching with Teensy and Raspberry Pi

  This program interfaces with a Teensy microcontroller to control an ADG731 multiplexer (MUX).
  It listens for a signal from a Raspberry Pi to change the MUX channel and acknowledges each change.

  Modified by 12 Feb 2025
  by Sadman Sakib, Adam Mak
*/

#include <SPI.h>

// RPi Communication Pins
#define CH_CHANGE_PIN      18  // Teensy IN: Command to change MUX channel
#define CH_CHANGE_ACK_PIN  19  // Teensy OUT: Acknowledge channel change
#define CYCLE_ACK_PIN      20  // Teensy OUT: Acknowledge full electrode change cycle

// SPI Slave Select Pin
#define SELECT_PIN1        9   // SYNC signal for the ADG731 MUX

// SPI Configuration
#define SPI_FREQUENCY      30000000
#define SPI_BIT_ORDER      MSBFIRST
#define SPI_MODE           SPI_MODE2
SPISettings spiConfig(SPI_FREQUENCY, SPI_BIT_ORDER, SPI_MODE);

// ADG731 SPI Channel Select Addresses (MSB:: !EN !CS X A4 A3 A2 A1 A0 :: LSB)
const byte CHANNELS[] = {
  0b00011111,  // 32
  0b00011110,  // 31
  0b00011101,  // 30
  0b00011100,  // 29
  0b00011011,  // 28
  0b00011010,  // 27
  0b00011001,  // 26
  0b00011000   // 25
};

#define TOTAL_CHANNELS 8
#define MUX_OFF        0b1000000  // All switches off
#define KEEP_CHANNEL   0b01000000 // Retain previous switch condition

volatile bool triggerFunction = false;  // Flag to indicate interrupt occurrence
int channelIndex = 0; // Current channel index

// Interrupt Service Routine (ISR) for channel change signal
void handleInterrupt() {
  triggerFunction = true;
}

// Latch function to retain the previous switch condition
void latch() {
  SPI.beginTransaction(spiConfig);
  digitalWrite(SELECT_PIN1, LOW);
  SPI.transfer(KEEP_CHANNEL);
  digitalWrite(SELECT_PIN1, HIGH);
  SPI.endTransaction();
}

// Switch MUX channel
void switchChannel(int channel) {
  SPI.beginTransaction(spiConfig);
  digitalWrite(SELECT_PIN1, LOW);
  SPI.transfer(CHANNELS[channel]);
  digitalWrite(SELECT_PIN1, HIGH);
  SPI.endTransaction();
}

// Acknowledgment signal that MUX channel has changed
void channelChangeAck() {
  digitalWrite(CH_CHANGE_ACK_PIN, HIGH);
  delay(10);
  digitalWrite(CH_CHANGE_ACK_PIN, LOW);
  Serial.println(channelIndex);
  Serial.println("Channel Changed!");
  delay(1000);
}

// Acknowledgment signal that MUX has cycled through all available channels
void cycleCompleteAck() {
  digitalWrite(CYCLE_ACK_PIN, HIGH);
  delay(10);
  digitalWrite(CYCLE_ACK_PIN, LOW);
  Serial.println("Cycle Complete!");
  delay(1000);
}

void setup() {
  // Initialize Raspberry Pi Communication Pins
  pinMode(CH_CHANGE_PIN, INPUT);
  pinMode(CH_CHANGE_ACK_PIN, OUTPUT);
  pinMode(CYCLE_ACK_PIN, OUTPUT);

  // Initialize SPI Slave Select Pin
  pinMode(SELECT_PIN1, OUTPUT);

  // Attach interrupt for channel change request
  attachInterrupt(digitalPinToInterrupt(CH_CHANGE_PIN), handleInterrupt, RISING);

  // Initialize SPI and Serial Communication
  SPI.begin();
  Serial.begin(38400);

  // Initialize MUX to the first channel
  switchChannel(0);

  latch();
}

void loop() {
  // Check if an interrupt has occurred
  if (triggerFunction) {
    triggerFunction = false;  // Reset the flag
    Serial.println("Teensy: Sending instruction to MUX");

    // Cycle through channels
    channelIndex = (channelIndex + 1) % TOTAL_CHANNELS;

    // Send new channel selection to MUX
    switchChannel(channelIndex);

    if (channelIndex == TOTAL_CHANNELS - 1) {
      Serial.println("Teensy: Full cycle completed. Sending signal to RPi to finish last measurement.");
      cycleCompleteAck();
    } else {
      Serial.println("Teensy: Completed. Sending signal to RPi to start next measurement.");
      channelChangeAck();
    }
    latch();
  }
}
