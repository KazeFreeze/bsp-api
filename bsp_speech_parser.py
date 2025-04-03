"""
BSP Speech Parser

A utility for fetching and parsing speeches from the Bangko Sentral ng Pilipinas (BSP) website.
This module provides functionality to retrieve speech data, clean it, and save it in various formats.
"""

import requests
import pandas as pd
import os
import re
import csv
import json
from datetime import datetime, timedelta, timezone
from dateutil import parser as date_parser
import html
import ftfy


class BSPSpeechParser:
    """
    Parser for BSP speeches from the official website.

    This class handles fetching, parsing, cleaning, and saving speeches from the
    Bangko Sentral ng Pilipinas website.

    Attributes:
        base_url (str): The API endpoint for BSP speeches.
        headers (dict): HTTP headers for API requests.
        ph_timezone (timezone): Philippine timezone (UTC+8).
        output_folder (str): Directory for saving outputs.
    """

    def __init__(self, output_folder=None):
        """
        Initialize the BSP Speech Parser.

        Args:
            output_folder (str, optional): Directory path to save output files.
                                          If provided, necessary subdirectories will be created.
        """
        self.base_url = (
            "https://www.bsp.gov.ph/_api/web/lists/getByTitle('Speeches%20list')/items"
        )
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json;odata=verbose;charset=utf-8",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        }
        # Philippine timezone (UTC+8)
        self.ph_timezone = timezone(timedelta(hours=8))

        # Set output folder if provided
        self.output_folder = output_folder
        if self.output_folder:
            # Create output folder and required subdirectories if they don't exist
            if not os.path.exists(self.output_folder):
                os.makedirs(self.output_folder)

            # Create subdirectories for processed data and raw responses
            os.makedirs(os.path.join(self.output_folder, "processed"), exist_ok=True)
            os.makedirs(os.path.join(self.output_folder, "csv"), exist_ok=True)
            os.makedirs(
                os.path.join(self.output_folder, "raw_responses"), exist_ok=True
            )

    def parse_date(self, date_str):
        """
        Parse date string in various formats to ISO format while maintaining Philippine Time context.

        Args:
            date_str (str): Date string in various formats (e.g., '6/29', '01/01/2023', 'January 1, 2023')

        Returns:
            str: ISO formatted date string in UTC (for API compatibility)

        Raises:
            ValueError: If the date string cannot be parsed
        """
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
        """
        Convert UTC date string to Philippine Time datetime object.

        Args:
            utc_date_str (str): UTC date string from API response

        Returns:
            datetime: Date in Philippine Time zone or None if conversion fails
        """
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
        """
        Fetch speeches within the given date range from the BSP API.

        Args:
            start_date (str, optional): Start date for filtering speeches.
                                       If None, defaults to '2000-01-01'.
            end_date (str, optional): End date for filtering speeches.
                                     If None, defaults to current date.

        Returns:
            list: List of speech data dictionaries from the API response
        """
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

        # Save the raw response
        self.save_raw_response(
            response, f"raw_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            return data.get("value", [])
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return []

    def fix_encoding(self, text):
        """
        Fix encoding issues using ftfy and specific character replacements.

        Args:
            text (str): Text with potential encoding issues

        Returns:
            str: Text with encoding issues fixed
        """
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
        """
        Clean HTML content from the speech transcription.

        Args:
            html_content (str): HTML content from the API response

        Returns:
            str: Cleaned plain text without HTML tags and encoding issues
        """
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
        """
        Extract and clean relevant speech data from JSON response.

        Args:
            speeches_json (list): List of speech dictionaries from the API

        Returns:
            list: List of cleaned speech dictionaries with formatted data
        """
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

    def save_raw_response(self, response, filename):
        """
        Save the raw API response as received before any processing.

        Args:
            response (Response): Response object from requests
            filename (str): Filename to save the response under

        Raises:
            ValueError: If output folder is not set
        """
        if not self.output_folder:
            raise ValueError("Output folder not set")

        path = os.path.join(self.output_folder, "raw_responses", filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(response.text)
        print(f"Raw API response saved: {path}")

    def save_processed_data(self, content, filename):
        """
        Save the processed speech data as JSON.

        Args:
            content (list): Processed speech data
            filename (str): Filename to save the data under

        Raises:
            ValueError: If output folder is not set
        """
        if not self.output_folder:
            raise ValueError("Output folder not set")

        path = os.path.join(self.output_folder, "processed", filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(content, f, indent=4, ensure_ascii=False)
        print(f"Processed data saved: {path}")

    def save_csv_file(self, speeches, filename):
        """
        Save the speeches to a CSV file.

        Args:
            speeches (list): List of speech dictionaries
            filename (str): Filename for the CSV file

        Raises:
            ValueError: If output folder is not set
        """
        if not self.output_folder:
            raise ValueError("Output folder not set")

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

    def get_speeches(self, start_date=None, end_date=None, save_files=False):
        """
        Get speeches within the given date range and return them as a list.

        Args:
            start_date (str, optional): Start date in any recognized format.
            end_date (str, optional): End date in any recognized format.
            save_files (bool, optional): Whether to save processed and CSV files.

        Returns:
            list: List of dictionaries containing cleaned speech data

        Raises:
            ValueError: If save_files is True but output_folder is not set
        """
        try:
            # Fetch speeches
            speeches_raw = self.fetch_speeches(start_date, end_date)

            if not speeches_raw:
                print("No speeches found for the given date range.")
                return []

            # Extract and clean the data
            speeches_clean = self.extract_speech_data(speeches_raw)

            # Save files if requested
            if save_files:
                if not self.output_folder:
                    raise ValueError("Output folder must be set to save files")

                # Generate a filename based on the date range
                date_str_start = start_date.replace("/", "-") if start_date else "all"
                date_str_end = end_date.replace("/", "-") if end_date else "today"
                filename_prefix = f"speeches_{date_str_start}_to_{date_str_end}"

                # Save processed JSON data
                processed_filename = f"{filename_prefix}.json"
                self.save_processed_data(speeches_clean, processed_filename)

                # Save CSV
                csv_filename = f"{filename_prefix}.csv"
                self.save_csv_file(speeches_clean, csv_filename)

            return speeches_clean

        except Exception as e:
            print(f"Error getting speeches: {e}")
            import traceback

            traceback.print_exc()
            return []


def get_bsp_speeches(start_date=None, end_date=None, output_folder=None):
    """
    Convenience function to get BSP speeches within a date range.

    Args:
        start_date (str, optional): Start date in any recognized format.
        end_date (str, optional): End date in any recognized format.
        output_folder (str, optional): Folder to save files.

    Returns:
        list: List of dictionaries containing cleaned speech data
    """
    parser = BSPSpeechParser(output_folder)
    return parser.get_speeches(start_date, end_date, save_files=bool(output_folder))


if __name__ == "__main__":
    # This will run when the script is executed directly
    parser = BSPSpeechParser("bsp_speeches")

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

    speeches = parser.get_speeches(start_date, end_date, save_files=True)
    print(f"Successfully processed {len(speeches)} speeches.")
