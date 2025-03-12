# X-Posts

A simple Python script to automate posting to X.

## Setup

1. Clone this repository:

   ```bash
   git clone https://github.com/gusleig/twitter-x-posts.git
   cd x-posts
   ```

2. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Create a `credentials.json` file by copying `example.credentials.json` and filling in your Twitter API credentials:

   ```bash
   cp example.credentials.json credentials.json
   ```

4. Edit `credentials.json` with your Twitter API keys and tokens:
   ```json
   {
     "api_key": "your_api_key",
     "api_secret_key": "your_api_secret_key",
     "access_token": "your_access_token",
     "access_token_secret": "your_access_token_secret"
   }
   ```

## Usage

Run the script to post to Twitter:

```bash
python twitter_poster.py
```

Make sure your posts are defined in `posts.json` before running the script.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
