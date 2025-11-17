# Creative Commons Images Downloader

This script downloads Creative Commons licensed images for medical education questions from Wikimedia Commons.

## Features

- Parses 68 medical education questions from the provided content
- Extracts the main medical topic/condition for each question
- Searches Wikimedia Commons for Creative Commons licensed images
- Downloads the most relevant image for each question
- Creates a log file with download details

## Requirements

- Python 3.7+
- requests library
- Pillow library (for adding citation overlays to images)

## Installation

1. Install the required dependencies:
```bash
pip3 install --user -r requirements.txt
```

Or if you have permission issues, you may need to use:
```bash
pip3 install --break-system-packages -r requirements.txt
```

**Note**: If Pillow installation fails, the script will still download images but won't add citation overlays. You can add citations manually later.

## Usage

Run the script:
```bash
python download_cc_images.py
```

The script will:
1. Extract all 68 questions from the content
2. For each question, identify the main medical topic
3. Search Wikimedia Commons for CC-licensed images
4. Download the most relevant image to the `downloaded_images/` folder
5. Create a log file `downloaded_images/download_log.txt` with details

## Output

- **Images**: Saved as `question_01.jpg`, `question_02.jpg`, etc. in the `downloaded_images/` folder
- **Log file**: `downloaded_images/download_log.txt` contains:
  - Question number and topic
  - Question and answer text
  - Image filename and URL
  - Download status

## Notes

- The script includes rate limiting to be respectful to the Wikimedia Commons API
- Images are filtered to only include Creative Commons licensed content
- If no CC-licensed image is found for a question, it will be logged in the error log
- The script searches for medical terms related to each question's answer

## License

The downloaded images are Creative Commons licensed. Please check the individual image licenses and provide appropriate attribution when using them.

