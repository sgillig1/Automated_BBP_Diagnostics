#include <MemoryFree.h>
#include <pgmStrToRAM.h>

bool debug = false; // Change the display between readout and excel
bool rectDisk = false; // This is for the rectangular disks and not the circular
bool almostCircle = false; // Case for almost circle, keep rect on for this
int numWells = 4; // This is to determine which well is which
bool dispGraphs = false;
bool overWellIR = true; // Only collect IR temp when over a well

// Setup multiple LEDs
bool onlyFAM = false;  // Start with blue
bool steadyState = false; // this is for the testing of end point
int steadyStateButton = 15; // Button that will turn on steady state only 65

// LED Status
/*
0. LED off
1. FAM
2. TEX
*/
int LEDStatus = 0;
const int TOGGLE_INTERVAL = 2; // 2 iterations per LED
int loopCounter = 0;

// ERRORS
// Variable holding all error flags (up to 16 if using uint16_t)
// When you print - 0 = no errors, 1 = heating, 10 (2) = motor, 11 (3) = both
uint16_t ErrorStatus = 0;
// Define the two error types
#define ERROR_HEATING_DROP   (1 << 0)  // Bit 0
#define ERROR_NO_ROTATION    (1 << 1)  // Bit 1 
const unsigned long ERROR_DELAY = 60000;  ///< Time (ms) before confirming an error
const float HEATING_THRESHOLD = 35.0;     ///< Temperature threshold (°C)
unsigned long heatingBelowStart = 0;      ///< Timer for heating dropout
bool heatingEverAbove = false;            ///< Tracks if heating ever crossed threshold
unsigned long motorStillStart = 0;        ///< Timer for motor stall
float lastMotorPos = 0;                   ///< Last recorded motor position

// Setup for the DHT Temp and Humidity Sensor
#include <DHT.h>;
#define DHTPIN 3     // what pin we're connected to
#define DHTTYPE DHT22   // DHT 22  (AM2302)
DHT dht(DHTPIN, DHTTYPE); //// Initialize DHT sensor for normal 16mhz Arduino
int chk;
float humDHT;  //Stores DHT humidity value
float tempDHT; //Stores DHT temperature value
double collectTimeDHT = 0;

// Setup for MLX temp sensor
#include <Wire.h>
#include "SparkFun_MLX90632_Arduino_Library.h"
MLX90632 MLXSensor;
float MLXObjectTemp; // MLX IR sensor object temp
float MLXSensorTemp; // MLX IR sensor thermistor temp
float MLXObjectTempTEMP; // MLX IR sensor object temp
float MLXSensorTempTEMP; // MLX IR sensor thermistor temp

// Global or static variable to track last MLX read
unsigned long lastMLXReadTime = 0;
const unsigned long mlxInterval = 10000; // 10 seconds in ms

// Setup heater
int heatIndicatorLED = 30; // Not using RN
int heaterPWM = 10; // Bottom heater PWM signal
int heaterTopPWM = 9; // Top heater PWM signal

// Setup Bot Thermistor
int botThermistor = A1; // Bottom thermistor pin
float RREF = 10000; // Reference resistance
float botThermR = 0; // Calcualted resistance
float botThermT = 0; // Calcualted temp SHH
float botThermResistance; // Analog read of the thermistor

// Setup Top Thermistor
int topThermistor = A2; // Top thermistor pin
float topThermR = 0; // Calcualted resistance
float topThermT = 0; // Calcualted temp SHH
float topThermResistance; // Analog read of the thermistor

// PID Constants
double kp = 50; 
double ki = 10; 
double kd = 10;
bool firstHeat = false; // Indicator of whether this is the first time the heater has been heated to within 2 C of the setpoint
bool splitPID = true; // Indicator of whether we want to do split PID control for integral or not

// PID for bot
long currentTimeBOT, previousTimeBOT;
double elapsedTimeBOT;
double errorBOT, errorSampleBOT;
double lastErrorBOT;
float cumErrorBOT, rateErrorBOT;
double setPointBOT = 65;
double heatPIDBOT;
double PIDBOT;

// PID for TOP
long currentTimeTOP, previousTimeTOP;
double elapsedTimeTOP;
double errorTOP, errorSampleTOP;
double lastErrorTOP;
float cumErrorTOP, rateErrorTOP;
double setPointTOP = 65;
double heatPIDTOP;
double PIDTOP;

double setPointSample = 65; // Set point for IR sensor

//Time variables
double startTime; // Start of the device setup
double current; // Current time

int heatButton = 8; // Button that will turn on the heating
bool reachTemp = false; // Indicator of within 1 C of the set point

//Setup Thermocouple
#include <Adafruit_MAX31856.h>
#define DRDY_PIN 5
Adafruit_MAX31856 maxthermo = Adafruit_MAX31856(4, 5, 6, 7);
double ThermcoupleTemp = 0; // Initialize thermocouple temperature

//Setup OLED
#include <SPI.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#define SCREEN_WIDTH 128 // OLED display width, in pixels
//#define SCREEN_HEIGHT 32 // OLED display height, in pixels
#define SCREEN_HEIGHT 64 // OLED display height, in pixels
// Declaration for an SSD1306 display connected to I2C (SDA, SCL pins)
#define OLED_RESET     -1 // Reset pin # (or -1 if sharing Arduino reset pin)
#define SCREEN_ADDRESS 0x3D ///< See datasheet for Address
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// AS7341 Fluor
#include <Adafruit_AS7341.h>
Adafruit_AS7341 as7341;
int LED_blue = 12;
int LED_orange = 13;
uint16_t readings[12];
float counts[12];
int fluorLEDSwitch = 22;
double FAMValueBasic;
double LEDValueBasic;
double FAMReading;
double LEDReading;
double fluorOutput;
double IRSignal;
// TEX
double TEXValueBasic;
double TEXLEDValueBasic;
double TEXReading;
double TEXLEDReading;
double TEXfluorOutput;

//Setup ODRIVE
#include <HardwareSerial.h>
#include <SoftwareSerial.h>
#include <ODriveArduino.h>
// Printing with stream operator helper functions
template<class T> inline Print& operator <<(Print &obj,     T arg) { obj.print(arg);    return obj; }
template<>        inline Print& operator <<(Print &obj, float arg) { obj.print(arg, 4); return obj; }
HardwareSerial& odrive_serial = Serial1;
ODriveArduino odrive(odrive_serial);
float ODRV_pos;
float ODRV_pos_post;
float ODRV_last_pos;
float ODRV_offset = 0; // For new system this is 0
float ODRV_velocity;
int ODRV_well;
int ODRV_well_pre;
int ODRV_well_post;
bool ODRV_stop = true;
bool ODRVMLX = false;

// Buttons
int heatOnLED = 11;
int fluorOnLED = 14;

// Status
/*
0. Not initialized
1. No heat
2. Heat
3. Reach set point
*/
int heatStatus = 0;
/*
0. Not initialized
1. Pre-Heat (no fluorescence)
2. Amplification (fluorescence) 
3. Amplification (reached temp, Bob algorithm)
*/
int amplificationStatus = 0;
bool lidOpen = false; 
double IRSignalMin = 800; // Minimum value for clear signal to determine if lid is open
static unsigned long lastUpdateScreen = 0;
static int currentScreen = 1;
String statusIndicator;

// Store data
// Define the size of the arrays
const int MAX_DATA_POINTS = 100;
const int NUM_DATA_COLUMNS = 3;
int nextIndexTemperature = 0;
int nextIndexWell1 = 0;
int nextIndexWell2 = 0;

float window = -60000; //Window from Harmony
float window_long_end = -360000;
float window_long_start = -420000;
float timePositive = 15000;

// float window = -6000; // Shorter times for testing
// float window_long_end = -36000;
// float window_long_start = -42000;
// float timePositive = 15000;

float rollingAverageWell1;
float rollingAverageLongWell1;
/* Positive well
0. Negative
1. Positive
2. POSITIVE CALL
*/
int positiveWell1;
int flagWell1 = 0;
long startTimeWell1 = 0;
long elapsedWell1 = 0; 
float rollingAverageWell2;
float rollingAverageLongWell2;
/* Positive well
0. Negative
1. Positive
2. POSITIVE CALL
*/
int positiveWell2;
int flagWell2 = 0;
long startTimeWell2 = 0;
long elapsedWell2 = 0; 


