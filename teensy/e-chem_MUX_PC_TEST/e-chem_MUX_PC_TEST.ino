/*
  E-Chem MUX

  Cycles through 8 channels on an ADG731 MUX chip
  Uses LED lights to indicate when a chnl is on

  modified on 11 June 2025
  by Sadman Sakib
*/

// hardware serial port for communicating wirh Raspberry Pi (not the USB serial port)
// Teensy::Pin 0 - RX1 and Pin 1 - TX1
#define HWSERIAL Serial1

// include the SPI and Bounce libraries
#include <SPI.h> 

// slave select Pins used in 3-wire SPI communication
// SYNC signals for the ADG731 MUX chips
const int muxSelectPin1 = 6;  // WE MUX #1
const int muxSelectPin2 = 7;  // WE MUX #2
const int muxSelectPin3 = 8;  // RE MUX
const int muxSelectPin4 = 9;  // CE MUX
// SPI settings -> frequency, significant bit polarity and mode
SPISettings spiconfig(1000000, MSBFIRST, SPI_MODE2);

// ADG731 SPI channel select addresses
// MSB:: !EN !CS X A4 A3 A2 A1 A0 :: LSB
const byte chnls[] = {
  0b00000000,  // 1
  0b00000001,  // 2
  0b00000010,  // 3
  0b00000011,  // 4
  0b00000100,  // 5
  0b00000101,  // 6
  0b00000110,  // 7
  0b00000111,  // 8
  0b00001000,  // 9
  0b00001001,  // 10
  0b00001010,  // 11
  0b00001011,  // 12
  0b00001100,  // 13
  0b00001101,  // 14
  0b00001110,  // 15
  0b00001111,  // 16
  0b00010000,  // 17
  0b00010001,  // 18
  0b00010010,  // 19
  0b00010011,  // 20
  0b00010100,  // 21
  0b00010101,  // 22
  0b00010110,  // 23
  0b00010111,  // 24
  0b00011000,  // 25
  0b00011001,  // 26
  0b00011010,  // 27 
  0b00011011,  // 28
  0b00011100,  // 29
  0b00011101,  // 30
  0b00011110,  // 31
  0b00011111,  // 32

  // special cases
  0b10000000,  // All MUX chnls off
  0b01000000   // Retain previous MUX switch conditions
};

// Special MUX states index
const byte MUX_OFF = 32;
const byte KEEP_CHANNEL = 33;

// Serial input commant charcter limit
const int MAX_CMD_LENGTH = 10;  // "16 4" + safety margin

// State tracking (-1 indicates initial off state)
byte currentChip = -1;    // Current active chip (0-15)
byte currentWE = -1;       // Current WE on chip (0-3)

// Function prototypes
void setMuxChannel(byte muxID, byte channel);
void parseSerialCommand();
void processCommand(char* cmd);
void setElectrodes(byte chip, byte we);
void sendAck(byte chipID, byte weID, bool success, const char* errorMsg = "");

void latch(byte muxID) {
  int selectPin;
  switch(muxID) {
    case 1: selectPin = muxSelectPin1; break;
    case 2: selectPin = muxSelectPin2; break;
    case 3: selectPin = muxSelectPin3; break;
    case 4: selectPin = muxSelectPin4; break;
    default: return;
  }
  
  SPI.beginTransaction(spiconfig);
  digitalWrite(selectPin, LOW);
  SPI.transfer(chnls[KEEP_CHANNEL]);
  digitalWrite(selectPin, HIGH);
  SPI.endTransaction();
}

void setMuxChannel(byte muxID, byte channel) {
  int selectPin;
  switch(muxID) {
    case 1: selectPin = muxSelectPin1; break;
    case 2: selectPin = muxSelectPin2; break;
    case 3: selectPin = muxSelectPin3; break;
    case 4: selectPin = muxSelectPin4; break;
    default: return; // Error handling
  }
  
  SPI.beginTransaction(spiconfig);
  digitalWrite(selectPin, LOW);
  SPI.transfer(chnls[channel]);  // Use pre-defined channel commands
  digitalWrite(selectPin, HIGH);
  SPI.endTransaction();
}

