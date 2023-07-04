#include "Arduino.h"
#include "SoftwareSerial.h"
#include "DFRobotDFPlayerMini.h"

//Pulsadores
const int s[] = {9,8,7,6,5,4}; //sensores hal y boton de pausa (no implementado)
int state[] = {0,0,0,0,0};
int last[] = {0,0,0,0,0};
int lastRaised = -1;
int lastPlayed = -1;
int ready = 5;

SoftwareSerial mySoftwareSerial(10, 11); // RX, TX
DFRobotDFPlayerMini myDFPlayer;
void printDetail(uint8_t type, int value);

void setup()
{
  mySoftwareSerial.begin(9600);
  Serial.begin(115200);

  Serial.println();
  Serial.println(F("DFRobot DFPlayer Mini Demo"));
  Serial.println(F("Initializing DFPlayer ... (May take 3~5 seconds)"));

  delay(5000);

  while (!myDFPlayer.begin(mySoftwareSerial)) {  //Use softwareSerial to communicate with mp3.
    Serial.println(F("Unable to begin:"));
    Serial.println(F("1.Please re-check the speaker connection!"));
    Serial.println(F("2.Please insert the SD card!"));
  }
  Serial.println(F("DFPlayer Mini online."));

  myDFPlayer.setTimeOut(500); //Set serial communictaion time out 500ms

  //----Set volume----
  myDFPlayer.volume(20);  //Set volume value (0~30).
  myDFPlayer.volumeUp(); //Volume Up
  myDFPlayer.volumeDown(); //Volume Down

  //----Set different EQ----
  myDFPlayer.EQ(DFPLAYER_EQ_NORMAL);

  //----Set device we use SD as default----
  myDFPlayer.outputDevice(DFPLAYER_DEVICE_SD);

  for(int i = 0 ; i < 6 ; i++){
    pinMode(s[i], INPUT_PULLUP);
  }

  ready = verify();
  while(ready!=-1){
    Serial.print("To start, align correctly object #");
    Serial.println(ready+1);
    ready = verify();
  }; //Cant start the program until all the pieces lay on the box
}


void loop()
{
  // Loop that detects if an object has been recently raised that has not been yet registered.
  for(int i = 0 ; i < 5 ; i++){
    state[i] = !digitalRead(s[i]);
    if(state[i] != last[i] && state[i]){
      lastRaised = i;
    }
    last[i] = state[i];
  }

  // Condition that plays an audio if a new object has been raised.
  if(state[lastRaised] && lastRaised != -1){
    myDFPlayer.play(lastRaised+1);
    Serial.print("Playing audio #");
    Serial.println(lastRaised+1);
    lastPlayed = lastRaised;
    lastRaised = -1;
    delay(500);
  }

  // Condition that pauses the audio if the object raised last is back on the box.
  if(lastPlayed != -1 && !state[lastPlayed]){
    Serial.print("Pausing audio #");
    Serial.println(lastPlayed+1);
    myDFPlayer.pause();
    lastPlayed = -1;
  }
}

// Function that verifies that all the objects are on the box;
int verify(){
  for(int i = 0 ; i < 5 ; i++){
    if(!digitalRead(s[i]))
      return i;
  }
  return -1;
}