float multiplier = 1.5;

// Declare the arrays
float temperatureData[MAX_DATA_POINTS][NUM_DATA_COLUMNS]; // Time, Temp, Fluor 
float well1Data[MAX_DATA_POINTS][NUM_DATA_COLUMNS]; // Time, Temp, Fluor 
float well2Data[MAX_DATA_POINTS][NUM_DATA_COLUMNS]; // Time, Temp, Fluor 

// RT heat step
unsigned long startRTTime = 0;
bool initialHeatComplete = false;
bool secondStage = false;  // To track the switch from 50°C to 65°C
float maxHeater = 75; // Max heater temp
float cumuReset = 0.5; // Reset temp for I 

// Setup function
void setup() {
  Serial.begin(9600);
  while (!Serial) {
    ; // Wait until Serial is ready
  }
  Serial.println(""); // This line won't be printed
  Serial.println("This board is running: ");
  Serial.println(F(__FILE__));
  Serial.print("Compiled on: ");
  Serial.println(F(__DATE__ " " __TIME__));
  Serial.println(freeMemory());

  startTime = millis();
  startRTTime = startTime;

  initializeIO();
  initializeThermocouple();
  initializeMLX();
  initializeOLED();
  initializeAS7341();
  initializeODRIVE();
  initializeFlashLights();
  
  initializeArrays();
  initializeAmplificationSettings();

  printColumnTitles();
  readDHTTempHum();
  
  heatStatus = 1; // Initialized heat status
  amplificationStatus = 1;
  debugSettings();
}

// the loop function runs over and over again forever
void loop() {
  current = millis() - startTime; // calculate current time
  int switchHeatOn = digitalRead(heatButton); //heat switch - this determines when to start the heating
  int amplificationOn = digitalRead(fluorLEDSwitch); //amplification switch - this determines when to start amplification
  int steadyStateOn = digitalRead(steadyStateButton); //steady state switch - this determines when to start steady state

  determineAmpStatus(amplificationOn); 
  determineHeatStatus(switchHeatOn);

  fluorescenceLED(); // Turns on the blue LED and the button LED
  delay(100); // Make sure that LED has switched fully - this adds time but ensures good reading
  
  ODRV_well_pre = getODRVPos(ODRV_pos); // Get position before fuorescence read
  getODRVVelocity(); 
  readAS7341AllChannels();
  extractAS7341FAM(); // Extract FAM/Blue LED

  // Only update MLX temps every 5 seconds when at 65C for 5 mins
  if (secondStage and millis() - startRTTime >= 5 * 60 * 1000) {
    if (millis() - lastMLXReadTime >= mlxInterval) {
      MLXObjectTempTEMP = MLXSensor.getObjectTemp(); // Object temp
      MLXSensorTempTEMP = MLXSensor.getSensorTemp(); // Sensor temp
      lastMLXReadTime = millis();
    }
    else {}
  }
  else {
      MLXObjectTempTEMP = MLXSensor.getObjectTemp(); // Object temp
      MLXSensorTempTEMP = MLXSensor.getSensorTemp(); // Sensor temp
  }
  // MLXObjectTempTEMP = MLXSensor.getObjectTemp(); //Get the temperature of the object we're looking at
  // MLXSensorTempTEMP = MLXSensor.getSensorTemp(); //Get the temperature of the sensor
  lidIsOpen();
  ODRV_well_post = getODRVPos(ODRV_pos); // Get position after fuorescence read
  ODRV_well = getODRVWell(ODRV_well_pre,ODRV_well_post); // Return the well if the wells before and after are the same. Else return 0.

  readThermistors();

  if(amplificationStatus == 2) {reachTempAmp(MLXObjectTemp, setPointSample, amplificationStatus);}
  if(amplificationStatus == 3) {
    checkPositive(well1Data, nextIndexWell1, rollingAverageWell1, rollingAverageLongWell1, positiveWell1, flagWell1, startTimeWell1, elapsedWell1);
    checkPositive(well2Data, nextIndexWell2, rollingAverageWell2, rollingAverageLongWell2, positiveWell2, flagWell2, startTimeWell2, elapsedWell2);
    //printArray(well1Data, 10,3);
  }
  
  ThermcoupleTemp = maxthermo.readThermocoupleTemperature();
  
  // MLX temperature read (only if over the temp sensor for a rectangular disk) 
  // If lid open don't take a new value
  // Also if overWellIR then only take when over a well (new case to take the reading earlier in between checking wells but only use here
  if ((ODRV_well == -1 or rectDisk == false) and !lidOpen) {
    if (!overWellIR or ODRV_well != 0) {
      //MLXObjectTemp = MLXSensor.getObjectTemp(); //Get the temperature of the object we're looking at
      //MLXSensorTemp = MLXSensor.getSensorTemp(); //Get the temperature of the sensor
      MLXObjectTemp = MLXObjectTempTEMP; //Get the temperature of the object we're looking at
      MLXSensorTemp = MLXSensorTempTEMP; //Get the temperature of the sensor
    }
  }

  statusDescriptionSet();
  // HEATING BEGINS
  if (switchHeatOn == 1) { 
    // Set initial conditions for 50°C if not started
    if (!initialHeatComplete) {
      setPointSample = 50;
      setPointBOT = 50;
      setPointTOP = 50;
      maxHeater = 62.5;
      // PID Constants
      kp = 50; // ***** For split (single 100)
      ki = 5; // ******** FOR SPLIT (other was 0.01)
      kd = 10;
      cumuReset = 0.5;
      
      if (startRTTime == startTime && amplificationStatus == 2) { // Start the timer only when we go into amplification
        firstHeat = false;
        startRTTime = millis(); // Start timing for initial heating phase
        cumErrorBOT = 0;
        cumErrorTOP = 0; // Reset I term from pre-heat
      }
      // Check if 10 minutes have passed at 50°C (5 FOR NOW)
      if (millis() - startRTTime >= 10.0 * 60.0 * 1000.0 and startRTTime != startTime) { // Onyl do this after 50 has started or else it will just be 5 min from start
        initialHeatComplete = true; // Mark the initial heating phase as complete
        secondStage = true;         // Trigger the transition to the second stage
        startRTTime = millis();     // Reset start time for the next phase
        firstHeat = false;          // Reset firstHeat to re-enable heating logic for next stage
        cumErrorBOT = 0;            // Reset cumulative errors after RT heating
        cumErrorTOP = 0;
      }
    }

    if (steadyState or steadyStateOn == 1) { // Allows to use the button to turn this on - can turn on after reach 65 so I know it cant revert
      initialHeatComplete = true; // Mark the initial heating phase as complete
      secondStage = true;         // Trigger the transition to the second stage
      //startRTTime = millis();     // Reset start time for the next phase
      firstHeat = false;          // Reset firstHeat to re-enable heating logic for next stage
      //cumErrorBOT = 0;            // Reset cumulative errors after RT heating
      //cumErrorTOP = 0;
    }
    
    // Transition to the second stage at 65°C if the initial heating is complete
    if (secondStage) {
      setPointSample = 65;
      setPointBOT = 65;
      setPointTOP = 65;
      maxHeater = 85;
      kp = 50; // ***** For split (single 100)
      ki = 10; // ******** FOR SPLIT (other was 0.01)
      kd = 10;
      cumuReset = 1.0;

      // Check if 60 minutes have passed at 65°C
      if (millis() - startRTTime >= 90.0 * 60.0 * 1000.0) { // I don't need it to stop
        //switchHeatOn = 0;            // Turn off heating after completing the second stage
        //secondStage = false;         // Reset second stage flag
        Serial.println("DONE");
      }
    }
    
    if(amplificationStatus == 1) {splitPID = false;} // Not split PID when pre-heat
    else {splitPID = true;}

    PIDBOT = computePID(botThermT, MLXObjectTemp, currentTimeBOT, previousTimeBOT, elapsedTimeBOT, errorBOT,
      errorSampleBOT, lastErrorBOT, cumErrorBOT, rateErrorBOT, setPointBOT); // PID control (Split if determined)
    PIDTOP = computePID(topThermT, MLXObjectTemp, currentTimeTOP, previousTimeTOP, elapsedTimeTOP, errorTOP,
      errorSampleTOP, lastErrorTOP, cumErrorTOP, rateErrorTOP, setPointTOP); // PID control (Split if determined)

    heatPIDBOT = mapPID(PIDBOT); // Map PID values to 0-255
    heatPIDTOP = mapPID(PIDTOP); // Map PID values to 0-255
    
    // Set a hard cap on the heaters at 85
    if(botThermT>maxHeater) {heatPIDBOT = 0;}
    if(topThermT>maxHeater) {heatPIDTOP = 0;}

    // Reset the cumulative error when close to temperature to minimize the overshoot
    if (MLXObjectTemp > setPointSample - 5 and !firstHeat) {
      cumErrorBOT = 0;
      cumErrorTOP = 0;
      //Serial.println("-5");
    }
    if (MLXObjectTemp > setPointSample - cumuReset and !firstHeat) {
      firstHeat = true;
      cumErrorBOT = 0;
      cumErrorTOP = 0;
      //Serial.println("-2");
    }
    
    analogWrite(heaterPWM, heatPIDBOT); // Send signal to flex heater
    analogWrite(heaterTopPWM, heatPIDTOP); // Send signal to flex heater
    printAllValues();
  }
  else {
    heatPIDBOT = 0; // Set PWM values to 0
    analogWrite(heaterPWM, 0); // Send signal to flex heater
    heatPIDTOP = 0;
    analogWrite(heaterTopPWM, 0); // Send signal to flex heater
    printAllValues();
  }
  saveData();
  //graphArray(temperatureData, nextIndexTemperature, "Temperature", 1);
  //graphArray(temperatureData, nextIndexTemperature, "Fluor", 2);
  //graphArray(well1Data, nextIndexWell1, "Well 1");
  //displayOLED();
  checkErrors(amplificationStatus, MLXObjectTemp, ODRV_pos);
  displayAllScreens();
}


