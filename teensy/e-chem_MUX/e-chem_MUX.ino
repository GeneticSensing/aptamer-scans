/*
  E-Chem MUX

  Controls four 32-channel multiplexers for electrochemical measurements
  Communicates with Raspberry Pi via hardware serial (Serial1)

  modified on 11 June 2025
  by Sadman Sakib
*/

#include <SPI.h> 

// Multiplexer control pins
const int muxSelectPin1 = 6;  // WE MUX #1 (Channels 0-31)
const int muxSelectPin2 = 7;  // WE MUX #2 (Channels 32-63)
const int muxSelectPin3 = 8;  // RE MUX (16 channels)
const int muxSelectPin4 = 9;  // CE MUX (16 channels)

// SPI configuration
SPISettings spiconfig(1000000, MSBFIRST, SPI_MODE2);

// Channel configuration for ADG731 (32 channels + 2 special states)
const byte chnls[] = {
  0b00000000, 0b00000001, 0b00000010, 0b00000011,  // 1-4
  0b00000100, 0b00000101, 0b00000110, 0b00000111,  // 5-8
  0b00001000, 0b00001001, 0b00001010, 0b00001011,  // 9-12
  0b00001100, 0b00001101, 0b00001110, 0b00001111,  // 13-16
  0b00010000, 0b00010001, 0b00010010, 0b00010011,  // 17-20
  0b00010100, 0b00010101, 0b00010110, 0b00010111,  // 21-24
  0b00011000, 0b00011001, 0b00011010, 0b00011011,  // 25-28
  0b00011100, 0b00011101, 0b00011110, 0b00011111,  // 29-32
  0b10000000,  // MUX_OFF (index 32)
  0b01000000   // KEEP_CHANNEL (index 33)
};

// Special state indices
const byte MUX_OFF = 32;
const byte KEEP_CHANNEL = 33;

// Serial configuration
const int MAX_CMD_LENGTH = 10;  // Max command length

// System state
byte currentChip = -1;    // Current chip (0-15)
byte currentWE = -1;      // Current working electrode (0-3)

// Function prototypes
void setMuxChannel(byte muxID, byte channel);
void parseSerialCommand();
void processCommand(char* cmd);
void setElectrodes(byte chip, byte we);
void sendAck(byte chipID, byte weID, bool success, const char* errorMsg = "");
void latch(byte muxID);


// --------------------------
// Hardware Control Functions
// --------------------------

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
    default: return;
  }
  
  SPI.beginTransaction(spiconfig);
  digitalWrite(selectPin, LOW);
  SPI.transfer(chnls[channel]);
  digitalWrite(selectPin, HIGH);
  SPI.endTransaction();
}

// --------------------------
// Serial Communication
// --------------------------

void parseSerialCommand() {
  static char buffer[MAX_CMD_LENGTH];
  static int index = 0;

  while (Serial.available() && index < MAX_CMD_LENGTH-1) {  // Changed to Serial
    char c = Serial.read();  // Read from USB
    
    if (c == '\n') {
      buffer[index] = '\0';
      processCommand(buffer);
      index = 0;
    } 
    else if (c != '\r') {
      buffer[index++] = c;
    }
  }
  
  if (index >= MAX_CMD_LENGTH-1) {
    sendAck(0, 0, false, "Command too long");
    index = 0;
  }
}

void processCommand(char* cmd) {
  int chip, we;
  
  if (sscanf(cmd, "%d %d", &chip, &we) != 2) {
    sendAck(0, 0, false, "Invalid format");
    return;
  }
  
  if (chip < 1 || chip > 16 || we < 1 || we > 4) {
    sendAck(0, 0, false, "Invalid chip/WE");
    return;
  }
  
  setElectrodes(chip-1, we-1);
  sendAck(chip-1, we-1, true);
}

// --------------------------
// Core Functions
// --------------------------

void setElectrodes(byte chip, byte we) {
  // Calculate global WE index
  int globalWE = (chip * 4) + we;
  
  // Determine MUX and channel
  byte weMux = (globalWE < 32) ? 1 : 2;
  byte weChannel = (globalWE < 32) ? globalWE : globalWE - 32;
  
  // RE/CE use same channel as chip index
  setMuxChannel(weMux, weChannel);
  setMuxChannel(3, chip);  // RE
  setMuxChannel(4, chip);  // CE
  
  // Apply latching
  latch(weMux);
  latch(3);
  latch(4);
  
  // Update state
  currentChip = chip;
  currentWE = we;
}

void setup() {
  // Initialize LED for status
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);  // Power-on indicator

  // Initialize MUX control pins
  pinMode(muxSelectPin1, OUTPUT);
  pinMode(muxSelectPin2, OUTPUT);
  pinMode(muxSelectPin3, OUTPUT);
  pinMode(muxSelectPin4, OUTPUT);
  
  // Initialize SPI
  SPI.begin();
  
  // Initialize USB Serial ONLY
  Serial.begin(115200);
  while (!Serial);  // Wait for USB connection (remove if not using Arduino IDE)
  
  // Initialize all MUXes to OFF state
  setMuxChannel(1, MUX_OFF);
  setMuxChannel(2, MUX_OFF);
  setMuxChannel(3, MUX_OFF);
  setMuxChannel(4, MUX_OFF);
  
  Serial.println("READY");  // USB initialization complete
  digitalWrite(LED_BUILTIN, LOW);
}

void loop() {
  parseSerialCommand();  // Handle incoming USB commands
  delay(10);            // Prevent CPU overuse
}

void sendAck(byte chipID, byte weID, bool success, const char* errorMsg = "") {
  if (success) {
    String message = "switched to: chip";
    message += String(chipID + 1);
    message += " and WE ";
    message += String(weID + 1);
    
    Serial.println(message);  // Send via USB
  } 
  else {
    String error = "ERROR: ";
    error += errorMsg;
    Serial.println(error);  // Send via USB
  }
}