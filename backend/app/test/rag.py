import json
import uuid
from typing import List
from app.utils.chunks import chunkTimeStampedFile, clean_up_string

def generate_test_data(filepaths: List[str], output_file: str = "test_data.json", 
                       timestamp_regex: str = r"\[(\d{1,2}/\d{1,2}/\d{2}), \d{1,2}:\d{2}:\d{2}(?:.AM|.PM)?\]", 
                       date_format: str = "%d/%m/%y", interval: str = "week", overlap: int = 2) -> None:
    """
    Generates test data by chunking timestamp files and saving chunks to a JSON file.
    
    Args:
        filepaths (List[str]): List of files to process
        output_file (str): Path where to save the JSON output
        timestamp_regex (str): Regex pattern to match timestamps in the files
        date_format (str): Format string for parsing the datetime
        interval (str): One of 'day', 'week', or 'month'
        overlap (int): Number of days to overlap at beginning and end of chunks
    """
    samples = []
    
    for filepath in filepaths:
        try:
            # Process each chunk in the file
            for _, (_, _, lines) in enumerate(chunkTimeStampedFile(
                filepath, timestamp_regex, date_format, interval, overlap
            )):
                # Join the lines to create a single text chunk
                chunk_text = "".join(lines)
                removePatterns = {
                  "timeStampRegex": r"\[(\d{1,2}/\d{1,2}/\d{2}), \d{1,2}:\d{2}:\d{2}(?:.AM|.PM)?\]",
                }
                chunk_text = clean_up_string(chunk_text, removePatterns)
                
                # Create a sample with unique id and the chunk text
                sample = {
                    "id": str(uuid.uuid4()),
                    "context": chunk_text
                }
                
                samples.append(sample)
                
        except FileNotFoundError:
            print(f"Error: File not found: {filepath}")
            continue
        except ValueError as e:
            print(f"Error processing file: {e}")
            continue
        except Exception as e:
            print(f"Unexpected error processing file: {e}")
            continue
    
    # Create the final JSON structure
    data = {
        "samples": samples
    }
    
    # Write the data to the output file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"Generated test data with {len(samples)} samples in {output_file}")

if __name__ == "__main__":
    # Example usage
    files_to_process = [
        "app/data/_chat_abel_mesén.txt",
    ]
    
    generate_test_data(files_to_process, "app/test/test_data.json")