// Initialization functions. These are all of the functions that will be run to begin the code
/// @brief This will initialize the button lights to flash. Ensure function but also for fun
void initializeFlashLights() {
  for (int i = 0; i < 10; i++) {
    digitalWrite(heatOnLED, LOW); // LOW IS ON
    digitalWrite(fluorOnLED, LOW); // LOW IS ON
    delay(50);
    digitalWrite(heatOnLED, HIGH); // HIGH IS OFF
    digitalWrite(fluorOnLED, HIGH); // HIGH IS OFF
    delay(50);
  }
}
/// @brief Initialize I/O for the code, buttons, heater PWM, button LEDs 
void initializeIO() {
  // Setup for all sensors
  while (!Serial) delay(10);
  dht.begin(); // Begin DHT sensor

  pinMode(heatButton, INPUT); 
  pinMode(heaterPWM, OUTPUT);
  pinMode(heaterTopPWM, OUTPUT);
  pinMode(heatIndicatorLED, OUTPUT); 
  analogWrite(heaterPWM, 0); // Setup heaters as off
  analogWrite(heaterTopPWM, 0);

  // Steady state button
  pinMode(steadyStateButton, INPUT);
  
  // Buttons LED 
  pinMode(heatOnLED, OUTPUT);
  pinMode(fluorOnLED, OUTPUT);
}
/// @brief Initialize the thermocouple as a T type thermocouple and check if the MAX returns the same value. Set mode to continuous
void initializeThermocouple() {
  pinMode(DRDY_PIN, INPUT);
  if (!maxthermo.begin()) {
    Serial.println("Could not initialize thermocouple.");
    //while (1) delay(10);
  }
  maxthermo.setThermocoupleType(MAX31856_TCTYPE_T);
  Serial.print("Thermocouple type: ");
  switch (maxthermo.getThermocoupleType() ) {
    case MAX31856_TCTYPE_B: Serial.println("B Type"); break;
    case MAX31856_TCTYPE_E: Serial.println("E Type"); break;
    case MAX31856_TCTYPE_J: Serial.println("J Type"); break;
    case MAX31856_TCTYPE_K: Serial.println("K Type"); break;
    case MAX31856_TCTYPE_N: Serial.println("N Type"); break;
    case MAX31856_TCTYPE_R: Serial.println("R Type"); break;
    case MAX31856_TCTYPE_S: Serial.println("S Type"); break;
    case MAX31856_TCTYPE_T: Serial.println("T Type"); break;
    case MAX31856_VMODE_G8: Serial.println("Voltage x8 Gain mode"); break;
    case MAX31856_VMODE_G32: Serial.println("Voltage x8 Gain mode"); break;
    default: Serial.println("Unknown"); break;
  }
  maxthermo.setConversionMode(MAX31856_CONTINUOUS);
}
/// @brief Initialize the MLX temp sensor and decide the sensor address. Deal with errors.
void initializeMLX() {
    //MLX Sensor Setup
  Wire.begin(); 
   
  byte sensorAddress = 0x3A; //The default I2C address for the SparkX breakout board is 0x3B.
  //But if you close the I2C ADR jumper it changes the device address to 0x3A.
  //This allows you to have up to two sensors on one I2C bus.
  MLX90632::status errorFlag; //Declare a variable called errorFlag that is of type 'status'
  //Now begin communication with all these settings
  //MLXSensor.enableDebugging(Serial);
  MLXSensor.begin(sensorAddress, Wire, errorFlag); //Useful on SAMD21 and other platforms
  //The errorFlag is set to one of a handful of different errors
  if(errorFlag == MLX90632::SENSOR_SUCCESS)
  {
    Serial.println("MLX90632 online!");
  }
  else
  {
    //Something went wrong
    if(errorFlag == MLX90632::SENSOR_ID_ERROR) Serial.println("MLX Sensor ID did not match the sensor address. Probably a wiring error.");
    else if(errorFlag == MLX90632::SENSOR_I2C_ERROR) Serial.println("MLX Sensor did not respond to I2C properly. Check wiring.");
    else if(errorFlag == MLX90632::SENSOR_TIMEOUT_ERROR) Serial.println("MLX Sensor failed to respond.");
    else Serial.println("Other Error");
  }
  MLXObjectTemp = MLXSensor.getObjectTemp(); //Get the temperature of the object we're looking at
  MLXSensorTemp = MLXSensor.getSensorTemp(); //Get the temperature of the sensor
}
/// @brief Initialize the OLED display. Display "Initializing"
void initializeOLED() {
  //Setup OLED display
  if (!display.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS)) {
    Serial.println(F("SSD1306 allocation failed"));
    for (;;); // Don't proceed, loop forever
  }
  display.clearDisplay();
  // Draw a single pixel in white - just to make sure this thing works
  display.drawPixel(10, 10, SSD1306_WHITE);
  display.display();
  delay(50);
  display.setTextSize(1); // Draw 2X-scale text
  display.setTextColor(SSD1306_WHITE);
  display.clearDisplay();
  display.setCursor(0, 0);            // Start at top-left corner - xpos, ypos
  display.println("Initializing ...");
  display.display();
  delay(100);
}
/// @brief Initialize the AS7341 fluorescence sensor and the fluorescence LEDs. Initilize the settings for the sensor.
void initializeAS7341() {
    // Setup AS7341 Sensor
  pinMode(LED_blue, OUTPUT); // Setup BLUE excitation LED
  pinMode(LED_orange, OUTPUT); // Setup BLUE excitation LED

  if (!as7341.begin()){
    Serial.println("Could not find AS7341");
    while (1) { delay(10); }
  }
  as7341.setATIME(100); // Setup values from fluorescence v1.7
  as7341.setASTEP(999);
  as7341.setGain(AS7341_GAIN_256X);
  as7341.enableLED(false);

  analogWrite(heatIndicatorLED, 0); // Write LED as off

  if (!as7341.readAllChannels(readings)){
    Serial.println("Error reading all channels!");
    return;
  }
  readAS7341Parameters();
  pinMode(fluorLEDSwitch, INPUT); // setup switch for LED off and on

  analogWrite(LED_blue, 200);
  analogWrite(LED_orange, 0);
  delay(100); 
  analogWrite(LED_blue, 0);
  analogWrite(LED_orange, 200);
  delay(100); 
  analogWrite(LED_blue, 0);
  analogWrite(LED_orange, 0);
  delay(100);

}
/// @brief Initialize the ODrive connection and get the initial position
void initializeODRIVE() {
      // Setup ODRIVE
  odrive_serial.begin(115200); // ODrive uses 115200 baud
  ODRV_pos = odrive.GetPosition(0);
}
/// @brief Print the amplification window settings to the serial so that I can keep track of them
void initializeAmplificationSettings() {
  Serial.print("Window: "); Serial.println((window/-1000));
  Serial.print("Long Start: "); Serial.println((window_long_start/-1000));
  Serial.print("Long End: "); Serial.println((window_long_end/-1000));
}
/// @brief Settings for debugging. Fluorescence shorter read.
void debugSettings() {
  if (debug) {
    as7341.setATIME(29); // Setup values from fluorescence v2.3 (short time scale)
    as7341.setASTEP(599);
  }
}

