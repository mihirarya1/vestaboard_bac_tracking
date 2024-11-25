from globals import opt_out, username_max_len

welcome_message = (
    "🎃 Welcome to our BAC Awareness Activity at our Halloween Party🎃\n\n"
    "This interactive experience helps you learn about alcohol consumption responsibly. "
    f"To opt out at any time, send the text message {opt_out}."
)

username_prompt = f"👤 Choose a username\n\nPlease keep it alphabetical and {username_max_len} characters or less."

opt_out_confirmation = (
    "You have been successfully removed from the event.\n\nAll your data has been deleted. "
    "Feel free to rejoin if you'd like. Stay safe!"
)

opt_out_invalid = (
    "It seems you are not registered in the event, so there's nothing to remove."
)

username_error = f"❌ Invalid username.\n\nPlease ensure it is alphabetical and no longer than {username_max_len} characters."
username_success = "Your username has been successfully registered."

general_error = "⚠️ An unexpected error occurred. Please try again."

invalid_command = "❌ Invalid command. Please try again."

wrong_password = " 🔒 Invalid password. Please try again."

onboarding_success = (
    "You're all set!\n\nFurther instructions will follow as we begin. "
    "Thank you for participating in this responsible drinking awareness event."
)

terms = """Disclaimer:

This event is for educational purposes only. BAC (Blood Alcohol Content) measurements may not be fully accurate.

Your safety is our priority. Always consume alcohol responsibly and in moderation. Never drive after consuming alcohol.

By continuing, you agree to these terms. Please respond with a number:

1: I understand and agree
2: I do not agree
"""

wait_to_blow = "The breathalyzer is currently in use. Please text 'blow' again once the device becomes available."

your_turn_message = (
    "It's your turn! Head to the testing area and follow the instructions to complete your BAC test."
)

start_prompt = "The event is starting! Check your phones for instructions."

game_instruction_msg = (
    "🍷 Welcome to the BAC Awareness Event 🍷\n\n"
    "We’ve connected a breathalyzer to the display board to provide insights on alcohol consumption.\n\n"
    "Text 'blow' to start a breathalyzer test. Your results will be displayed and shared responsibly.\n\n"
    "Remember, this is not a competition—our goal is education and awareness. Drink responsibly!"
)

accurate_results = (
    "For the most accurate results, please wait at least 15 minutes after your last drink."
)

broadcast_success = "ADMIN: Your broadcast was successful."

blow_instructions = (
    "To complete your BAC test:\n\n"
    "1. Turn on the device. Look for the blue light. 💙\n\n"
    "2. Wait for 15 seconds.\n\n"
    "3. Blow steadily into the device for 10 seconds."
)

blow_now = "📣 It's time to blow! Follow the instructions provided. 📣"

blow_complete = "Processing your results. Please wait a moment."

blow_results = "Your BAC reading is: {}"

blow_retry = (
    "Something went wrong. Let's restart the test process and try again."
)

blow_failure = (
    "We encountered an issue with the platform. Please try again later."
)

hi_superman = (
    "You’ve achieved the highest BAC reading so far :(\n\n"
    "Remember, higher BAC levels come with risks. Consider slowing down and hydrating. "
    "Take care of yourself and others."
)

super_gone = (
    "Your BAC is thankfully no longer the highest  Check the leaderboard for updates.\n\n"
    "Remember, this event is about awareness, not competition!"
)

supers_are_off = "Leaderboard tracking has been paused by the administrators."

fake_super = "You don’t have leaderboard privileges. Stay focused on responsible drinking."

game_end_user_message = (
    "The event has ended. Thank you for participating in this BAC Awareness Event. 🎃"
)

