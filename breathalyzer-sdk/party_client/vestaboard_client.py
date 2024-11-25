import ast
import subprocess
from socket import socket

import requests

from pydantic import BaseModel, Field
from typing import List, Optional

from globals import vestaboard_metadata
import logging


class AbsolutePosition(BaseModel):
    x: int = Field(default=0)
    y: int = Field(default=0)


class SubMessageStyle(BaseModel):
    height: Optional[int] = Field(
        default=6, ge=1, le=6
    )  # Height must be between 1 and 6
    width: Optional[int] = Field(
        default=22, ge=1, le=22
    )  # Width must be between 1 and 22
    justify: Optional[str] = Field(
        default="left", pattern="^(left|right|center|justified)$"
    )  # Justification options
    align: Optional[str] = Field(
        default="top", pattern="^(top|bottom|center|justified)$"
    )  # Alignment options
    absolutePosition: Optional[AbsolutePosition] = Field(default=None)


class SubMessage(BaseModel):
    template: str
    style: SubMessageStyle


class Message(BaseModel):
    components: List[SubMessage]  # List of components


class Vestaboard:
    def __init__(
        self,
        x_api_key,
        ip_address,
        height=vestaboard_metadata["default_height"],
        width=vestaboard_metadata["default_width"],
        min_char_code=vestaboard_metadata["default_min_char_code"],
        max_char_code=vestaboard_metadata["default_max_char_code"],
        ip_address_alternate=None,
    ):
        self.x_api_key = x_api_key
        self.base_headers = {"X-Vestaboard-Local-Api-Key": self.x_api_key}
        self.url = self.establish_connection(ip_address, ip_address_alternate)
        self.height = height
        self.width = width
        self.min_char_code = min_char_code
        self.max_char_code = max_char_code

    def validate_message(self, message: bytes):
        if (
            not message
            or not isinstance(message, list)
            or len(message) != self.height
            or not message[0]
            or not isinstance(message[0], list)
            or len(message[0]) != self.width
        ):
            logging.error(
                f"Invalid message to be sent to vestaboard. Expecting a {self.height}x{self.width} list of lists"
            )
            return False

        for r in range(self.height):
            for c in range(self.width):
                if (
                    not isinstance(message[r][c], int)
                    or message[r][c] < self.min_char_code
                    or message[r][c] > self.max_char_code
                ):
                    logging.error(
                        f"Invalid character submitted in message display request. Expecting a value between {self.min_char_code} and {self.max_char_code}"
                    )
                    return False

        return True

    def send_msg(self, message: bytes):
        if self.url:
            headers = self.base_headers | {"Content-Type": "application/json"}
            if self.validate_message(message):
                logging.info("Attempting write to Vestaboard")
                response = requests.post(
                    url=self.url, data=str(message), headers=headers
                )
                logging.info(f"Wrote to Vestaboard with Status: {response.status_code}")
                return response.status_code, response.text

    def read_msg(self):
        if self.url:
            logging.info("Attempting read from Vestaboard")
            response = requests.get(url=self.url, headers=self.base_headers)
            logging.info(f"Read from Vestaboard with Status: {response.status_code}")
            return response.status_code, response.text

    def establish_connection(self, ip_address, ip_address_alternate):
        url = "http://{}:7000/local-api/message"
        if self.check_connection(ip_address):
            url = url.format(ip_address)
        elif self.check_connection(ip_address_alternate):
            url = url.format(ip_address_alternate)
        else:
            url = ""
            logging.error("All attempts to connect to Vestaboard unsuccessful")
        return url

    def check_connection(self, ip_address, ping_timeout=2):
        if not ip_address:
            return False
        try:
            logging.info(f"Attempting Vestaboard ping check to {ip_address}")
            result = subprocess.run(
                [
                    "ping",
                    "-c",
                    "1",
                    ip_address,
                ],  # Use "-c 1" to send 1 ping request (Linux/Mac)
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=ping_timeout,
            )
            if result.returncode == 0:
                logging.info(f"Ping to Vestaboard {ip_address} successful")
                return True
            else:
                logging.warning(
                    f"Ping to Vestaboard {ip_address} failed: {result.stderr.strip()}"
                )
                return False
        except Exception as e:
            logging.warning(
                f"Uncaught error while pinging Vestabord {ip_address}host: {e}"
            )
            return False


def convert_vbml_to_array(vbml_message, url=vestaboard_metadata["vbml_url"]):
    headers = {"Content-Type": "application/json"}
    logging.info(
        f"Calling VBML to Array Endpoint at {url}, with message {vbml_message}"
    )
    response = requests.post(url=url, headers=headers, data=vbml_message.json())
    logging.info(
        f"Received VBML to Array Endpoint response with Status: {response.status_code} and Payload: {response.text}"
    )

    converted_response_text = ""
    try:
        converted_response_text = ast.literal_eval(response.text)
    except:
        logging.error(
            "Error converting message response from VBML API to list of lists."
        )
    return response.status_code, converted_response_text
