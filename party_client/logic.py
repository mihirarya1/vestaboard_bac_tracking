import asyncio
import json
import logging
import os
import queue
import threading
from asyncio import sleep
from datetime import datetime, time
from genai_client import GenAI, user_prompt_template
from tenacity import stop_after_attempt, wait_fixed, retry

from globals import (
    master_credentials,
    phone_numbers,
    twilio_credentials,
    admin_info,
    bactrack_metadata,
    vestaboard_metadata,
)

from user import *
from prompts import *
from twilio.rest import Client
from vestaboard_client import (
    convert_vbml_to_array,
    Message,
    SubMessage,
    SubMessageStyle,
    AbsolutePosition,
    Vestaboard,
)
from breathalyzer_client import BacTrack


def exposed_marker(func):
    func.is_exposed = True  # Attach a custom attribute to the function.
    return func


class Logic:

    def __init__(self):
        self.all_func_names = [  # get list of all function names in class
            name for name, method in Logic.__dict__.items() if callable(method)
        ]

        self.exposed_func_names = [  # get list of all exposed function names in class
            name
            for name, method in Logic.__dict__.items()
            if callable(method) and getattr(method, "is_exposed", False)
        ]

        self.bac_track = BacTrack(
            # the bac track instance should be tied to the Game instance as well, and definitely be lock based access
            device_bluetooth_address=bactrack_metadata["BACTRACK_BLE_ADDRESS"],
        )

        self.vestaboard = Vestaboard(
            x_api_key=vestaboard_metadata["x_api_key"],
            ip_address=vestaboard_metadata["ip_address_two_four_wifi"],
            ip_address_alternate=vestaboard_metadata["ip_address_five_wifi"],
        )

        self.test_lock = threading.Lock()  # Thread-level lock

        self.users = restore_user_states()
        self.admin_info = admin_info
        for username, number in self.admin_info.items():
            self.users[number] = User(
                number=number,
                username=username,
                next_step="gameplay",
                agree_to_terms=True,
                onboarded=True,
            )

        # a list of the top 3 leaders, using a list of lists  [["username": "player1", "score": 150, "timestamp": datetime.now()]],
        self.usernames = {}
        self.genai_client = GenAI()

        self.twilio = Client(
            twilio_credentials["account_sid"], twilio_credentials["auth_token"]
        )

        logging.info(
            f"Standard user runnable functions via message: {self.exposed_func_names}"
        )
        logging.info(
            f"Admin user runnable functions via message: {self.all_func_names}"
        )

        self.unique_usernames = []

        self.superman = None
        self.super_number = None

        # send message to the vestaboard with phone # and password
        self.vesta_starter()

    async def process_message(self, client_number, message):
        # make response all lower case
        message = message.lower().strip()
        is_client_number_active = client_number in self.users

        # user opt out
        if message == opt_out.lower() and is_client_number_active:
            logging.info(
                f"Registered user {client_number} chose to opt-out. Deleting them from users."
            )
            self.users.pop(client_number, None)
            persist_users_data(self.users)
            self.send_msg(client_number, opt_out_confirmation)
            return
        # process new user, checking for password
        if not is_client_number_active:
            logging.info(
                f"Attempting to create new user for unrolled number {client_number}"
            )
            args = [client_number, message]
            responses = self.new_user(args)
            self.send_msg(client_number, responses)
            return

        words = message.split()
        func_name = words[0]
        args = words[1:]

        user_has_func_name_permissions = (
            client_number not in self.admin_info.values()
            and func_name in self.exposed_func_names
        ) or (
            client_number in self.admin_info.values()
            and func_name in self.all_func_names
        )

        # invalid command
        if not user_has_func_name_permissions and self.users[client_number].onboarded:
            self.send_msg(client_number, invalid_command)

        # user onboarding in progress
        if (
            not user_has_func_name_permissions
            and self.users[client_number].onboarded is False
        ):
            func = getattr(self, self.users[client_number].next_step)
            args = [client_number, message, self.bac_track]
            responses = func(args)
            self.send_msg(client_number, responses)
            return

        response = ""
        # user wants to run valid commands
        func = getattr(self, func_name)
        try:
            response = await func(client_number) if func_name == "blow" else func(args)
        except Exception as e:
            self.send_msg(client_number, general_error)
        self.send_msg(client_number, response)
        return

    def broadcast(self, message):
        print("broadcasting")
        for client_number in self.users.keys():
            if client_number != "leaders":
                self.send_msg(client_number, message)

    def start_game(self, args):
        self.broadcast(game_instruction_msg)
        self.broadcast(accurate_results)
        self.send_vesta_message(start_prompt)
        return broadcast_success

    def end_game(self, args):
        self.broadcast(game_instruction_msg)
        return broadcast_success

    def end_game(self, args):
        self.broadcast(game_end_user_message)
        # self.send_vesta_message(game_end_vesta_message)
        return broadcast_success

    def find_phone_by_username(self, username):
        for phone_number, user in self.users.items():
            if user.username == username:
                return phone_number
        return None  # Return None if the username is not found

    def new_user(self, args):

        client_number = args[0]
        password = args[1]

        responses = []

        if password != master_credentials["master_password"]:
            logging.warning(f"Number {client_number} sent INCORRECT password")
            return wrong_password

        responses.append(welcome_message)
        responses.append(username_prompt)

        self.users[client_number] = User(client_number)
        persist_users_data(self.users)
        logging.info(f"Number {client_number} sent correct password")

        return responses

    @exposed_marker
    def register_user(self, args):

        client_number = args[0]
        new_user_name = args[1]

        if (
            len(new_user_name) > username_max_len
            or len(new_user_name) < 0
            or new_user_name.isalnum() is False
            or new_user_name == master_credentials["master_password"]
            or new_user_name in self.unique_usernames  # check for duplicate usernames
        ):
            logging.error(
                f"Received invalid username: {new_user_name} during registration",
                exc_info=True,
            )
            return username_error

        self.users[client_number].username = new_user_name
        logging.info(f"Number {client_number} registered as {new_user_name}")

        self.users[client_number].next_step = "agree_to_terms"
        persist_users_data(self.users)

        return [username_success, terms]

    @exposed_marker
    def agree_to_terms(self, args):

        client_number = args[0]
        response = args[1]

        if response != "1":
            logging.info("User did not consent to T&C, removing them")
            self.users.pop(client_number, None)
            persist_users_data(self.users)
            return opt_out_confirmation

        self.users[client_number].agreed_to_terms = True
        self.users[client_number].onboarded = True
        self.users[client_number].next_step = "gameplay"
        persist_users_data(self.users)

        return onboarding_success

    # def before_blow_retry(self, retry_state): # runs on start of any retry
    #     if retry_state.attempt_number >= 2:
    #         self.send_msg(retry_state.kwargs.get("client_number"), blow_retry)
    #
    # def after_blow_retry(self, retry_state): # runs after final try
    #     if retry_state.attempt_number >= bactrack_metadata["max_conduct_test_retries"]:
    #         self.send_msg(retry_state.kwargs.get("client_number"), blow_failure)  # Send final failure message

    def vesta_starter(self):

        password = master_credentials["master_password"]
        phone_number = phone_numbers["backend_number"]
        formatted_number = f"{phone_number[:2]}-{phone_number[2:5]}-{phone_number[5:8]}-{phone_number[8:]}"
        msg = f"Text {password} to the phone number {formatted_number}"
        self.send_vesta_message(msg)

    def reading_age(self, time_then):
        if isinstance(time_then, str):
            time_then = datetime.fromisoformat(time_then)
        time_now = datetime.now()

        difference_in_minutes = (time_now - time_then).total_seconds() / 60

        # Round to the nearest whole number
        rounded_minutes_ago = round(difference_in_minutes)

        reading_age = min(rounded_minutes_ago, 99)
        return str(reading_age).zfill(2)

    def get_leader(self, pos):
        if pos >= len(self.users["leaders"]):  # there is no silver or bronze
            return ""

        leader_data = self.users["leaders"][pos]
        username = leader_data[0]
        bac_score = leader_data[1]
        reading_time = leader_data[2]

        formatted_username = username.ljust(username_max_len)
        formatted_bac_score = bac_score[1:]
        formatted_reading_age = self.reading_age(reading_time)

        formatted_line = f"{pos+1} {formatted_username}{formatted_bac_score} -{formatted_reading_age}min"
        if formatted_line.endswith("-00min"):
            return formatted_line[:-6] + "recent"

        return formatted_line

    def find_user_index(self, username):
        for index, user in enumerate(self.users["leaders"]):
            if user[0] == username:  # Check if the username matches
                return index
        return -1  # Return -1 if the username is not found

    def update_vesta_leaderboard(self, username, bac_score, time_now):
        # make username padded for vesta formatting
        logging.info("Updating Vestabord leaderboard")
        formatted_username = username.ljust(username_max_len)
        formatted_bac_score = bac_score[1:]

        # current users position
        pos = self.find_user_index(username)
        line_1 = "{64}{68}{64}{68}{64}Leaderboard{64}{68}{64}{68}{64}{68}"
        gold = self.get_leader(0)

        silver = self.get_leader(1)
        bronze = self.get_leader(2)
        line_5 = "{64}{68}{64}{68}{64}{68}{64}{68}{64}{68}{64}{68}{64}{68}{64}{68}{64}{68}{64}{68}{64}{68}"

        if pos == 0:
            line_6 = "You take the gold!"
        elif pos == 1:
            line_6 = "You take the silver!"
        elif pos == 2:
            line_6 = "You take the bronze!"
        else:
            line_5 = (
                "{64}{68}{64}{68}{64}{68}{64}{68}Recent{64}{68}{64}{68}{64}{68}{64}{68}"
            )
            line_6 = f"{pos + 1} {formatted_username}{formatted_bac_score} recent"

        message_to_send = f"{line_1}\n{gold}\n{silver}\n{bronze}\n{line_5}\n{line_6}"
        self.send_vesta_message(message_to_send)

    def update_superman(self, username, client_number):

        gold_data = self.users["leaders"][0]

        if (
            self.superman is None or self.superman != gold_data[0]
        ):  # superman does not exist or has changed
            self.superman = username
            self.super_number = client_number

            self.send_msg(self.super_number, hi_superman)

            usernames_in_game = "Usernames + Scores\n"
            for record in self.users["leaders"]:

                current_user = record[0]
                current_bac = record[1]
                usernames_in_game = (
                    usernames_in_game + "- " + current_user + " " + current_bac + "\n"
                )
        self.send_msg(self.super_number, usernames_in_game)

    @exposed_marker
    def bother(self, args):

        client_number = args[0]
        user_to_bother = args[1]

        if client_number != self.super_number:
            self.send_msg(client_number, fake_super)
            return

        number_to_bother = self.find_phone_by_username(user_to_bother)

        line_1, line_6 = (
            "{64}{68}{64}{68}{64}{68}{64}{68}{64}{68}{64}{68}{64}{68}{64}{68}{64}{68}{64}{68}{64}{68}"
        )

        vesta_msg = (
            f"Hey @{number_to_bother}, slow down and make sure you're drinking responsibly!"
        )

        self.send_vesta_message(f"{line_1}\n{vesta_msg}\n{line_6}")
        self.send_msg(
            f"Hey party goer! You've been drinking a little too much and {self.superman} has noticed. Why don't you slow down and drink some water!"
        )

    def send_vesta_message(self, message):
        status_message = Message(
            components=[
                SubMessage(
                    template=message,
                    style=SubMessageStyle(
                        height=6,
                        width=22,
                        justify="center",
                        align="center",
                        absolutePosition=AbsolutePosition(x=0, y=0),
                    ),
                )
            ]
        )

        response_code, response = convert_vbml_to_array(status_message)
        logging.info("Sending message to VBML API")

        if 200 <= response_code < 300:
            logging.info("Sending message to Vestaboard API")
            response_code, response = self.vestaboard.send_msg(response)
        return ""

    def update_user_vestaboard_data(self, username):
        req = self.genai_client.create_request(
            user_prompt=user_prompt_template.format(
                name=username, bac_history=str(self.users[username])
            )
        )
        response_text, response_code = self.genai_client.call_completions(req)
        self.send_vesta_message(response_text[:80])

    def update_user_leaderboard_data(self, username, new_bac_value, new_time):
        # Check if the user exists and update their data
        logging.info("Updating user leaderboard data")
        for user in self.users["leaders"]:
            if user[0] == username:
                user[1] = new_bac_value  # Update bac_value
                user[2] = new_time  # Update timestamp
                logging.info(
                    f"Updated {username}'s leaderboard data to {new_bac_value} and timestamp {new_time}."
                )
                self.users["leaders"].sort(
                    key=lambda x: x[1], reverse=True
                )  # sort based on descending back score
                persist_users_data(self.users)
                return

        # If the user is not found, you can optionally add them to the list
        self.users["leaders"].append([username, new_bac_value, new_time])
        self.users["leaders"].sort(
            key=lambda x: x[1], reverse=True
        )  # sort based on descending back score

        persist_users_data(self.users)

        logging.info(
            f"Added new user {username} with bac_value {new_bac_value} and timestamp {new_time}."
        )
        return

    @exposed_marker
    async def blow(self, client_number):
        # @retry(stop=stop_after_attempt(bactrack_metadata["max_conduct_test_retries"]), wait=wait_fixed(2),
        #        before=self.before_blow_retry, after=self.after_blow_retry)
        async def conduct_test(**kwargs):
            self.send_msg(client_number, blow_instructions)
            try:
                await self.bac_track.bluetooth_connect()
                reading = await self.bac_track.conduct_test(
                    self.message_callback, client_number
                )
            except Exception as e:
                raise Exception(f"Unhandled error during BAC test: {str(e)}")
            finally:
                await self.bac_track.bluetooth_disconnect()
            # self.post_test_vestaboard_display(client_number)
            username = (self.users[client_number]).username
            time_now = datetime.now()
            self.update_user_leaderboard_data(username, reading, time_now)
            # self.update_user_vestaboard_data(username) # COMMENT OUT
            # sleep(10) # COMMENT OUT
            self.update_vesta_leaderboard(username, reading, time_now)
            # self.update_superman(username, client_number)

        if not self.test_lock.locked():
            with self.test_lock:
                await conduct_test(client_number=client_number)
        else:
            self.send_msg(client_number, wait_to_blow)

    def send_msg(self, client_number, responses):
        if not responses:
            return
        if not isinstance(responses, (str, list)):
            responses = [general_error]
        elif isinstance(responses, str):
            responses = [responses]
        for response in responses:  # multiple responses
            logging.info(
                f"Sending message to {client_number}, with value {str(response)}"
            )
            message = self.twilio.messages.create(
                to=client_number, from_=phone_numbers["backend_number"], body=response
            )
            logging.info(message)
        return

    # @retry(stop=stop_after_attempt(2), wait=wait_fixed(2))
    def message_callback(self, description, countdown, client_number):
        try:
            if description == "WARMING_UP" and countdown == "1":
                self.send_msg(client_number, blow_now)
            elif description == "KEEP_BLOWING" and countdown == "1":
                self.send_msg(client_number, blow_complete)
            elif description == "ATTAINED_RESULTS":
                # self.send_msg(client_number, blow_results.format(countdown)) # countdown here is the results
                current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.users[client_number].test_history[countdown] = current_timestamp
                persist_users_data(self.users)

        except Exception as e:
            logging.error(f"Exception in bac_track listener callback {e}")
            raise Exception(f"Exception in bac_track listener callback {e}")
