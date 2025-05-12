import re
from datetime import datetime, timedelta
from typing import Generator, Tuple, List, Dict
from app.utils.dates import getDateIntervals

def chunkTimeStampedFile(filepath: str, timeStampRegex: str, dateRegex: str, interval: str, overlap: int) -> Generator[Tuple[datetime, datetime, List[str]], None, None]:
    """
    Generator that yields chunks of a timestamped file based on intervals with overlap periods
    at both the beginning and end of each chunk.
    
    Args:
        filepath (str): Path to the file to chunk
        timeStampRegex (str): Regex pattern to match timestamps in the file
        dateRegex (str): Format string for parsing the datetime
        interval (str): One of 'day', 'week', or 'month'
        overlap (int): Number of days to overlap at the beginning and end of each chunk
        
    Yields:
        Tuple[datetime, datetime, List[str]]: Each chunk containing:
            - Start date of the chunk (including overlap)
            - End date of the chunk (including overlap)
            - List of lines in the chunk
    """
    # Compile the regex for efficiency
    ts_pattern = re.compile(timeStampRegex)
    
    # First pass: find start and end dates
    with open(filepath, 'r', encoding='utf-8') as f:
        # Find first timestamp
        startDate = None
        for line in f:
            match = ts_pattern.search(line)
            if match:
                date_str = match.group(1)
                startDate = datetime.strptime(date_str, dateRegex)
                break
        
        # Find last timestamp
        endDate = None
        f.seek(0)  # Reset to beginning
        for line in f:
            match = ts_pattern.search(line)
            if match:
                date_str = match.group(1)
                current_date = datetime.strptime(date_str, dateRegex)
                if not endDate or current_date > endDate:
                    endDate = current_date

    if not startDate or not endDate:
        raise ValueError("Could not find timestamps in file")

    # Get the base intervals (without overlap)
    intervals = getDateIntervals(startDate, endDate, interval)
    
    # Second pass: yield chunks with overlaps
    with open(filepath, 'r', encoding='utf-8') as f:
        for i in range(len(intervals)):
            # Determine chunk boundaries with overlaps
            base_start = intervals[i]
            
            # If not the first chunk, add overlap at start
            chunk_start = base_start - timedelta(days=overlap) if i > 0 else base_start
            
            # Determine base end date (without overlap)
            if i == len(intervals) - 1:
                base_end = endDate
            else:
                base_end = intervals[i + 1]
            
            # If not the last chunk, add overlap at end
            chunk_end = base_end + timedelta(days=overlap) if i < len(intervals) - 1 else base_end
            
            # Reset file pointer to start
            f.seek(0)
            
            # Collect lines for this chunk
            chunk_lines = []
            for line in f:
                match = ts_pattern.search(line)
                if match:
                    date_str = match.group(1)
                    line_date = datetime.strptime(date_str, dateRegex)
                    if chunk_start <= line_date <= chunk_end:
                        chunk_lines.append(line)
            
            yield (chunk_start, chunk_end, chunk_lines)

def analyzeChunkSizes(files: List[str], timeStampRegex: str, dateRegex: str, interval: str, overlap: int) -> None:
    """
    Analyze the size of chunks across multiple files.
    
    Args:
        files (List[str]): List of file paths to analyze
        timeStampRegex (str): Regex pattern to match timestamps in the files
        dateRegex (str): Format string for parsing the datetime
        interval (str): One of 'day', 'week', or 'month'
        overlap (int): Number of days to overlap at beginning and end of chunks
    """
    all_chunk_sizes = []
    
    for filepath in files:
        print(f"\nAnalyzing file: {filepath}")
        try:
            # Process each chunk in the file
            for i, (start, end, lines) in enumerate(chunkTimeStampedFile(
                filepath, timeStampRegex, dateRegex, interval, overlap
            )):
                chunk_size = sum(len(clean_up_string(line, {"timeStampRegex": timeStampRegex})) for line in lines)
                all_chunk_sizes.append(chunk_size)
                print(f"  Chunk {i + 1}: {chunk_size:,} characters")
                
        except FileNotFoundError:
            print(f"  Error: File not found: {filepath}")
            continue
        except ValueError as e:
            print(f"  Error processing file: {e}")
            continue
        except Exception as e:
            print(f"  Unexpected error processing file: {e}")
            continue
    
    if all_chunk_sizes:
        min_size = min(all_chunk_sizes)
        max_size = max(all_chunk_sizes)
        avg_size = sum(all_chunk_sizes) / len(all_chunk_sizes)
        
        print("\nSummary Statistics:")
        print(f"Smallest chunk: {min_size:,} characters")
        print(f"Biggest chunk: {max_size:,} characters")
        print(f"Average chunk size: {avg_size:,.2f} characters")
    else:
        print("\nNo chunks were processed successfully.")

