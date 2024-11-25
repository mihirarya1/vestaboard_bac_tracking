import asyncio
import time
from asyncio import sleep
from bleak import BleakClient
from bleak.exc import BleakError, BleakDeviceNotFoundError
from globals import bactrack_metadata
from tenacity import retry, stop_after_attempt, wait_fixed

import logging


class BacTrack:
    def __init__(
        self,
        device_bluetooth_address,
        battery_level_characteristic_uuid=bactrack_metadata[
            "BATTERY_LEVEL_CHARACTERISTIC_UUID"
        ],
        connection_initialization_uuid=bactrack_metadata[
            "CONNECTION_INITIALIZATION_UUID"
        ],
        start_test_uuid=bactrack_metadata["START_TEST_UUID"],
        test_results_listener_uuid=bactrack_metadata["TEST_RESULTS_LISTENER_UUID"],
    ):
        self.BATTERY_LEVEL_CHARACTERISTIC_UUID = battery_level_characteristic_uuid
        self.CONNECTION_INITIALIZATION_UUID = connection_initialization_uuid
        self.START_TEST_UUID = start_test_uuid
        self.TEST_RESULTS_LISTENER_UUID = test_results_listener_uuid

        self.device_bluetooth_address = device_bluetooth_address
        self.client = None

        self.is_test_running = False
        self.last_read_notification_timestamp = None
        self.stage = None

    async def check_connection(self):
        # This function actively checks if the client is still connected
        try:
            while self.is_test_running:
                if not self.client.is_connected:
                    logging.error("Device unexpectedly disconnected!")
                    raise Exception("Device unexpectedly disconnected!")
                if (
                    self.stage
                    and self.stage > 1
                    and self.stage <= 3
                    and time.time() - self.last_read_notification_timestamp
                    > bactrack_metadata["read_notifications_timeout_duration"]
                ):
                    logging.error(
                        "Did not get a read_notification from device in greater than threshold."
                    )
                    raise Exception(
                        "Did not get a read_notification from device in greater than threshold."
                    )
                await asyncio.sleep(1)  # check for connection open every 2 seconds
            return
        except Exception as e:
            logging.error(f"Exception in check_connection: {e}")
            raise Exception(f"Exception in check_connection: {e}")

    async def get_battery_state(self):
        try:
            prev_pct = await self.get_battery_percentage()
            previous_voltage = self.battery_pct_to_voltage(prev_pct)
            await sleep(0.5)
            curr_pct = await self.get_battery_percentage()
            curr_voltage = self.battery_pct_to_voltage(curr_pct)
            battery_state = "Invalid"
            if curr_voltage <= 3.7 and previous_voltage <= 3.7:
                battery_state = "Low"
            elif 3.7 < curr_voltage <= 3.8 and 3.7 < previous_voltage <= 3.8:
                battery_state = "Medium Low"
            elif 3.8 < curr_voltage <= 4.0 and 3.8 < previous_voltage <= 4.0:
                battery_state = "Medium"
            elif 4.0 < curr_voltage <= 5.9 and 4.0 < previous_voltage <= 5.9:
                battery_state = "High"
            logging.info(f"Read battery state of {battery_state}")
            return battery_state
        except BleakError as e:
            logging.error(f"Error reading battery state: {e}")
            return "Invalid"

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(2))
    async def bluetooth_connect(self):
        try:
            if not self.client or not self.client.is_connected:
                self.client = BleakClient(
                    address_or_ble_device=self.device_bluetooth_address,
                    timeout=bactrack_metadata["connection_timeout_duration"],
                )
                await self.client.connect()
                logging.info("Connected to breathalyzer")
        except BleakDeviceNotFoundError as e:
            logging.error(f"Unable to bluetooth find breathalyzer: {e}")
            raise Exception(f"Unable to bluetooth find breathalyzer: {e}")
        except BleakError as e:
            logging.error(f"Failed to connect to breathalyzer: {e}")
            raise Exception(f"Failed to connect to breathalyzer: {e}")

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    async def get_battery_percentage(self) -> int:
        try:
            if self.client.is_connected:
                battery_level = await self.client.read_gatt_char(
                    self.BATTERY_LEVEL_CHARACTERISTIC_UUID
                )
                logging.info(f"Read battery percentage of {int(battery_level[0])}%")
                return int(battery_level[0])
        except BleakError as e:
            logging.error(f"Error reading battery percentage: {e}")
            raise BleakError(f"Error reading battery percentage: {e}")

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(2))
    async def bluetooth_disconnect(self):
        try:
            if self.client.is_connected:
                await self.client.disconnect()
                logging.info("Disconnected from breathalyzer")
        except BleakError as e:
            logging.error(f"Error during breathalyzer disconnection: {e}")
            raise BleakError(f"Error during breathalyzer disconnection: {e}")

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(2))
    async def write_gatt_bytes(
        self, characteristic, bytes_data, expect_write_response=True
    ):
        try:
            if self.client.is_connected:
                await self.client.write_gatt_char(
                    characteristic, bytes_data, response=expect_write_response
                )
                logging.info(
                    f"Wrote GATT bytes on characteristic: {characteristic} to breathalyzer: {bytes_data}"
                )
        except BleakError as e:
            logging.error(f"Error writing GATT bytes to breathalyzer: {e}")
            raise BleakError(f"Error writing GATT bytes to breathalyzer: {e}")

    def battery_pct_to_voltage(self, pct):
        return pct * 0.01 * 1.1999998 + 3.0

    async def start_test(self):
        logging.info("Beginning breathalyzer test procedure")
        await self.write_gatt_bytes(
            self.CONNECTION_INITIALIZATION_UUID, bytes.fromhex("000100")
        )
        logging.info("Successfully did GATT initiation step 1")
        await self.write_gatt_bytes(
            self.CONNECTION_INITIALIZATION_UUID, bytes.fromhex("000130")
        )
        logging.info("Successfully did GATT initiation step 2")
        await sleep(1)

        await self.write_gatt_bytes(self.START_TEST_UUID, bytes.fromhex("027203e0"))
        logging.info("Successfully started test")

    async def conduct_test(self, message_callback, client_number):
        try:
            if self.client.is_connected and await self.get_battery_state() not in [
                "Invalid",
                "Low",
            ]:
                await self.start_test()

                logging.info(
                    f"Starting notification listener on breathalyzer characteristic: {self.TEST_RESULTS_LISTENER_UUID}"
                )

                test_results_future = asyncio.Future()
                await self.client.start_notify(
                    self.TEST_RESULTS_LISTENER_UUID,
                    lambda sender, data: self.test_results_listener(
                        data, message_callback, client_number, test_results_future
                    ),
                )
                self.is_test_running = True

                await asyncio.create_task(self.check_connection())

                done, pending = await asyncio.wait(
                    [
                        test_results_future,  # Wait directly for the existing Future
                        asyncio.create_task(asyncio.sleep(60)),
                    ],
                    return_when=asyncio.FIRST_COMPLETED,
                )

                results = "Error occured during BAC test"
                if test_results_future.done() and test_results_future.result():
                    logging.info("Test end criterion reached: attained test results")
                    results = test_results_future.result()
                else:
                    logging.warning(
                        "Test end criterion reached: hit test timeout duration"
                    )
                await self.end_test()
                return results
        except Exception as e:
            logging.error(f"Error while conducting breathalyzer test: {e}")
            await self.end_test()
            raise Exception(f"Error while conducting breathalyzer test: {e}")

    def test_results_listener(
        self, data, message_callback, client_number, test_results_future
    ):
        self.last_read_notification_timestamp = time.time()
        if self.client.is_connected and self.is_test_running:
            logging.info("Bytes received on breathalyzer test listener")

            if len(data) != 13:
                logging.warning("Invalid data received on breathalyzer test listener")
                return

            stage = data[2] & 0x0F
            self.stage = stage
            countdown = data[5] & 0x0F

            description = ""
            if stage == 1:
                description = "WARMING_UP"
            if stage == 2:
                description == "BEGIN_BLOWING"
            if stage == 3:
                description = "KEEP_BLOWING"
                if countdown == 0:
                    description = "STOP_BLOWING"
            if stage == 4:
                description = "PROCESSING"
            if stage == 5:
                description = "ATTAINED_RESULTS"
                reading = ((data[3] & 255) * 256 + (data[4] & 255)) / 10000.0
                reading = f"{float(reading):.3f}"
                test_results_future.set_result(reading)
                self.is_test_running = False
                logging.info(f"Attained BAC reading of {reading}")
                countdown = reading

            print(
                f"Stage description: {description}, with countdown/reading: {countdown}"
            )  # eventually comment out
            message_callback(description, str(countdown), client_number)

            logging.info(
                f"Stage description: {description}, with countdown/reading: {countdown}"
            )
            return countdown

    async def end_test(self):
        logging.info("Beginning end breathalyzer test procedure")

        try:
            if self.client.is_connected and self.is_test_running:
                self.is_test_running = False
                self.last_read_notification_timestamp = None
                self.stage = None

                logging.info(
                    f"Stopping notification listener on breathalyzer characteristic: {self.TEST_RESULTS_LISTENER_UUID}"
                )
                await self.client.stop_notify(self.TEST_RESULTS_LISTENER_UUID)
                await self.client.write_gatt_char(
                    self.CONNECTION_INITIALIZATION_UUID, bytes.fromhex("000130")
                )
                logging.info("Successfully completed breathalyzer test ending step 1")
                await self.client.write_gatt_char(
                    self.CONNECTION_INITIALIZATION_UUID, bytes.fromhex("000100")
                )
                logging.info("Successfully completed breathalyzer test ending step 2")
        except BleakError as e:
            logging.error(f"Error during breathalyzer test end: {e}")