// Serial printing function. Printing that allows for data collection from Arduino
/// @brief Print all of the variable output names to the Serial for the Excel output
void printColumnTitles() {
    // Print column titles
  Serial.print("Time"); Serial.print("\t");
  Serial.print("Bot_Resistor"); Serial.print("\t");
  Serial.print("Bot_resistance"); Serial.print("\t");
  Serial.print("Bot_Temp"); Serial.print("\t");
  Serial.print("Therm_Temp"); Serial.print("\t");
  Serial.print("DHT_temp"); Serial.print("\t");
  Serial.print("DHT_hum"); Serial.print("\t");
  Serial.print("Bot_set"); Serial.print("\t");
  Serial.print("Bot_PID"); Serial.print("\t");
  Serial.print("Bot_error"); Serial.print("\t");
  Serial.print("Bot_cumError"); Serial.print("\t");
  Serial.print("Bot_rateError"); Serial.print("\t");
  Serial.print("Bot_heatPID"); Serial.print("\t");
  Serial.print("Top_Resistor"); Serial.print("\t");
  Serial.print("Top_resistance"); Serial.print("\t");
  Serial.print("Top_temp"); Serial.print("\t");
  Serial.print("Top_set"); Serial.print("\t");
  Serial.print("Top_PID"); Serial.print("\t");
  Serial.print("Top_error"); Serial.print("\t");
  Serial.print("Top_cumError"); Serial.print("\t");
  Serial.print("Top_rateError"); Serial.print("\t");
  Serial.print("Top_heatPID"); Serial.print("\t");
  Serial.print("MLXObjectTemp"); Serial.print("\t");
  Serial.print("MLXSensorTemp"); Serial.print("\t");
  Serial.print("FAM_Basic"); Serial.print("\t");
  Serial.print("LED_Basic"); Serial.print("\t");
  Serial.print("FAM/LED"); Serial.print("\t");
  Serial.print("FAM_Reading"); Serial.print("\t");
  Serial.print("LED_Reading"); Serial.print("\t");
  Serial.print("TEX_Basic"); Serial.print("\t");
  Serial.print("TEXLED_Basic"); Serial.print("\t");
  Serial.print("TEX/LED"); Serial.print("\t");
  Serial.print("TEX_Reading"); Serial.print("\t");
  Serial.print("TEXLED_Reading"); Serial.print("\t");
  Serial.print("Velocity"); Serial.print("\t");
  Serial.print("Position"); Serial.print("\t");
  Serial.print("Well"); Serial.print("\t");
  Serial.print("Well1_ShortAvg"); Serial.print("\t");
  Serial.print("Well1_LongAvg"); Serial.print("\t");
  Serial.print("Well1_Status"); Serial.print("\t");
  Serial.print("Well2_ShortAvg"); Serial.print("\t");
  Serial.print("Well2_LongAvg"); Serial.print("\t");
  Serial.print("Well2_Status"); Serial.print("\t");
  Serial.print("Heat_Status"); Serial.print("\t");
  Serial.print("Lid_Status"); Serial.print("\t");
  Serial.print("LED_Status"); Serial.print("\t");
  Serial.print("Error_Status"); Serial.print("\t");
  Serial.print("Amp_Status"); Serial.print("\t");
  Serial.println("ExtraData");
}
/// @brief Print all of the output values that I would like to track to the Serial monitor. If debug then calls other print
void printAllValues() {
  if (!debug) {
    Serial.print(current); Serial.print("\t");
    Serial.print(botThermResistance); Serial.print("\t");
    Serial.print(botThermR); Serial.print("\t");
    Serial.print(botThermT); Serial.print("\t");
    Serial.print(ThermcoupleTemp); Serial.print("\t");
    Serial.print(tempDHT); Serial.print("\t");
    Serial.print(humDHT); Serial.print("\t");
    Serial.print(setPointBOT); Serial.print("\t");
    Serial.print(PIDBOT); Serial.print("\t");
    Serial.print(errorBOT); Serial.print("\t");
    Serial.print(cumErrorBOT); Serial.print("\t");
    Serial.print(rateErrorBOT, 6); Serial.print("\t");
    Serial.print(heatPIDBOT); Serial.print("\t");
    Serial.print(topThermResistance); Serial.print("\t");
    Serial.print(topThermR); Serial.print("\t");
    Serial.print(topThermT); Serial.print("\t");
    Serial.print(setPointTOP); Serial.print("\t");
    Serial.print(PIDTOP); Serial.print("\t");
    Serial.print(errorTOP); Serial.print("\t");
    Serial.print(cumErrorTOP, 6); Serial.print("\t");
    Serial.print(rateErrorTOP); Serial.print("\t");
    Serial.print(heatPIDTOP); Serial.print("\t");
    Serial.print(MLXObjectTemp, 2); Serial.print("\t");
    Serial.print(MLXSensorTemp, 2); Serial.print("\t");
    Serial.print(FAMValueBasic); Serial.print("\t");
    Serial.print(LEDValueBasic); Serial.print("\t");
    Serial.print(fluorOutput,5); Serial.print("\t");
    Serial.print(FAMReading,5); Serial.print("\t");
    Serial.print(LEDReading,5); Serial.print("\t");
    Serial.print(TEXValueBasic); Serial.print("\t");
    Serial.print(TEXLEDValueBasic); Serial.print("\t");
    Serial.print(TEXfluorOutput,5); Serial.print("\t");
    Serial.print(TEXReading,5); Serial.print("\t");
    Serial.print(TEXLEDReading,5); Serial.print("\t");
    Serial.print(ODRV_velocity, 3); Serial.print("\t");
    Serial.print(ODRV_pos, 3); Serial.print("\t");
    Serial.print(ODRV_well); Serial.print("\t");
    Serial.print(rollingAverageWell1); Serial.print("\t");
    Serial.print(rollingAverageLongWell1); Serial.print("\t");
    Serial.print(positiveWell1); Serial.print("\t");
    Serial.print(rollingAverageWell2); Serial.print("\t");
    Serial.print(rollingAverageLongWell2); Serial.print("\t");
    Serial.print(positiveWell2); Serial.print("\t");
    Serial.print(heatStatus);Serial.print("\t");
    Serial.print(lidOpen);Serial.print("\t");
    Serial.print(LEDStatus);Serial.print("\t");
    Serial.print(ErrorStatus, BIN);Serial.print("\t");
    Serial.print(amplificationStatus);Serial.print("\t");
    printReadings(readings, 12);
    Serial.println();
  }
  else {
    printValuesDebug();
  }
}
/// @brief Print the important values to the Serial, temperatures, Fluor
void printValuesDebug() {
  Serial.print("Time: "); Serial.println(current);
  Serial.print("Status: "); Serial.println(statusIndicator);
  Serial.print("Bottom Therm: "); Serial.println(botThermT);
  Serial.print("Top Therm: "); Serial.println(topThermT);
  Serial.print("MLX Object: "); Serial.println(MLXObjectTemp);
  Serial.print("MLX Sensor: "); Serial.println(MLXSensorTemp);
  Serial.print("Thermocouple: "); Serial.println(ThermcoupleTemp);
  Serial.print("FAM: "); Serial.println(FAMReading);
  Serial.print("LED: "); Serial.println(LEDReading);
  Serial.print("Fluorescence: "); Serial.println(fluorOutput);
  Serial.print("TEX: "); Serial.println(TEXReading);
  Serial.print("TEX LED: "); Serial.println(TEXLEDReading);
  Serial.print("TEX Fluor: "); Serial.println(TEXfluorOutput);
  Serial.print("ODrive Position: "); Serial.println(ODRV_pos);
  Serial.print("ODrive Well: "); Serial.println(ODRV_well);
  Serial.print("Open signal: "); Serial.println(IRSignal);
  Serial.println("");
}

