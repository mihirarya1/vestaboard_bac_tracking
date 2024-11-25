import json
from datetime import datetime

import requests

from globals import bactrack_stats
import logging


class BacTrackStats:
    def __init__(
        self,
        url=bactrack_stats["histogram_url"],
        histogram_bins=bactrack_stats["histogram_bins"],
    ):
        self.url = url
        self.histogram_bins = histogram_bins

    def get_histogram_user_counts(
        self, current_day_of_week=datetime.now().isoweekday()
    ):
        logging.info("Making call to BacTrack Stats API")
        result = requests.get(url=self.url + str(current_day_of_week))
        logging.info(
            f"Received response from BacTrack Stats API with Status: {result.status_code}, Payload: {result.text}"
        )
        histogram_dict = {}
        try:
            payload = json.loads(result.text)
            user_counts = payload["bins"]
            if not isinstance(user_counts, list) or len(user_counts) != len(
                self.histogram_bins
            ):
                logging.warning(
                    "Mismatch between histogram bins and user counts returned from BacTrack Stats API"
                )
                return {}
            for i in range(len(user_counts)):
                histogram_dict[self.histogram_bins[i]] = user_counts[i]
        except Exception:
            logging.warning(
                "Unexpected error while parsing user counts from BacTrack Stats API"
            )
            return {}
        return histogram_dict
