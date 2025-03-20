# BSP Speech Parser

![Python](https://img.shields.io/badge/Python-3.6%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)

A Python library for extracting and parsing speeches from the Bangko Sentral ng Pilipinas (BSP) website.

## Overview

BSP Speech Parser provides tools to fetch, clean, and analyze speeches published by the Bangko Sentral ng Pilipinas. The library handles date conversion between UTC and Philippine Time, fixes encoding issues, and offers convenient methods to save the extracted data in both raw JSON and CSV formats.

## Features

- Fetch speeches from BSP's website within a specified date range
- Clean HTML content and fix encoding issues in speech transcriptions
- Convert between UTC and Philippine Time (UTC+8)
- Save extracted speeches as JSON and CSV files
- Flexible date parsing that accepts various formats

## Installation

### Prerequisites

- Python 3.6+

### Setup

1. Clone this repository:

```bash
git clone https://github.com/yourusername/bsp-speech-parser.git
cd bsp-speech-parser
```

2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Simple Example

```python
from bsp_speech_parser import get_bsp_speeches

# Get speeches from January 1, 2023 to March 31, 2023
speeches = get_bsp_speeches("01/01/2023", "03/31/2023")

# Print the number of speeches found
print(f"Found {len(speeches)} speeches")
```

### Save to Files

```python
# Get speeches and save files (both JSON and CSV)
speeches = get_bsp_speeches(
    "01/01/2023",
    "03/31/2023",
    output_folder="bsp_data"
)
```

### Using the Class Directly

```python
from bsp_speech_parser import BSPSpeechParser

# Create a parser instance with a custom output folder
parser = BSPSpeechParser(output_folder="custom_output")

# Get recent speeches
recent_speeches = parser.get_speeches("01/01/2024", None, save_files=True)

# Filter speeches by speaker
all_speeches = parser.get_speeches()
governor_speeches = [s for s in all_speeches if "Governor" in s.get("Speaker", "")]
```

### Convert to Pandas DataFrame

```python
import pandas as pd
from bsp_speech_parser import get_bsp_speeches

speeches = get_bsp_speeches("01/01/2023", "03/31/2023")
df = pd.DataFrame(speeches)
```

### Command Line Interface

The library also includes a simple command-line interface:

```bash
python bsp_speech_parser.py
```

This will prompt you to enter a date range and save the extracted speeches to a folder named "bsp_speeches".

## Output Format

Each speech is returned as a dictionary with the following fields:

- `Title`: The title of the speech
- `Date`: Formatted date in Philippine Time (e.g., "January 1, 2023")
- `SDate`: Original date string for sorting
- `Place`: Location where the speech was delivered
- `Occasion`: The event or occasion for the speech
- `Speaker`: Name of the person who delivered the speech
- `Transcription`: Clean text of the speech with HTML tags and encoding issues removed

## Project Structure

```
bsp-speech-parser/
├── bsp_speech_parser.py   # Main library file
├── example_usage.py       # Example scripts
├── requirements.txt       # Required dependencies
└── README.md              # This file
```

## License

This project is licensed under the MIT License - see below for details:

MIT License

Copyright (c) 2025 Bernard G. Tapiru, Jr.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