// Heating functions
/// @brief Generate temperature information from the resistance of the thermistor using SteinHart Hart equation
/// @param R Thermistor resistance
/// @return Temperature
float SHH(float R){
  float A = 0.000874022779276159;
  float B = 0.000253789577124884;
  float C = 1.82391198361997*pow(10,(-7));
  float Tk = 273.15;

  float T = 1/(A + B*log(R) + C*pow(log(R), 3));
  T = T - Tk;
  return T;
}
/// @brief Compute the PID constant for a heater. This allows for both split PID and normal PID. splitPID boolean controls whether split or not.
/// @param inp Heater temperature (in our case from the thermistor)
/// @param sample Sample temperature (in our case the IR temp sensor)
/// @param currentTime Current time value that willbe used to caluculate elapsed time
/// @param previousTime Previous time value from last iteration
/// @param elapsedTime Elapsed time calculated in function
/// @param error Proportional error term (direct error from setpoint)
/// @param errorSample Proportional error term for split PID (direct error of sample from setpoint)
/// @param lastError Last error value (not from sample)
/// @param cumError Integral error
/// @param rateError Derivative error
/// @param setPoint Setpoint value
/// @return The PID constant is returned. This is the output from the equation that determined heating
double computePID(double inp, double sample, long& currentTime, long& previousTime, double& elapsedTime, 
  double& error, double& errorSample, double& lastError, float& cumError, float& rateError, double& setPoint) {
  
  currentTime = millis();
  elapsedTime = (double)(currentTime-previousTime)/1000.0; // compute elapsed time   

  // P - Proportional
  error = setPoint - inp; // determine error value
  errorSample = setPointSample - sample; // determine sample error value
  
  // I - Integral
  if (splitPID) {cumError += errorSample * elapsedTime;} // compute integral of error in time step using SAMPLE (**SPLIT PID**)
  else {cumError += error * elapsedTime;} // compute integral of error in time step using heater

  // D - Derivative
  rateError = (error - lastError)/elapsedTime; // compute derivative

  double out = kp*error +ki*cumError+kd*rateError; // PID out
  lastError = error;
  previousTime = currentTime;

  //Serial.println("A");
  //Serial.println(out);
  return out;
}
double mapPID(double PIDInput) {
  double PIDOutput;
  if (PIDInput < 0) {
      PIDOutput = 0;
  }
  else if (PIDInput >255) {
    PIDOutput = 255;
  }
  else {
    PIDOutput = PIDInput;
  }
  return PIDOutput;
}
/// @brief Read the thermistor resistance and calculate temp
void readThermistors () {
  // Read both thermistors
  botThermResistance = analogRead(botThermistor);
  topThermResistance = analogRead(topThermistor);
  botThermR = ((1023 * RREF)/botThermResistance) - RREF; // Calculate the thermistor resistance
  botThermT = SHH(botThermR); // Calculate thermistor temp based on Steinhart Hart
  topThermR = ((1023 * RREF)/topThermResistance) - RREF; // Calculate the thermistor resistance
  topThermT = SHH(topThermR); // Calculate thermistor temp based on Steinhart Hart
}
/// @brief Read the DHT temperature and humidity every 2 seconds
void readDHTTempHum() {
  // DHT Read
  if (collectTimeDHT + 2000 < current) {
    humDHT = dht.readHumidity();
    tempDHT= dht.readTemperature();
    collectTimeDHT = current;
  }
}
/// @brief Take in the heater button and determine if heating should be on. If the heater reaches the setpoint then change heat status
/// @param button Input of the heater button
void determineHeatStatus(int button) {
  // First check if the heater switch is on
  if (button == 1) {
    heatStatus = 2;
    digitalWrite(heatOnLED, LOW); // LOW IS ON
  }
  else {
    heatStatus = 1;
    digitalWrite(heatOnLED, HIGH); // HIGH IS OFF
  }

  // Then check if the heater has reached the setpoint
  if (MLXObjectTemp > setPointSample - 1 and MLXObjectTemp < setPointSample + 1) {
    digitalWrite(heatIndicatorLED, HIGH);
    reachTemp = true;
    heatStatus = 3;
    //Serial.println("Setpoint");
  }
  else {
    digitalWrite(heatIndicatorLED, LOW);
    reachTemp = false;
  }
}

// Fluorescence functions
/// @brief Extract the FAM and Blue LED channels from the readings matrix
void extractAS7341FAM() {
  FAMReading = readings[3];
  LEDReading = readings[2];
  FAMValueBasic = as7341.toBasicCounts(readings[3]);
  LEDValueBasic = as7341.toBasicCounts(readings[2]);
  fluorOutput = FAMReading/LEDReading;

  TEXReading = readings[8]; // There are 2 channels in readings that are skipped
  TEXLEDReading = readings[7];
  TEXValueBasic = as7341.toBasicCounts(readings[8]);
  TEXLEDValueBasic = as7341.toBasicCounts(readings[7]);
  TEXfluorOutput = TEXReading/TEXLEDReading;

  if (fluorOutput > 5) {
    fluorOutput = 0;
  }
  //Serial.println(as7341.toBasicCounts(readings[3]));
  //Serial.println(as7341.toBasicCounts(readings[2]));  
}
/// @brief Read all channels from AS7341 and check errors
void readAS7341AllChannels () {
  if (!as7341.readAllChannels(readings)){
    Serial.println("Error reading all channels!");
    return;
  }
}
/// @brief Read and print AS7341 parameters (gain, int, ASTEP, ATIME)
void readAS7341Parameters() {
  Serial.print("AS7341 Gain: ");Serial.println(as7341.getGain()); 
  Serial.print("AS7341 Integration Time: ");Serial.println(as7341.getTINT()); 
  Serial.print("AS7341 ASTEP: ");Serial.println(as7341.getASTEP());
  Serial.print("AS7341 ATIME: ");Serial.println(as7341.getATIME());
}
/// @brief Determine the amplification status from the buttons
/// @param button The button value for the amplification button
void determineAmpStatus(int button) {
  if(button == 1) {
    amplificationStatus = 2;
  }
  else {
    amplificationStatus = 1;
    LEDStatus = 0;
  }
}
/// @brief Turn on the fluor LED if the fluorescence status is 2 (on) and at the 65 stage
void fluorescenceLED() {
  if (amplificationStatus == 2 and LEDStatus == 0) { //and secondStage I am fine with fluor during 50 C step
    LEDStatus = 1;
    loopCounter = 0; // Reset loop count
  }
  else if (LEDStatus == 1 and loopCounter % TOGGLE_INTERVAL == 0) { // Change every 2 loops
    LEDStatus = 2;
    loopCounter = 0; // Reset loop count
  }
  else if (LEDStatus == 2 and loopCounter % TOGGLE_INTERVAL == 0) {
    LEDStatus = 1;
    loopCounter = 0; // Reset loop count
  }

  loopCounter++;

  if (onlyFAM) {
    LEDStatus = 1; ////// ******** OVERRIDE TO ONLY FAM
  }

  if ((amplificationStatus == 2 or amplificationStatus == 3) ) { //and secondStage (could add back in to only flour at 65)
      if (LEDStatus == 1) {
      digitalWrite(fluorOnLED, LOW); // LOW IS ON
      analogWrite(LED_blue, 200);
      analogWrite(LED_orange, 0);
      } else if (LEDStatus == 2) {
      digitalWrite(fluorOnLED, LOW); // LOW IS ON
      analogWrite(LED_blue, 0);
      analogWrite(LED_orange, 200);
      }
    }
    else {
      digitalWrite(fluorOnLED, HIGH); // HIGH IS OFF
      analogWrite(LED_blue, 0);
      analogWrite(LED_orange, 0);
    }
  delay(50); // Delay to allow for fluorescence excitation
}

