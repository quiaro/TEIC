import json
import uuid
import os
import asyncio
from typing import List, Dict, Any
from app.utils.chunks import chunkTimeStampedFile, clean_up_string
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.setup.environment import setup
# Call setup to initialize environment
setup()

def generate_test_samples(filepaths: List[str], output_file: str = "test_data.json", 
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

def generate_test_samples_with_questions(queries: List[str], source_filepath: str, destination_filepath: str) -> None:
    """
    Adds test questions to samples in a JSON file.
    
    For each sample in the source file, creates N new samples where N is the length of the queries list.
    Each new sample has the original context plus a query from the list.
    
    Args:
        queries (List[str]): List of queries to add to each sample
        source_filepath (str): Path to the source JSON file containing samples
        destination_filepath (str): Path where to save the output JSON file
    """
    try:
        # Read the source file
        with open(source_filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'samples' not in data:
            raise ValueError("Source file does not contain a 'samples' key")
        
        # Create new samples with queries
        new_samples = []
        for sample in data['samples']:
            sample_id = sample.get('id')
            context = sample.get('context')
            
            if not sample_id or not context:
                print(f"Warning: Sample is missing id or context, skipping: {sample}")
                continue
                
            # Create a new sample for each query
            for i, query in enumerate(queries):
                new_sample = {
                    'id': f"{sample_id}-{i}",
                    'query': query,
                    'context': context
                }
                new_samples.append(new_sample)
        
        # Create the output data structure
        output_data = {
            'samples': new_samples
        }
        
        # Write to the destination file
        with open(destination_filepath, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
            
        print(f"Created {len(new_samples)} samples with test questions in {destination_filepath}")
        
    except FileNotFoundError:
        print(f"Error: Source file not found: {source_filepath}")
    except json.JSONDecodeError:
        print(f"Error: Source file is not valid JSON: {source_filepath}")
    except Exception as e:
        print(f"Unexpected error: {e}")

async def generate_test_samples_with_answers(source_filepath: str, destination_filepath: str) -> None:
    """
    Generates answers for test samples with questions using an LLM.
    
    Reads samples from the source file, generates answers for each sample using an LLM,
    and writes the results to the destination file.
    
    Args:
        source_filepath (str): Path to the source JSON file containing samples with queries
        destination_filepath (str): Path where to save the output JSON file with answers
    """
    try:
        # Read the source file
        with open(source_filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'samples' not in data:
            raise ValueError("Source file does not contain a 'samples' key")
        
        # Process each sample
        samples_with_answers = []
        total_samples = len(data['samples'])
        
        for i, sample in enumerate(data['samples']):
            sample_id = sample.get('id')
            query = sample.get('query')
            context = sample.get('context')
            
            if not sample_id or not query or not context:
                print(f"Warning: Sample is missing required fields, skipping: {sample}")
                continue
            
            # Create a copy of the sample to add the answer
            new_sample = sample.copy()
            
            # Generate answer using LLM
            answer = await generate_answer_from_llm(query, context)
            new_sample['answer'] = answer
            
            samples_with_answers.append(new_sample)
            
            # Print progress
            print(f"Processed {i+1}/{total_samples} samples")
            
            # Add delay between API calls to avoid rate limiting
            if i < total_samples - 1:  # Don't delay after the last sample
                await asyncio.sleep(2)  # second delay between calls
        
        # Create the output data structure
        output_data = {
            'samples': samples_with_answers
        }
        
        # Write to the destination file
        with open(destination_filepath, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
            
        print(f"Created {len(samples_with_answers)} samples with answers in {destination_filepath}")
        
    except FileNotFoundError:
        print(f"Error: Source file not found: {source_filepath}")
    except json.JSONDecodeError:
        print(f"Error: Source file is not valid JSON: {source_filepath}")
    except Exception as e:
        print(f"Unexpected error: {e}")


async def generate_answer_from_llm(query: str, context: str) -> str:
    """
    Generates an answer to a query based on the provided context using an LLM.
    
    Args:
        query (str): The question to answer
        context (str): The context to use for answering the question
        
    Returns:
        str: The generated answer
    """

    ANSWER_PROMPT = """
    Eres un asistente que responde preguntas basándose únicamente en el contexto proporcionado. Tu respuesta debe consistir en una oración, concisa y al punto. Si la información para responder la pregunta no está contenida en el contexto, responde con "No lo sé". No uses conocimiento externo ni hagas suposiciones más allá de lo que está en el contexto.

    Contexto:
    {context}

    Pregunta:
    {query}

    Respuesta:
    """
    
    api_key = os.environ.get("OPENAI_API_KEY")
    model_name = os.environ.get("ANSWERS_LLM")
    
    if not model_name:
        raise ValueError("ANSWERS_LLM environment variable not set")

    prompt_template = ChatPromptTemplate.from_template(ANSWER_PROMPT)
    prompt = prompt_template.format(context=context, query=query)

    try:
        llm = ChatOpenAI(model=model_name, temperature=0.3)
        response = await llm.ainvoke(prompt)
        return response.content

    except Exception as e:
        print(f"Error generating answer with LLM: {e}")
        return "Error generating answer"


if __name__ == "__main__":
    # Example usage
    files_to_process = [
        "app/data/_chat_maritza_ortiz.txt",
    ]
    
    generate_test_samples(files_to_process, "app/test/test_chunks.json")
    
    # Example usage of generate_test_samples_with_questions
    sample_queries = [
        "Qué le gusta hacer a Maritza Ortiz para divertirse?",
        "Qué tipo de cosas le interesan a Maritza Ortiz?",
        # "Qué cosas le gustan a Maritza Ortiz?",
    ]
    
    generate_test_samples_with_questions(sample_queries, "app/test/test_samples.json", "app/test/test_chunks_with_questions.json")
    
    # Example usage of generate_test_samples_with_answers
    asyncio.run(generate_test_samples_with_answers("app/test/test_chunks_with_questions.json", "app/test/test_chunks_with_answers.json"))