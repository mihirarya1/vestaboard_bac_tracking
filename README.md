### Overview

The **Breathalyzer Project** is a Python-based application designed to integrate with BACtrack Breathalyzer devices, allowing users to measure their Blood Alcohol Concentration (BAC) and receive personalized feedback based on their test results. This project takes a responsible, advisorial approach to drinking habits, providing users with guidance regarding their BAC levels.

Unlike traditional party games, this system focuses on health and safety by advising users to stop drinking if their BAC exceeds safe limits or offering neutral, factual information about their drinking behavior. The game is meant to be used at a small social event like a party or get-together, where the host has at a minimum a BACtrack breathalyzer. 

The application integrates with hardware to automate BAC testing, providing real-time results and feedback through a user-friendly interface, including a **Vestaboard** display.

---

### Architecture

![](images/Vestaboard_Architecture.png?raw=true)

1. **User Onboarding**: The user onboards to the game by sending a provided password to a given number and accepting terms and conditions. Message sending/receiving facilitation between phone number and Python Application is done by **Twilio**. Once onboarded and if the breathalyzer is not being used, the user can initiate a test.

2. **BeagleBone Green IoT Integration**: The Python application running on a **BeagleBone Green IoT 'mini-computer'** notifies the breathalyzer to start warming up and receives a response from the user once the device is ready. The BeagleBone Green runs on an **ARMv7 Cortex-A8 processor**, with **512MB RAM** and **4GB Flash**, making the device computationally constrained. 

3. **User Test Initiation**: The Python application sends a text message to the user to begin blowing on the breathalyzer. The user receives a message and starts blowing. Upon hearing a click from the device, they know they can stop blowing and wait for the test results.

4. **Test Result Processing**: The Python application receives results from the breathalyzer and sends them to **Google Gemini** language model to generate an informative or warning message related to the user's BAC level.

5. **Display Message on Vestaboard**: The Python application receives a message from the Gemini model and sends a display request to the **Vestaboard UI**, showing the message.

---

### Directory Structure

Note that the entire project utilizes **'poetry'** rather than **'pip'** for project dependency and virtual environment management. Additionally, a **Makefile** is used to start the application.

1. **party_client/bactrack_stats.py**  
   Handles pulling a histogram of all BACtrack users' usage on a given day from live BACtrack APIs.

2. **party_client/breathalyzer_client.py**  
   Manages all interactions with the breathalyzer. Includes handling device attributes such as battery level, warmup following test initiation, and returning test results. Communication is done via Bluetooth (BLE) protocol.

3. **party_client/flask_server.py**  
   Entry point for the Python application, starting the Flask server which allows users to send requests and receive responses. **Ngrok** reverse proxy is used for forwarding requests from Twilio to the Python application.

4. **party_client/genai_client.py**  
   Handles integration with **Google Gemini** hosted models to fetch a fun/informative fact based on the user's BAC test and their test history.

5. **party_client/logic.py**  
   Contains the central orchestrator behind user text messages, managing onboarding, T&C agreement, test initiation, leaderboard display, and error handling. Admins can broadcast messages or end the game.

6. **party_client/user.py**  
   Manages the game state, including all onboarded users, their status, and BAC test history. The state is persisted in a JSON file, which is reloaded if the application crashes.

7. **party_client/vestaboard_client.py**  
   Manages the semantics of writing data to the **Vestaboard UI display**, using the **VBML API** to format messages into byte strings and then using **Vestaboard Local Read APIs** to update the board.

---

### References

1. [Vestaboard UI Overview](https://www.vestaboard.com/)  
   Overview of the Vestaboard display UI.

2. [Vestaboard Read/Write API](https://docs.vestaboard.com/docs/read-write-api/introduction)  
   Vestaboard development Read/Write APIs used to push changes to the UI board.

3. [BACtrack Mobile Breathalyzer](https://www.bactrack.com/products/bactrack-mobile-smartphone-breathalyzer?srsltid=AfmBOoqe8dASnrp5PrzMlx8phhVCQHJWeKD_RdcxZNXygIoKSw4kIt-N)  
   BAC monitoring breathalyzer device.

4. [BACtrack SDK Documentation](https://developer.bactrack.com/breathalyzer_sdk/documentation)  
   Breathalyzer Mobile App SDK, used for developing custom communication implementations via Bluetooth.

5. [Twilio SMS API](https://www.twilio.com/en-us/messaging/channels/sms)  
   Twilio products and APIs used for facilitating requests/responses between a mobile number and Python application.

6. [BeagleBone Green Wiki](https://wiki.seeedstudio.com/BeagleBone_Green/)  
   BeagleBone Green IoT device, where the Python application runs.