// Odrive functions
/// @brief Get the ODRIVE position and compare with the last position to see if there has been movement. Determine well #
/// @param lastPos Last position of the ODrive
/// @return The well # (0 is no well)
int getODRVPos(double lastPos) {
  ODRV_last_pos = lastPos; // Gets the last position
  ODRV_pos = odrive.GetPosition(0) - ODRV_offset; // Get ODRIVE pos (- offset since the ODRV is offsetting)
  int well;

  if (abs(ODRV_pos - ODRV_last_pos) < 0.1) { // Determine if it has moved
    ODRV_stop = true;
  }
  else {
    ODRV_stop = false;
  }

  //// Circular Disk
  int relativePos = abs(ExtractDecimalPart(ODRV_pos));
  int tolerance = 5;              // Tolerance for well proximity
  int sectionSize = 100 / numWells; // Size of each well section
  well = 0;                        // Default to 0 when between wells
  if (ODRV_stop && !rectDisk) {
      // Special case for well 1: within tolerance of either 0 or 100
      if (relativePos <= tolerance || relativePos >= 100 - tolerance) {
          well = 1;
      } else {
          // Loop through other wells
          for (int i = 0; i < numWells; i++) {
              int wellPosition = i * sectionSize + sectionSize; // Center of each well section
              
              // Check if relativePos is within the tolerance range of the well position
              if (relativePos >= wellPosition - tolerance && relativePos <= wellPosition + tolerance) {
                  well = i+2;  // Set well to the 1-indexed well number
                  break;         // Exit loop once the well is identified
              }
          }
      }
  } else {
      well = 0; // Set to 0 when in between wells
  }

  //// Rectangular disk
  if(rectDisk){
    // Determines the well information and will set 0 if not a well or if there has been movement
    if (abs(ExtractDecimalPart(ODRV_pos)) - 0 < 10 or abs(abs(ExtractDecimalPart(ODRV_pos)) - 100) < 10 and ODRV_stop) { // Determine well 1
      well = 1;
    }
    else if (abs(abs(ExtractDecimalPart(ODRV_pos)) - 50) < 10 and ODRV_stop) { // Determine well 2
      well = 2;
    }
    else if (abs(abs(ExtractDecimalPart(ODRV_pos)) - 25) < 10 and ODRV_stop) { // Determine temp well
      well = -1;
    }
    else { 
      well = 0;
    }
  }

  // Almost circle disk case
  if(almostCircle) {
       // Determines the well information and will set 0 if not a well or if there has been movement
    if (abs(ExtractDecimalPart(ODRV_pos)) - 0 < tolerance or abs(abs(ExtractDecimalPart(ODRV_pos)) - tolerance) < 10 and ODRV_stop) { // Determine well 1
      well = 1;
    }
    else if (abs(abs(ExtractDecimalPart(ODRV_pos)) - 12) < tolerance and ODRV_stop) { // Determine well 2
      well = 2;
    }
    else if (abs(abs(ExtractDecimalPart(ODRV_pos)) - 50) < tolerance and ODRV_stop) { // Determine well 2
      well = 3;
    }
    else if (abs(abs(ExtractDecimalPart(ODRV_pos)) - 62) < tolerance and ODRV_stop) { // Determine well 2
      well = 4;
    }
    else if (abs(abs(ExtractDecimalPart(ODRV_pos)) - 25) < tolerance and ODRV_stop) { // Determine temp well
      well = -1;
    }
    else { 
      well = 0;
    }
  }

  return well;
}
/// @brief This checks the well position to ensure no errors. Will first determine no movemment in fluorescence reading. Also check to see if lid open
/// @param pre Position before fluor read
/// @param post Position after fluor read
/// @return The Well # (0 indicates movement or lid open)
int getODRVWell(int pre, int post) {
  int returnWell;
  if (pre == post) {
    returnWell = pre;
  }
  else {
    returnWell = 0;
  }
  if (lidOpen) {
    returnWell = 0;
    }
  return returnWell;
}
void getODRVVelocity() {
  ODRV_velocity = odrive.GetVelocity(0);
}
/// @brief Used to determine the well position. Extracts the decimal portion of the position (Tenths and hundredths)
/// @param Value Input value. In this case the position (eg. 1.51)
/// @return Decimal portion (51)
int ExtractDecimalPart(float Value) { // Used to determine well
  int IntegerPart = (int)(Value);
  int DecimalPart = 100 * (Value - IntegerPart); //1000 b/c my float values always have exactly 4 decimal places
  return DecimalPart;
}

// OLED Functions. Function for the numerical OLED display
void displayOLED() {
  float timeElapsed = current/1000;

  String w1Indicator = "-";
  String w2Indicator = "-";

  if (positiveWell1 == 2) {w1Indicator = "+";}
  if (positiveWell2 == 2) {w2Indicator = "+";}
  display.clearDisplay();
  display.setCursor(0, 0);            // Start at top-left corner - xpos, ypos
  display.println("Centrifugal Heater v1");
  display.print("Status: "); display.print(statusIndicator);
  if (ErrorStatus != 0) { display.print(" ERR");}
  if (hasError(ERROR_HEATING_DROP)) {display.print(" HEAT");}
  if (hasError(ERROR_NO_ROTATION)) {display.print(" MOTOR");}
  display.println(""); // new line
  display.print("Time:"); display.print(timeElapsed,1);
  if(amplificationStatus == 2 or amplificationStatus == 3) {display.print("("); display.print((int)setPointSample); display.print(":"); display.print(((millis() - startRTTime)/1000.0/60.0),1); display.print(")");}
  display.println(""); // new line
  display.print("B/T Temp: "); display.print(botThermT);display.print("/");display.print(topThermT);
  display.print("MLX Temp: "); display.println(MLXObjectTemp);
  display.print("Pos: "); display.print(ODRV_pos); display.print(" W:"); display.println(ODRV_well);
  if (LEDStatus == 1) {
    display.print("FAM*:"); display.print(fluorOutput); display.print("("); display.print(FAMReading,0); 
    display.print(","); display.print(LEDReading,0); display.println(")");
    display.print("TEX:"); display.print(TEXfluorOutput,3); display.print("("); display.print(TEXReading,0); 
    display.print(","); display.print(TEXLEDReading,0); display.println(")");
  }
  else if (LEDStatus == 2) {
    display.print("FAM:"); display.print(fluorOutput); display.print("("); display.print(FAMReading,0); 
    display.print(","); display.print(LEDReading,0); display.println(")");
    display.print("TEX*:"); display.print(TEXfluorOutput,3); display.print("("); display.print(TEXReading,0); 
    display.print(","); display.print(TEXLEDReading,0); display.println(")");
  }
  else {
    display.print("FAM:"); display.print(fluorOutput); display.print("("); display.print(FAMReading,0); 
    display.print(","); display.print(LEDReading,0); display.println(")");
    display.print("TEX:"); display.print(TEXfluorOutput,3); display.print("("); display.print(TEXReading,0); 
    display.print(","); display.print(TEXLEDReading,0); display.println(")");
  }
  //display.print("W1:"); display.print(rollingAverageWell1); display.print(w1Indicator); display.print(" ");
  //display.print("W2:"); display.print(rollingAverageWell2); display.print(w2Indicator);
  display.display();
//  display.clearDisplay();
//  display.setCursor(0, 0);            // Start at top-left corner - xpos, ypos
//  display.println("Centrifugal Heater v1");
//  display.print("Status: "); display.println(statusIndicator);
//  display.print("Time: "); display.println(timeElapsed);
//  display.print("Bot Temp: "); display.println(botThermT);
//  display.print("Top Temp: "); display.println(topThermT);
//  display.print("MLX Temp: "); display.println(MLXObjectTemp);
//  display.print("Pos: "); display.print(ODRV_pos); display.print(" W:"); display.println(ODRV_well);
//  display.print("Fl:"); display.print(fluorOutput); display.print("("); display.print(FAMReading,0); 
//  display.print(","); display.print(LEDReading,0); display.println(")");
//  display.display();
}
/// @brief This will take the different status indicators and determine the status message
void statusDescriptionSet () {
  if (heatStatus == 1) {
    statusIndicator = "Off";
  }
  else if (heatStatus == 2 || heatStatus == 3) {
    if (amplificationStatus == 1) {
      statusIndicator = "Pre-Heat";
      if (heatStatus == 3) {statusIndicator = "Pre-Heated";}
    }
    else if (amplificationStatus == 2) {
      statusIndicator = "Amp";
    }
    else if (amplificationStatus == 3) {
      statusIndicator = "Amp+T";
      if (positiveWell1 == 2) {statusIndicator += " 1+";}
      if (positiveWell2 == 2) {statusIndicator += " 2+";}
    }
  }
  else {
    statusIndicator = "Error";
  }

  if (lidOpen) {statusIndicator = "LID OPEN";}
}