void parseSerialCommand() {
  static char buffer[MAX_CMD_LENGTH];
  static int index = 0;

  while (HWSERIAL.available() && index < MAX_CMD_LENGTH-1) {
    char c = HWSERIAL.read();
    
    if (c == '\n') {
      buffer[index] = '\0';  // Null-terminate
      processCommand(buffer);
      index = 0;  // Reset
    } else if (c != '\r') {
      buffer[index++] = c;
    }
  }
  
  // Handle overflow
  if (index >= MAX_CMD_LENGTH-1) {
    sendAck(0, 0, false, "Command too long");
    index = 0;  // Reset buffer
  }
}

void processCommand(char* cmd) {
  int chip, we;
  
  // Parse with format checking
  if (sscanf(cmd, "%d %d", &chip, &we) != 2) {
    sendAck(0, 0, false, "Invalid format");
    return;
  }
  
  // Validate bounds
  if (chip < 1 || chip > 16 || we < 1 || we > 4) {
    sendAck(0, 0, false, "Invalid chip/WE");
    return;
  }
  
  // Execute command
  setElectrodes(chip-1, we-1);
  sendAck(chip-1, we-1, true);
}

void setElectrodes(byte chip, byte we) {
  // Calculate global WE index (0-63)
  int globalWE = (chip * 4) + we;
  
  // Determine which MUX handles this WE
  byte weMux = (globalWE < 32) ? 1 : 2;
  byte weChannel = (globalWE < 32) ? globalWE : globalWE - 32;
  
  // RE/CE always match chip number (0-15)
  byte reChannel = chip;
  byte ceChannel = chip;

  // Set all electrodes
  setMuxChannel(weMux, weChannel);
  setMuxChannel(3, reChannel);
  setMuxChannel(4, ceChannel);
  
  // Latch all MUXes 
  latch(weMux);
  latch(3);
  latch(4);
  
  // Update global state
  currentChip = chip;
  currentWE = we;
}

// the setup function runs once when you press reset or power the board
void setup() {
  // Initialize all MUX select pins
  pinMode(muxSelectPin1, OUTPUT);
  pinMode(muxSelectPin2, OUTPUT);
  pinMode(muxSelectPin3, OUTPUT);
  pinMode(muxSelectPin4, OUTPUT);
  
  // Initialize SPI and Serial
  SPI.begin();
  Serial.begin(9600);
  HWSERIAL.begin(9600);  
  while (!HWSERIAL);  // Wait for serial connection
  
  // Turn off all channels initially
  setMuxChannel(1, MUX_OFF);  // MUX_OFF state
  setMuxChannel(2, MUX_OFF);
  setMuxChannel(3, MUX_OFF);
  setMuxChannel(4, MUX_OFF);
  
  HWSERIAL.println("READY");  // Signal initialization complete
}

// the loop function runs over and over again forever
void loop() {
  parseSerialCommand();  // Handle incoming serial commands
}

void sendAck(byte chipID, byte weID, bool success, const char* errorMsg = "") {
  if (success) {
    // Convert from 0-based to 1-based for human-readable display
    byte displayChip = chipID + 1;
    byte displayWE = weID + 1;
    
    String message = "switched to: chip";
    message += String(displayChip);
    message += " and WE ";
    message += String(displayWE);
    
    // Send to Raspberry Pi
    HWSERIAL.println(message);
    
    // Debug output to USB
    Serial.println(message);
  } else {
    String error = "ERROR: ";
    error += errorMsg;
    
    // Send error to Raspberry Pi
    HWSERIAL.println(error);
    
    // Debug output to USB
    Serial.println(error);
  }
}