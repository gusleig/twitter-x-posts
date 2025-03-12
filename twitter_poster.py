import argparse
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional

import pytz
import tweepy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("twitter_poster.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class TwitterPoster:
    def __init__(self, credentials_file: str, posts_file: str):
        """
        Initialize TwitterPoster with API credentials and posts data

        Args:
            credentials_file (str): Path to JSON file with Twitter API credentials
            posts_file (str): Path to JSON file with posts data
        """
        self.credentials = self._load_json(credentials_file)
        self.posts_data = self._load_json(posts_file)
        self.client = self._setup_client()
        self.brazil_tz = pytz.timezone("America/Sao_Paulo")
        self.posts_file = posts_file

    def _load_json(self, file_path: str) -> Dict:
        """Load and parse JSON file"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading JSON file {file_path}: {str(e)}")
            raise

    def _setup_client(self) -> tweepy.Client:
        """Setup Twitter API v2 client"""
        try:
            return tweepy.Client(
                consumer_key=self.credentials["api_key"],
                consumer_secret=self.credentials["api_key_secret"],
                access_token=self.credentials["access_token"],
                access_token_secret=self.credentials["access_token_secret"],
            )
        except Exception as e:
            logger.error(f"Error setting up Twitter client: {str(e)}")
            raise

    def post_tweet(self, text: str, reply_to_id: Optional[str] = None) -> str:
        """
        Post a tweet and return its ID

        Args:
            text (str): Tweet text content
            reply_to_id (str, optional): ID of tweet to reply to

        Returns:
            str: ID of posted tweet
        """
        try:

            response = self.client.create_tweet(
                text=text, in_reply_to_tweet_id=reply_to_id
            )
            tweet_id = response.data["id"]
            logger.info(f"Successfully posted tweet: {tweet_id}")
            return tweet_id
        except Exception as e:
            logger.error(f"Error posting tweet: {str(e)}")
            raise

    def post_thread(self, tweets: List[Dict]) -> None:
        """
        Post a complete thread of tweets

        Args:
            tweets (List[Dict]): List of tweet objects with text and reply_to_id
        """
        previous_tweet_id = None

        for tweet in tweets:
            if tweet["reply_to_id"] == "previous":
                tweet["reply_to_id"] = previous_tweet_id

            previous_tweet_id = self.post_tweet(
                text=tweet["text"], reply_to_id=tweet["reply_to_id"]
            )
            # Wait 2 seconds between tweets to avoid rate limits
            time.sleep(2)

    def post_specific_thread(self, thread_index: int) -> None:
        """
        Post a specific thread by its index

        Args:
            thread_index (int): Index of the thread in the JSON file (1-based)
        """
        try:
            # Convert to 0-based index
            index = thread_index - 1

            if index < 0 or index >= len(self.posts_data["threads"]):
                raise ValueError(
                    f"Thread index {thread_index} is out of range. Available threads: 1-{len(self.posts_data['threads'])}"
                )

            thread = self.posts_data["threads"][index]
            logger.info(f"Posting thread #{thread_index} immediately")
            self.post_thread(thread["tweets"])

            # Remove posted thread from data
            self.posts_data["threads"].pop(index)

            # Save the posted thread to archived.json
            archived_file = "archived.json"
            try:
                with open(archived_file, "r") as f:
                    archived_data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                archived_data = {"threads": []}

            archived_data["threads"].append(thread)

            with open(archived_file, "w") as f:
                json.dump(archived_data, f, indent=4)

            # Save updated posts data
            with open(self.posts_file, "w") as f:
                json.dump(self.posts_data, f, indent=4)

            logger.info(f"Successfully posted thread #{thread_index}")

        except Exception as e:
            logger.error(f"Error posting thread #{thread_index}: {str(e)}")
            raise

    def run_scheduler(self) -> None:
        """Main execution loop for posting threads at scheduled times"""
        logger.info("Starting scheduled posting mode")
        while True:
            try:
                current_time = datetime.now(self.brazil_tz)

                for thread in self.posts_data["threads"]:
                    scheduled_time = datetime.strptime(
                        thread["scheduled_time"], "%Y-%m-%d %H:%M:%S"
                    ).replace(tzinfo=self.brazil_tz)

                    # Check if it's time to post this thread
                    if current_time >= scheduled_time:
                        logger.info(f"Posting thread scheduled for {scheduled_time}")
                        self.post_thread(thread["tweets"])

                        # Save the posted thread to archived.json
                        archived_file = "archived.json"

                        try:
                            with open(archived_file, "r") as f:
                                archived_data = json.load(f)
                        except (FileNotFoundError, json.JSONDecodeError):
                            archived_data = {"threads": []}

                        archived_data["threads"].append(thread)

                        with open(archived_file, "w") as f:
                            json.dump(archived_data, f, indent=4)

                        # Remove posted thread from data
                        self.posts_data["threads"].remove(thread)

                        # Save updated posts data
                        with open(self.posts_file, "w", encoding="utf-8") as f:
                            json.dump(self.posts_data, f, indent=2)

                # Sleep for 30 seconds before next check
                time.sleep(30)

                # Exit if no more threads to post
                if not self.posts_data["threads"]:
                    logger.info("All threads have been posted. Exiting.")
                    break

            except Exception as e:
                logger.error(f"Error in scheduler loop: {str(e)}")
                time.sleep(60)  # Wait a minute before retrying


def main():
    parser = argparse.ArgumentParser(description="Twitter Thread Poster")
    parser.add_argument(
        "thread_number",
        type=int,
        nargs="?",
        help="Thread number to post immediately (1-based index)",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Force immediate posting of specified thread",
    )
    args = parser.parse_args()

    poster = TwitterPoster(credentials_file="credentials.json", posts_file="posts.json")

    if args.thread_number and args.force:
        # Post specific thread immediately
        poster.post_specific_thread(args.thread_number)
    else:
        # Run in scheduler mode
        poster.run_scheduler()


if __name__ == "__main__":
    main()