// Graphing functions for temperature and fluorescence
/// @brief Initialize the arrays to all zeros for well collection. Temp, well1, well2.
void initializeArrays() {
  for (int i = 0; i < MAX_DATA_POINTS; i++) {
    for (int j = 0; j < NUM_DATA_COLUMNS; j++) {
      temperatureData[i][j] = 0.0;
      well1Data[i][j] = 0.0;
      well2Data[i][j] = 0.0;
    }
  }
}
/// @brief Function that saves data for individual wells if the ODrive output indicates correct position
void saveData() {
  float elapsedTimeTemporary;
  float MLXObjectTemporary;
  float fluorTemporary; 
  float well1RFUTemporary;
  float well2RFUTemporary;
  
  elapsedTimeTemporary = current;
  MLXObjectTemporary = MLXObjectTemp;

  // This will set the fluorescence to 0 if the fluorescence status is off (either setup issues or if the device is open)
  if (isnan(fluorOutput)) { fluorTemporary = 0;}
  else if (amplificationStatus == 1 or amplificationStatus == 0) {fluorTemporary = 0;}
  else {fluorTemporary = fluorOutput;}

  if (ODRV_well == 1 && amplificationStatus == 3) {
    well1RFUTemporary = fluorTemporary;
    float lastWell1;
    if (nextIndexWell1 > 0) {lastWell1 = well1Data[nextIndexWell1-1][2];}
    else {lastWell1 = well1RFUTemporary;}
    // 0.5 here is resist large changes in fluorescence (unrealistic)
    if (nextIndexWell1 < MAX_DATA_POINTS and abs(well1RFUTemporary - lastWell1) < 0.5) {
      well1Data[nextIndexWell1][0] = elapsedTimeTemporary;
      well1Data[nextIndexWell1][1] = MLXObjectTemporary;
      well1Data[nextIndexWell1][2] = well1RFUTemporary;
      nextIndexWell1++;
    }
  }
  if (ODRV_well == 2 && amplificationStatus == 3) {
    well2RFUTemporary = fluorTemporary;
    float lastWell2;
    if (nextIndexWell2 > 0) {lastWell2 = well2Data[nextIndexWell2-1][2];}
    else {lastWell2 = well2RFUTemporary;}
    // 0.5 here is resist large changes in fluorescence (unrealistic)
    if (nextIndexWell2 < MAX_DATA_POINTS and abs(well2RFUTemporary - lastWell2) < 0.5) {
      well2Data[nextIndexWell2][0] = elapsedTimeTemporary;
      well2Data[nextIndexWell2][1] = MLXObjectTemporary;
      well2Data[nextIndexWell2][2] = well2RFUTemporary;
      nextIndexWell2++;
    }
  }
  // Store all temperature data
  if (nextIndexTemperature < MAX_DATA_POINTS) {
    temperatureData[nextIndexTemperature][0] = elapsedTimeTemporary;
    temperatureData[nextIndexTemperature][1] = MLXObjectTemporary;
    temperatureData[nextIndexTemperature][2] = fluorTemporary;
    nextIndexTemperature++;
  }
  // Trim the arrays by removing every other data point if exceed MAX_DATA_POINTS
  nextIndexTemperature = trimArray(temperatureData, nextIndexTemperature);
  nextIndexWell1 = trimArray(well1Data, nextIndexWell1);
  nextIndexWell2 = trimArray(well2Data, nextIndexWell2);
}
/// @brief Trim an array if it exceeds the max by removing every other data point
/// @param data Input array
/// @param dataSize The MAX data size for the array
/// @return Return the new size of the array. If trimmed then will be half
int trimArray(float data[][3], int dataSize) {
  int dataCount = dataSize;
  // check if we've reached the maximum number of data points
  if (dataCount == MAX_DATA_POINTS) {
    for (int i = 1; i < MAX_DATA_POINTS; i += 2) {
      for (int j = 0; j < 3; j++) {
        data[i-1][j] = data[i][j];
      }
    }
    dataCount = MAX_DATA_POINTS / 2;
  }
  return dataCount;
}
/// @brief Graph an array of type Time, Temp, Fluor
/// @param data Input data array [][3] Time, Temp, Fluor
/// @param dataSize Number of data points that have been added to the array
/// @param title Title of the graph
/// @param yIndex Refers to the index of the value that is being printed (1=Temp. 2=Fluor)
void graphArray(float data[][3], int dataSize, String title, int yIndex) {
  display.clearDisplay();
  display.setCursor(0, 0);

  // Set up plot area
  const int PLOT_X_START = 15;
  const int PLOT_X_END = SCREEN_WIDTH - 1;
  const int PLOT_Y_START = 5;
  const int PLOT_Y_END = SCREEN_HEIGHT - 20;
  const int PLOT_WIDTH = PLOT_X_END - PLOT_X_START;
  const int PLOT_HEIGHT = PLOT_Y_END - PLOT_Y_START;

  // Determine minimum and maximum values for x, y1, and y2 coordinates
  float xMin = data[0][0];
  float xMax = data[0][0];
  float y1Min = data[0][yIndex];
  float y1Max = data[0][yIndex];

  for (int i = 0; i < dataSize; i++) {
    float x = data[i][0];
    float y1 = data[i][yIndex];

    // Update minimum and maximum values for x and y coordinates
    xMin = min(xMin, x);
    xMax = max(xMax, x);
    y1Min = min(y1Min, y1);
    y1Max = max(y1Max, y1);
  }

  // Check if y1Max is greater than setPointSample
  if (yIndex == 1 and y1Max > setPointSample) {
    // Map the set point to the plot area
    int py = map(setPointSample, y1Min, y1Max, PLOT_Y_END, PLOT_Y_START);
    // Draw a straight line at the set point
    display.drawLine(PLOT_X_START, py, PLOT_X_END, py, WHITE);
  }
  
  if (yIndex == 2) {y1Min = y1Min*100; y1Max = y1Max*100;} // the values should be between 0-1. So this will turn 0.1 into 10 and 0.6 into 60
  // Map x and y coordinates to the plot area for each plot
  for (int i = 0; i < dataSize; i++) {
    float x = data[i][0];
    float y1 = data[i][yIndex];
    if (yIndex == 2) {y1 = y1*100;}
    int px = map(x, xMin, xMax, PLOT_X_START, PLOT_X_END);
    int py1 = map(y1, y1Min, y1Max, PLOT_Y_END, PLOT_Y_START);
    display.drawPixel(px, py1, WHITE);
  }

  // Draw plot frames
  display.drawRect(PLOT_X_START, PLOT_Y_START-5, PLOT_WIDTH, PLOT_HEIGHT+10, WHITE);

  // Add title to the graph
  display.setTextSize(1);
  display.setTextColor(WHITE);
  display.setCursor(20, SCREEN_HEIGHT-13);
  display.print(title+": "+statusIndicator);

  
  //display.setCursor(0, PLOT_Y_END-10);
  display.setCursor(0, SCREEN_HEIGHT-25);
  display.print((int) y1Min);
  display.setCursor(0, 0);
  display.print((int) y1Max);
  String timeMinutes;
  if (xMax < 60000) {
    timeMinutes = String(int(xMax/1000.0))+"s";
  }
  else {
    timeMinutes = String(int(xMax/1000.0/60.0))+"m";
  }
  int x, y;
  uint16_t w, h;
  display.getTextBounds(timeMinutes, 0, 0, &x, &y, &w, &h);
  int textWidth = w;
  int xRight = display.width() - textWidth;
  display.setCursor(xRight, SCREEN_HEIGHT-13);
  display.print(timeMinutes);
  display.display();
  //printArray(data, 100,3);
}
/// @brief Displays all of the graphical screens. This will display the stats for 4, then each of the wells (if fluor) or the temp
void displayAllScreens() {
  const int SCREEN_COUNT = 8;
  // Update the screen
  currentScreen = (currentScreen % SCREEN_COUNT) + 1;
  if (currentScreen <=4) {}
  if (!dispGraphs) {
    displayOLED();
  }
  else if (amplificationStatus == 2) {
    switch (currentScreen) {
      case 1: case 2: case 3: case 4: case 5: case 6:
        displayOLED();
        break;
      case 7:
        graphArray(well1Data, nextIndexWell1, "Well 1", 2);
        break;
      case 8:
        graphArray(well2Data, nextIndexWell2, "Well 2", 2);
        break;
  }
  }
  else {
    switch (currentScreen) {
      case 1: case 2: case 3: case 4: case 5: case 6:
        displayOLED();
        break;
      case 7:
        graphArray(temperatureData, nextIndexTemperature, "Temp", 1);
        break;
      case 8:
        graphArray(temperatureData, nextIndexTemperature, "Fluor", 2);
        break;
  }
  }
  // Reset the timer
  lastUpdateScreen = current;
}
/// @brief Allows for printing of an array [][3] to the Serial monitor for troubleshooting
/// @param data Array of 3 columns to be printed
/// @param rows Number of rows
/// @param cols Number of columns
void printArray(float data[][3], int rows, int cols) {
  for (int i = 0; i < rows; i++) {
    for (int j = 0; j < cols; j++) {
      Serial.print(data[i][j]);
      Serial.print("\t");
    }
    Serial.println();
  }
}

