#define INPUT_PIN 18   // Pin 18 to receive signal from Raspberry Pi
#define OUTPUT_PIN 19  // Pin 19 to send signal to Raspberry Pi

volatile bool triggerFunction = false;  // Flag to indicate interrupt occurred

// Interrupt service routine (ISR) for when signal is received
void handleInterrupt() {
  triggerFunction = true;
}

void muxSwitch() {
  Serial.println("Teensy: Sending instruction to MUX");
  delay(2000);  // Simulate MUX switch
  Serial.println("Teensy: Completed. Sending signal to RPi to start next measurement.");
  
  // Send acknowledgment signal
  digitalWrite(OUTPUT_PIN, HIGH);
  delay(100);  // Send a short pulse
  digitalWrite(OUTPUT_PIN, LOW);
}

void setup() {
  Serial.begin(9600);
  pinMode(INPUT_PIN, INPUT);
  pinMode(OUTPUT_PIN, OUTPUT);
  attachInterrupt(digitalPinToInterrupt(INPUT_PIN), handleInterrupt, RISING);
  Serial.println("Teensy: Waiting for signal from Raspberry Pi...");
}

void loop() {
  if (triggerFunction) {
    triggerFunction = false;  // Reset the flag
    muxSwitch();
    Serial.println("Teensy: Waiting for signal from Raspberry Pi...");
  }
  // Send acknowledgment signal
  digitalWrite(OUTPUT_PIN, HIGH);
  delay(100);  // Send a short pulse
  digitalWrite(OUTPUT_PIN, LOW);
  delay(1000);
}
