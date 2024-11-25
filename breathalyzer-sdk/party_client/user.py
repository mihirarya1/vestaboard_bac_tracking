import json
import logging
import os
import time

from globals import game_state
from sortedcontainers import SortedDict
from datetime import datetime


onboarding_flow = ["new_user", "register_user", "agree_to_terms", "gameplay"]


class User:
    def __init__(
        self,
        number,
        username=None,
        next_step="register_user",
        agree_to_terms=False,
        onboarded=False,
    ):
        self.number = number
        self.username = username
        self.next_step = next_step
        self.agreed_to_terms = agree_to_terms
        self.onboarded = onboarded
        self.test_history = SortedDict()

    def to_dict(self):
        return {
            "number": self.number,
            "username": self.username,
            "next_step": self.next_step,
            "agreed_to_terms": self.agreed_to_terms,
            "onboarded": self.onboarded,
            "test_history": self.test_history,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            number=data["number"],
            username=data.get("username"),
            next_step=data.get("next_step", "register_user"),
            agree_to_terms=data.get("agreed_to_terms", False),
            onboarded=data.get("onboarded", False),
        )


def persist_users_data(users):
    backup_file = os.path.join(os.getcwd(), game_state["backup_file_name"])

    if not os.path.isdir(os.getcwd()):
        logging.info(
            f"Backup file directory '{os.getcwd()}' not found. Unable to persist user state data."
        )
        return ""

    logging.info("In persist_users_data")

    for i in range(len(users["leaders"])):
        if isinstance(users["leaders"][i][2], datetime):
            users["leaders"][i][2] = users["leaders"][i][2].isoformat()

    serializable_data = {
        key: user if key == "leaders" else user.to_dict() for key, user in users.items()
    }
    with open(backup_file, "w") as json_file:
        logging.info("Writing users dictionary to json file.")
        json.dump(serializable_data, json_file, indent=4)
    return ""


def restore_user_states():
    backup_file = os.path.join(os.getcwd(), game_state["backup_file_name"])

    if not os.path.isfile(backup_file):
        logging.info(
            f"Backup file '{backup_file}' not found. Defaulting to empty users list."
        )
        return {"leaders": []}

    modified_time = os.path.getmtime(backup_file)
    # Check if the file was modified within the allowed threshold (in hours)
    if (time.time() - modified_time) / 3600 <= game_state["backup_edit_threshold"]:
        try:
            with open(backup_file, "r") as json_file:
                loaded_data = json.load(json_file)
            logging.info(f"Restoring state of Users in game from file: {backup_file}")
            restored_users = {
                key: value if key == "leaders" else User.from_dict(value)
                for key, value in loaded_data.items()
            }

            for i in range(len(restored_users["leaders"])):
                if isinstance(restored_users["leaders"][i][2], str):
                    restored_users["leaders"][i][2] = datetime.fromisoformat(
                        restored_users["leaders"][i][2]
                    )
            return restored_users
        except json.JSONDecodeError as e:
            logging.info(
                f"Error decoding JSON backup: {e}. Defaulting to empty users list."
            )
        except Exception as e:
            logging.info(
                f"Unexpected error occurred while reading the backup: {e}. Defaulting to empty users list."
            )
    else:
        logging.info(
            f"Backup file '{backup_file}' is older than the threshold. Defaulting to empty users list."
        )
    return {"leaders": []}