// Device functions
/// @brief Checks if the AS7341 sensor IR reading is above 800 to see if the device is open. Using IR since with LED signal < 50
void lidIsOpen() {
  IRSignal = readings[11];
  //Serial.println(IRSignal);
  if (IRSignal > IRSignalMin) {
    lidOpen = true;
  }
  else {
    lidOpen = false;
  }
  
}
/// @brief This function will check to see if the amplification reaction that we feed it is positive based on Bob's algorithm
/// @param arr The array that will be generated for each well with columns: Time, Temp, Fluorescence
/// @param i The index of the next value that will be added to the matrix
/// @param rollingAvg The value of the rolling average (the last 60 seconds)
/// @param rollingAvgLong The value of the long rolling average (based on parameters, 60 s 360 s ago)
/// @param positiveWell Indicator for whether the well is positive or not. 0 (negative), 1 (interim), 2 (call)
/// @param flag This flags a positive value but not checked if it has been positive long term
/// @param startTimeFlag This value allows us to track when the flag has been raised as positive
/// @param elapsedTimeFlag Elapsed time since first flag, any 0 flag will reset counter
void checkPositive(float arr[][3], int i, float& rollingAvg, float& rollingAvgLong, int& positiveWell, int& flag, long& startTimeFlag, long& elapsedTimeFlag) {
    i = i-1; // This indicated the next index (we need to see the last one)
    if ((arr[i][0] - arr[0][0]) < (-1.0 * window)) {
        // Not enough data points to calculate a rolling average yet
        rollingAvg = 0;
    } else {
        float result[i][2];
        int count = 0;
        for (int j = 0; j <= i; j++) {
            if (arr[j][0] - arr[i][0] >= window && arr[j][0] - arr[i][0] <= 0) {
                result[count][0] = arr[j][0];
                result[count][1] = arr[j][2];
                count++;
            }
        }
        float sum = 0.0;
        for (int k = 0; k < count; k++) {
            sum += result[k][1];
        }
        rollingAvg = sum / count;
    }
    
    if ((arr[i][0] - arr[0][0]) < (-1 * window_long_start)) {
        // Not enough data points to calculate a rolling average yet
        rollingAvgLong = 0;
    } else {
        float result[i][2];
        int count = 0;
        for (int j = 0; j <= i; j++) {
            if (arr[j][0] - arr[i][0] >= window_long_start && arr[j][0] - arr[i][0] <= window_long_end) {
                result[count][0] = arr[j][0];
                result[count][1] = arr[j][2];
                count++;
            }
        }
        float sum = 0.0;
        for (int k = 0; k < count; k++) {
            sum += result[k][1];
        }
        rollingAvgLong = sum / count;

        if (positiveWell == 2) {
            // The well is positive already and don't have to check
        }
        else if (rollingAvg > rollingAvgLong*multiplier) {
            int priorFlag = flag;
            positiveWell = 1;
            flag = 1;
            if (priorFlag == 0) {
                startTimeFlag = arr[i][0];
            }
            else if (priorFlag == 1) {
                elapsedTimeFlag = arr[i][0] - startTimeFlag;
                if (elapsedTimeFlag >= timePositive) {
                    positiveWell = 2;
                }
            }
        }
        else {
            positiveWell = 0;
            flag = 0;
        }
    }
}
/// @brief Check to see if the reaction has reached the setpoint
/// @param temp input temperature
/// @param setpoint setpoints
/// @param amplificationStatus Amplification status
void reachTempAmp(float temp, float setpoint, int& amplificationStatus) {
  if (abs(temp-setpoint) < 0.2) {
    amplificationStatus = 3;
  }
  else {
    amplificationStatus = 2;
  }
}

/// @brief Error handling helpers for setting, clearing, and checking errors
/// @param error 
void setError(uint16_t error) {
  ErrorStatus |= error;   // Set (turn ON) a bit
}
void clearError(uint16_t error) {
  ErrorStatus &= ~error;  // Clear (turn OFF) a bit
}
bool hasError(uint16_t error) {
  return (ErrorStatus & error);  // Check if bit is ON
}

/**
 * @brief Check for heating and motor errors.
 *
 * Errors are only checked if amplificationStatus == 2.
 * - Heating error: MLXObjectTemp drops below 35 °C for >1 minute,
 *   but only after it has first exceeded 35 °C at least once.
 * - Motor error: ODRV_pos remains constant for >1 minute.
 *
 * @param amplificationStatus Current amplification status (must be 2 to check).
 * @param MLXObjectTemp Current object temperature from MLX sensor (°C).
 * @param ODRV_pos Current motor position.
 */
void checkErrors(int amplificationStatus, float MLXObjectTemp, float ODRV_pos) {
  if (amplificationStatus != 2 and amplificationStatus != 3) {
    // Reset timers if not in checking state
    heatingBelowStart = 0;
    motorStillStart = 0;
    return;
  }

  unsigned long now = millis();

  // ---- Heating dropout check ----
  if (MLXObjectTemp > HEATING_THRESHOLD) {
    heatingEverAbove = true;   // System warmed up at least once
    heatingBelowStart = 0;     // Reset dropout timer
    clearError(ERROR_HEATING_DROP);  // Auto-clear when recovered
  } else if (heatingEverAbove) {
    if (heatingBelowStart == 0) {
      heatingBelowStart = now;  // Start timing below threshold
    } else if (now - heatingBelowStart > ERROR_DELAY) {
      setError(ERROR_HEATING_DROP);
    }
  }

  // ---- Motor stall check ----
  if (ODRV_pos != lastMotorPos) {
    lastMotorPos = ODRV_pos;
    motorStillStart = 0;       // Reset stall timer
    clearError(ERROR_NO_ROTATION);  // Auto-clear when movement resumes
  } else {
    if (motorStillStart == 0) {
      motorStillStart = now;   // Start timing still position
    } else if (now - motorStillStart > ERROR_DELAY) {
      setError(ERROR_NO_ROTATION);
    }
  }
}

/**
 * @brief Prints the contents of a uint16_t array to the Serial monitor.
 *
 * This function iterates through the provided array and prints each element
 * separated by a tab character (`\t`). No newline is printed at the end,
 * allowing you to control line breaks externally.
 *
 * @param readings  Pointer to the uint16_t array to print.
 * @param size      Number of elements in the array.
 *
 * @note This function uses Serial.print(), so ensure Serial.begin() has been called.
 *       To end the line after printing, call Serial.println() after this function.
 */
void printReadings(uint16_t readings[], int size) {
  for (int i = 0; i < size; i++) {
    Serial.print(readings[i]);
    if (i < size - 1) Serial.print(","); // comma-separated
  }
}
