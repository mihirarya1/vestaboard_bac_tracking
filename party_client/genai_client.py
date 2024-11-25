import requests
import json
import logging
from globals import genai_client


def request_template(
    user_prompt, system_prompt, temperature=0.7, max_output_tokens=100
):
    return {
        "contents": [
            {"role": "user", "parts": [{"text": user_prompt}]},
            {"role": "model", "parts": [{"text": system_prompt}]},
        ],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_output_tokens,
        },
    }


user_prompt_template = "Person Name: {name}, BAC History at Party: {bac_history}"

system_prompt = """You are a chatbot that provides a neutral, fact-based message for a person based on their BAC (Blood 
Alcohol Concentration). The person has just taken a BAC reading and your message, along with their results, will be 
displayed on a Vestaboard UI. Offer advice if their BAC indicates high levels of consumption, or share a neutral fact 
about drinking habits if their BAC is within a safe range. Your response should be concise and constructive."""


class GenAI:
    def __init__(
        self,
        model_url=genai_client["gemini_15_flash_url"],
        api_key=genai_client["google_api_key"],
    ):
        self.api_key = api_key
        self.model_url = model_url + self.api_key
        self.headers = {"Content-Type": "application/json"}
        self.base_user_prompt = user_prompt_template
        self.base_system_prompt = system_prompt

    def create_request(
        self, user_prompt: str, temperature: float = 0.5, max_output_tokens: int = 100
    ) -> dict:
        return request_template(
            user_prompt=user_prompt,
            system_prompt=self.base_system_prompt,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )

    def call_completions(self, payload: dict) -> tuple:
        """Calls the completion API and returns the response text and status code."""
        json_payload = json.dumps(payload)
        try:
            logging.info(
                f"Sending completions request to {self.model_url}, with header {self.headers} and payload {json_payload}"
            )
            response = requests.post(
                self.model_url, headers=self.headers, data=json_payload
            )
            logging.info(
                f"Received response from API, with response code {response.status_code}"
            )

            # Extract the answer text
            response_text = json.loads(response.text)["candidates"][0]["content"][
                "parts"
            ][0]["text"]

            logging.info(f"Parsed user message: {response_text}")
            return response_text, response.status_code

        except requests.exceptions.HTTPError as http_err:
            logging.error(f"HTTP error occurred: {http_err}")
        except KeyError as key_err:
            logging.error(f"Key error while processing the response: {key_err}")
        except json.JSONDecodeError as json_err:
            logging.error(f"Error decoding JSON response: {json_err}")
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
        return None, response.status_code
