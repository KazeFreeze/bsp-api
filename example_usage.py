# example_usage.py
from bsp_speech_parser import get_bsp_speeches, BSPSpeechParser
import pandas as pd

# Example 1: Simple usage with the convenience function
# Get speeches from January 1, 2023 to March 31, 2023
speeches = get_bsp_speeches("01/01/2023", "03/31/2023")

# Print the number of speeches found
print(f"Found {len(speeches)} speeches")

# Example 2: Convert to pandas DataFrame for analysis
df = pd.DataFrame(speeches)
print(df.head())

# Example 3: Get speeches and save files
speeches_with_files = get_bsp_speeches(
    "01/01/2023", "03/31/2023", output_folder="bsp_data"
)
print(f"Found and saved {len(speeches_with_files)} speeches")

# Example 4: Using the class directly for more control
parser = BSPSpeechParser(output_folder="custom_output")
recent_speeches = parser.get_speeches("01/01/2024", None, save_files=True)
print(f"Found {len(recent_speeches)} recent speeches")

# Example 5: Filter speeches by speaker
all_speeches = get_bsp_speeches()
governor_speeches = [s for s in all_speeches if "Governor" in s.get("Speaker", "")]
print(f"Found {len(governor_speeches)} speeches by governors")
