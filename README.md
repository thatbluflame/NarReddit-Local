# NarReddit-Local

NarReddit-Local is a locally running version of NarReddit, a tool for generating Reddit-style video content. This project aims to provide similar functionality to NarReddit but allows you to run it locally, eliminating the need to interact with external APIs or servers.

## Features
- Generates Reddit-style videos locally.
- No need to run a local API server for Gentle forced aligner, as it uses a forked version of Whisper from OpenAI.
- Requires input of title text and description text in designated files (`title-text.txt` and `description-text.txt`).
- Selects random background videos from the `background_videos/minecraft` folder.

## Usage
1. Install the packages using `pip install -r requirements.txt` in the Command Line
2. Ensure you have the required input files:
   - `title-text.txt`: Contains the title text for the video.
   - `description-text.txt`: Contains the description text for the video.
3. Add a video file to the `background_videos/minecraft` folder for the background.
4. Add your Logo to `intro_card_template` as `logo.png`
5. Run the script: `python main.py`
6. The generated video will be saved as `final.mp4`.

## Known Issues
- The project is still in development and may be unstable or have missing features.
- The user interface is currently rudimentary and not visually appealing.
- Some features present in NarReddit may be missing or incomplete. (Multilingual Video Output, OPENAI API)

## Contributing
Contributions to improve and extend NarReddit-Local are welcome! Feel free to submit bug reports, feature requests, or pull requests to help make this project better.
