import requests
import pandas as pd
import os
import re
import csv
import json
from datetime import datetime, timedelta, timezone
from dateutil import parser as date_parser
import html
import ftfy  # Added import for ftfy


class BSPSpeechParser:
    def __init__(self):
        self.base_url = (
            "https://www.bsp.gov.ph/_api/web/lists/getByTitle('Speeches%20list')/items"
        )
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json;odata=verbose;charset=utf-8",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        }
        self.output_folder = "bsp_speeches"
        # Philippine timezone (UTC+8)
        self.ph_timezone = timezone(timedelta(hours=8))

        # Create output folder if it doesn't exist
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
            os.makedirs(os.path.join(self.output_folder, "raw"))
            os.makedirs(os.path.join(self.output_folder, "csv"))

    def parse_date(self, date_str):
        """Parse date string in various formats to ISO format while maintaining Philippine Time context"""
        try:
            # If input is like '6/29', assume current year and set to midnight Philippine Time
            if "/" in date_str and len(date_str.split("/")) == 2:
                # Use current year if year is not specified
                current_year = datetime.now().year
                month, day = date_str.split("/")

                # Create a datetime at midnight Philippine Time
                ph_date = datetime(current_year, int(month), int(day), 0, 0, 0)

                # Convert to UTC for API (subtract 8 hours)
                utc_time = ph_date - timedelta(hours=8)

                return utc_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")

            # For other formats, parse the date
            parsed_date = date_parser.parse(date_str)

            # If no timezone info, assume it's Philippine time
            if parsed_date.tzinfo is None:
                parsed_date = parsed_date.replace(tzinfo=self.ph_timezone)

            # Convert to UTC for API
            utc_date = parsed_date.astimezone(timezone.utc)
            return utc_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")

        except Exception as e:
            raise ValueError(f"Unable to parse date: {date_str}. Error: {e}")

    def ph_time_from_utc(self, utc_date_str):
        """Convert UTC date string to Philippine Time datetime object"""
        if not utc_date_str:
            return None

        try:
            # Parse the UTC date string
            if utc_date_str.endswith("Z"):
                utc_date = datetime.strptime(utc_date_str, "%Y-%m-%dT%H:%M:%SZ")
                utc_date = utc_date.replace(tzinfo=timezone.utc)
            else:
                utc_date = date_parser.parse(utc_date_str)
                if utc_date.tzinfo is None:
                    utc_date = utc_date.replace(tzinfo=timezone.utc)

            # Convert to Philippine Time
            ph_date = utc_date.astimezone(self.ph_timezone)
            return ph_date

        except Exception as e:
            print(f"Error converting UTC to PHT: {e}")
            return None

    def fetch_speeches(self, start_date=None, end_date=None):
        """Fetch speeches within the given date range"""
        # Default to current date if end_date is not provided
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000Z")
        else:
            end_date = self.parse_date(end_date)

        # Use a very old date if start_date is not provided
        if start_date is None:
            start_date = "2000-01-01T00:00:00.000Z"
        else:
            start_date = self.parse_date(start_date)

        # Construct the query parameters
        params = {
            "$select": "*",
            "$filter": f"SDate ge '{start_date}' and SDate le '{end_date}' and OData__ModerationStatus eq 0",
            "$top": "5000",
            "$orderby": "SDate desc",
        }

        # Make the request
        response = requests.get(self.base_url, headers=self.headers, params=params)

        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            return data.get("value", [])
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return []

    def fix_encoding(self, text):
        """Fix encoding issues using ftfy and specific character replacements"""
        if not text:
            return ""

        # Use ftfy to fix mojibake and other encoding issues
        fixed_text = ftfy.fix_text(text)

        # Additional specific character replacements for stubborn encoding issues
        replacements = [
            # Unicode to ASCII replacements
            ("\u2013", "-"),  # En dash to hyphen
            ("\u2014", "--"),  # Em dash to double hyphen
            ("\u2018", "'"),  # Left single quote
            ("\u2019", "'"),  # Right single quote
            ("\u201c", '"'),  # Left double quote
            ("\u201d", '"'),  # Right double quote
            ("\u2026", "..."),  # Ellipsis
            ("\u200b", ""),  # Zero-width space
            ("\u00a0", " "),  # Non-breaking space
        ]

        # Apply all replacements
        for pattern, replacement in replacements:
            fixed_text = re.sub(pattern, replacement, fixed_text)

        return fixed_text

    def clean_html_content(self, html_content):
        """Clean HTML content from the speech transcription"""
        if not html_content:
            return ""

        # First decode HTML entities
        decoded_html = html.unescape(html_content)

        # Fix encoding issues using our enhanced method
        fixed_html = self.fix_encoding(decoded_html)

        # Remove HTML tags
        clean_text = re.sub(r"<.*?>", " ", fixed_html)

        # Replace non-breaking spaces
        clean_text = clean_text.replace("\xa0", " ")

        # Normalize whitespace (remove multiple spaces)
        clean_text = re.sub(r"\s+", " ", clean_text)

        # Final cleanup
        clean_text = clean_text.strip()

        return clean_text

    def extract_speech_data(self, speeches_json):
        """Extract relevant speech data from JSON response"""
        extracted_speeches = []

        for speech in speeches_json:
            # Convert UTC date to Philippine Time and format for display
            speech_date = None
            if speech.get("SDate"):
                speech_date = self.ph_time_from_utc(speech.get("SDate"))

            # Format date in Philippine Time
            formatted_date = speech_date.strftime("%B %d, %Y") if speech_date else ""

            # Get text fields and fix encoding issues
            title = self.fix_encoding(speech.get("Title", ""))
            place = self.fix_encoding(speech.get("Place", ""))
            occasion = self.fix_encoding(speech.get("Occasion", ""))
            speaker = self.fix_encoding(speech.get("Speaker", ""))

            # Clean the transcription HTML
            transcription = self.clean_html_content(speech.get("Transcription", ""))

            # Create a cleaned speech object with only the fields we need
            clean_speech = {
                "Title": title,
                "Date": formatted_date,
                "SDate": speech.get("SDate", ""),  # Keep original date for sorting
                "Place": place,
                "Occasion": occasion,
                "Speaker": speaker,
                "Transcription": transcription,
            }

            extracted_speeches.append(clean_speech)

        return extracted_speeches

    def save_raw_file(self, content, filename):
        """Save the raw content to a file"""
        path = os.path.join(self.output_folder, "raw", filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(content, f, indent=4, ensure_ascii=False)
        print(f"Raw file saved: {path}")

    def save_csv_file(self, speeches, filename):
        """Save the speeches to a CSV file"""
        path = os.path.join(self.output_folder, "csv", filename)

        # Define the CSV headers - only include the fields we want in our CSV
        headers = ["Title", "Date", "Place", "Occasion", "Speaker", "Transcription"]

        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for speech in speeches:
                # Create a new dict with only the fields in our headers
                filtered_speech = {k: speech[k] for k in headers if k in speech}
                writer.writerow(filtered_speech)

        print(f"CSV file saved: {path}")

    def process_speeches(self, start_date=None, end_date=None):
        """Process speeches within the given date range"""
        # Generate a filename based on the date range
        date_str_start = start_date.replace("/", "-") if start_date else "all"
        date_str_end = end_date.replace("/", "-") if end_date else "today"
        filename_prefix = f"speeches_{date_str_start}_to_{date_str_end}"

        # Fetch speeches
        try:
            # Make the request
            print(
                f"Fetching speeches from {start_date if start_date else 'beginning'} to {end_date if end_date else 'today'}..."
            )

            speeches_raw = self.fetch_speeches(start_date, end_date)

            if speeches_raw:
                # Save raw file (JSON format)
                raw_filename = f"{filename_prefix}.json"
                self.save_raw_file(speeches_raw, raw_filename)

                # Extract and clean the data
                speeches_clean = self.extract_speech_data(speeches_raw)

                # Save CSV
                csv_filename = f"{filename_prefix}.csv"
                self.save_csv_file(speeches_clean, csv_filename)

                print(f"Successfully processed {len(speeches_raw)} speeches.")
                return True
            else:
                print("No speeches found for the given date range.")
                return False
        except Exception as e:
            print(f"Error processing speeches: {e}")
            import traceback

            traceback.print_exc()
            return False


def main():
    parser = BSPSpeechParser()

    print("BSP Speech Parser")
    print("=================")
    print("Enter date range to fetch speeches (leave blank for all speeches)")
    print("For simple date formats like '6/29', the current year will be used")
    print("All dates are interpreted as Philippine Time (UTC+8)")

    start_date = input(
        "Start date (e.g., '6/29', '01/01/2023', 'January 1, 2023'): "
    ).strip()
    end_date = input(
        "End date (e.g., '6/30', '12/31/2023', 'December 31, 2023'): "
    ).strip()

    # Use None if no date is provided
    start_date = None if start_date == "" else start_date
    end_date = None if end_date == "" else end_date

    parser.process_speeches(start_date, end_date)


if __name__ == "__main__":
    main()
