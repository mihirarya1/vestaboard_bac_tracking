import logging
import asyncio
from datetime import datetime
from flask import Flask, request
from threading import Thread
from twilio.twiml.messaging_response import MessagingResponse
from logic import Logic

current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_filename = f"log_{current_time}.txt"


logging.basicConfig(
    filename="logs/" + log_filename,
    filemode="w",
    format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
    level=logging.INFO,
)


class FlaskApp:
    def __init__(
        self,
    ):  # the vestaboard instance should be tied to the Game instance, and should be accessed using locks
        self.app = Flask(__name__)
        self.logic_instance = Logic()
        self.app.route("/sms", methods=["POST"])(self.sms_reply)

    def run_async_task(self, coro):
        """Run an async coroutine in a new event loop."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(coro)
        loop.close()

    async def process_message_async(self, client_number, message):
        """Asynchronous function to process the message."""
        try:

            await self.logic_instance.process_message(client_number, message)
        except Exception as e:
            logging.error(
                f"Error processing message for {client_number}: {e}", exc_info=True
            )

    def sms_reply(self):
        """Receive incoming SMS messages."""
        client_number = request.form["From"]
        message = request.form["Body"]

        # Start a thread for processing the message asynchronously

        logging.info(
            f"Received message: {message}, from number {client_number}. Creating new thread to handle."
        )
        thread = Thread(
            target=self.run_async_task,
            args=(self.process_message_async(client_number, message),),
        )
        thread.start()

        # Dummy Twilio response to avoid 500 error
        resp = MessagingResponse()
        resp.message()
        return str(resp)

    def run(self):
        """Run the Flask application."""
        logging.info("Starting flask server on port 3000")
        self.app.run(port=3000, debug=False)


if __name__ == "__main__":
    flask_app = FlaskApp()
    flask_app.run()
