import os

twilio_credentials = {
    "account_sid": "<TWILIO_ACCOUNT_SID>",
    "auth_token": "<TWILIO_AUTH_TOKEN>",
}

vcard_credentials = {"vcard_sid": "<VCARD_SID>"}

ngrok_credentials = {
    "ngrok_domain": "<NGROK_DOMAIN>",
    "ngrok_auth": "<NGROK_AUTH_TOKEN>",
}

phone_numbers = {
    "backend_number": "<BACKEND_PHONE_NUMBER>",
    "<USER_NAME>": "<PHONE_NUMBER>",
}

admin_info = {"<USER_NAME>": "<PHONE_NUMBER>"}

master_credentials = {"master_password": "<MASTER_PASSWORD>"}

username_max_len = 7

opt_out = "<OPT_OUT_KEYWORD>"

bactrack_metadata = (
    {  # apparently BLE convention for UUID names, is all caps, minor thing
        "BACTRACK_BLE_ADDRESS": "<BACTRACK_BLE_ADDRESS>",
        "BATTERY_LEVEL_CHARACTERISTIC_UUID": "<BATTERY_LEVEL_UUID>",
        "CONNECTION_INITIALIZATION_UUID": "<CONNECTION_INIT_UUID>",
        "START_TEST_UUID": "<START_TEST_UUID>",
        "TEST_RESULTS_LISTENER_UUID": "<TEST_RESULTS_LISTENER_UUID>",
        "test_timeout_duration": 60,
        "connection_timeout_duration": 10,
        "read_notifications_timeout_duration": 4,
        "max_conduct_test_retries": 2,
    }
)

vestaboard_metadata = {
    "x_api_key": "<VESTABOARD_API_KEY>",
    "ip_address_two_four_wifi": "<VESTABOARD_IP_2.4GHZ>",
    "ip_address_five_wifi": "<VESTABOARD_IP_5GHZ>",
    "default_width": 22,
    "default_height": 6,
    "default_min_char_code": 0,
    "default_max_char_code": 71,
    "vbml_url": "<VBML_URL>",
}

game_state = {
    "backup_file_name": "<BACKUP_FILE_NAME>",
    "backup_edit_threshold": 4,
}

bactrack_stats = {
    "histogram_url": "<HISTOGRAM_URL>",
    "histogram_bins": [
        "0.00-0.02",
        "0.02-0.04",
        "0.04-0.06",
        "0.06-0.08",
        "0.08-0.10",
        "0.10-0.12",
        "0.12-0.14",
        "0.14-0.16",
        "0.16-0.18",
        "0.18-0.20",
        "0.20+",
    ],
}

genai_client = {
    "google_api_key": "<GOOGLE_API_KEY>",
    "gemini_15_flash_url": "<GEMINI_FLASH_URL>",
}