def getFirstChunkFromFile(filepath: str, timeStampRegex: str, dateRegex: str, interval: str) -> List[str]:
    """
    Gets only the lines from the first chunk of a timestamped file.
    
    Args:
        filepath (str): Path to the file to chunk
        timeStampRegex (str): Regex pattern to match timestamps in the file
        dateRegex (str): Format string for parsing the datetime
        interval (str): One of 'day', 'week', or 'month'
        
    Returns:
        List[str]: List of lines in the first chunk
            
    Raises:
        ValueError: If no timestamps found in file
        FileNotFoundError: If file doesn't exist
    """
    # Compile the regex for efficiency
    ts_pattern = re.compile(timeStampRegex)
    
    # First pass: find start date and first interval end date
    with open(filepath, 'r', encoding='utf-8') as f:
        # Find first timestamp
        startDate = None
        for line in f:
            match = ts_pattern.search(line)
            if match:
                date_str = match.group(1)
                startDate = datetime.strptime(date_str, dateRegex)
                break
                
        if not startDate:
            raise ValueError("Could not find timestamps in file")
            
        # Get the end date for the first interval
        intervals = getDateIntervals(startDate, startDate + timedelta(days=31), interval)
        if len(intervals) < 2:
            # If we only got one interval, we need to look for the actual end date
            f.seek(0)
            endDate = None
            for line in f:
                match = ts_pattern.search(line)
                if match:
                    date_str = match.group(1)
                    current_date = datetime.strptime(date_str, dateRegex)
                    if not endDate or current_date > endDate:
                        endDate = current_date
        else:
            endDate = intervals[1]  # Use the start of next interval as our end date
    
    # Second pass: collect lines for the first chunk
    chunk_lines = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            match = ts_pattern.search(line)
            if match:
                date_str = match.group(1)
                line_date = datetime.strptime(date_str, dateRegex)
                if startDate <= line_date < endDate:
                    chunk_lines.append(line)
                elif line_date >= endDate:
                    break  # We've gone past our chunk
    
    return chunk_lines

def clean_up_string(chunk: str, patterns: Dict[str, str]) -> str:
    """
    Removes patterns from a chunk based on provided regular expressions.
    
    Args:
        chunk (str): The text chunk to clean
        patterns (Dict[str, str]): Dictionary of pattern names to regex patterns
            that should be removed from the chunk
            
    Returns:
        str: The cleaned chunk with all matching patterns removed
    """
    result = chunk
    
    # Apply each regex pattern to remove matching content
    for pattern_name, regex_pattern in patterns.items():
        # Compile the regex for efficiency
        compiled_pattern = re.compile(regex_pattern)
        # Remove all matches of the pattern
        result = compiled_pattern.sub("", result)
    
    return result

if __name__ == "__main__":
    # Example usage
    files_to_analyze = [
        "app/data/_chat_abel_mesén.txt",
        "app/data/_chat_francisco_salas.txt",
        "app/data/_chat_grettel.txt",
        "app/data/_chat_laura_monestel.txt",
        "app/data/_chat_luisa_alfaro.txt",
        "app/data/_chat_maria_jose_alfaro.txt",
        "app/data/_chat_maritza_ortiz.txt",
        "app/data/_chat_paola_mora_lopez.txt",
        "app/data/_chat_robert_monestel.txt",
    ]
    
    analyzeChunkSizes(
        files_to_analyze,
        r"\[(\d{1,2}/\d{1,2}/\d{2}), \d{1,2}:\d{2}:\d{2}(?:.AM|.PM)?\]",
        "%d/%m/%y",
        "week",
        2
    )

    print("\nTesting getFirstChunkFromFile:")
    try:
        lines = getFirstChunkFromFile(
            files_to_analyze[0],
            r"\[(\d{1,2}/\d{1,2}/\d{2}), \d{1,2}:\d{2}:\d{2}(?:.AM|.PM)?\]",
            "%d/%m/%y",
            "week"
        )
        print(f"First chunk has {len(lines)} lines")
        print(f"Total characters: {sum(len(line) for line in lines)}")
        print(f"\nChunk content:")
        for line in lines:
            print(line.strip())
    except Exception as e:
        print(f"Error: {e}")

    # Test clean_up_string function
    print("\nTesting clean_up_string:")
    test_chunk = "[23/2/25, 14:28:56] David: Ok 👍"
    patterns = {
        "timeStampRegex": r"\[(\d{1,2}/\d{1,2}/\d{2}), \d{1,2}:\d{2}:\d{2}(?:.AM|.PM)?\]"
    }
    cleaned = clean_up_string(test_chunk, patterns)
    print(f"Original: {test_chunk}")
    print(f"Cleaned:  {cleaned}")
    
    # Test with multiple patterns
    test_chunk2 = "[23/2/25, 14:28:56] David: Ok 👍 https://example.com"
    patterns2 = {
        "timeStampRegex": r"\[(\d{1,2}/\d{1,2}/\d{2}), \d{1,2}:\d{2}:\d{2}(?:.AM|.PM)?\]",
        "urlRegex": r"https?://\S+"
    }
    cleaned2 = clean_up_string(test_chunk2, patterns2)
    print(f"Original: {test_chunk2}")
    print(f"Cleaned:  {cleaned2}")

