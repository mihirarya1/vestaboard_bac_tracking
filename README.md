### Overview:

    The Breathalyzer Project is a Python-based application designed to integrate with BACtrack Breathalyzer devices, 
    allowing users to measure their Blood Alcohol Concentration (BAC) and receive personalized feedback based on their 
    test results. This project takes a responsible, advisorial approach to drinking habits, providing users with guidance 
    regarding their BAC levels.

    Unlike traditional party games, this system focuses on health and safety by advising users to stop drinking if their 
    BAC exceeds safe limits or offering neutral, factual information about their drinking behavior. The application integrates 
    with hardware to automate BAC testing, providing real-time results and feedback through a user-friendly interface, 
    including a Vestaboard display

### Architecture


![](images/Vestaboard_Architecture.png?raw=true)

    

### Directory Structure:
    
    Note that the entire project utilizes 'poetry' rather than 'pip' for project dependency and virtual envrionment management.
    Additionally a Makefile is used to start the application.

    1. party_client/bactrack_stats.py 
       Class to handle pulling a histogram of all BacTrack user's usage on the given day, from live BacTrack APIs.

    2. party_client/breathalyzer_client.py
       Handles all interactions with the breathalyzer. This includes handling device attributes such as battery level, 
       device warmup following user initation of a test, user test semantics, and crunching and returning the user's test
       results. Communication between the Python applciation and the Breathalyzer device is done using Bluetooth (BLE) protocol.

    3. party_client/flask_server.py
       Entry point for the Python application, which actually starts the Flask server which allows a number to send requests
       and receives responses from our game. An ngrok reverse proxy is used, to facilitate forwarding of requests from Twilio
       to our Python application. Startup of this server, is handled by Makefile.

    4. party_client/genai_client.py
       GenAI integration with Google Gemini hosted models, to fetch a fun/informative fact on user, following a user's
       BAC test, and considering their test history.

    5. party_client/logic.py
       Contains the central orchestrator/logic behind user text messages sent to the Python Application. Items related to 
       onboarding a new user to the platform, ensuring they agree to T&C, and starting and viewing test results are handled, 
       in addition to vestaboard leaderboard and display management, and complex error handling.

    6. party_client/user.py
       File which handles the game state, consisting of all the users onboarded to the game, along with their status in the 
       game onboarding flow, and their BAC test history. This state is constantly persisted to a JSON backup file, which
       is automatically retrieved should the application be restarted should it crash.

    7. party_client/vestaboard_client.py
       Class which handles all semantics of writing data to the Vestabord UI display. Handles connection to the Vestaboard UI 
       display, and utilizes a Vestabord provided VBML API to format a message into a Vestabord friendly byte string, after
       which Vestabord Local Read APIs are used to write to the board.

### References: 

1. [Vestaboard UI Overview](https://www.vestaboard.com/)  
   Overview of the Vestaboard display UI.

2. [Vestaboard Read/Write API](https://docs.vestaboard.com/docs/read-write-api/introduction)  
   Vestaboard development Read/Write APIs used to push changes to the UI board.

3. [BACtrack Mobile Breathalyzer](https://www.bactrack.com/products/bactrack-mobile-smartphone-breathalyzer?srsltid=AfmBOoqe8dASnrp5PrzMlx8phhVCQHJWeKD_RdcxZNXygIoKSw4kIt-N)  
   BAC monitoring breathalyzer device.

4. [BACtrack SDK Documentation](https://developer.bactrack.com/breathalyzer_sdk/documentation)  
   Breathalyzer Mobile App SDK, which was used to develop a custom implementation for communicating with the Breathalyzer via Bluetooth.

5. [Twilio SMS API](https://www.twilio.com/en-us/messaging/channels/sms)  
   Twilio products and APIs, used to facilitate requests/responses between a mobile number and Python application.

6. [BeagleBone Green Wiki](https://wiki.seeedstudio.com/BeagleBone_Green/)  
   BeagleBone Green IoT device, which the Python application runs on.