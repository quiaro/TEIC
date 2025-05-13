import os
import json
from sentence_transformers import SentenceTransformer
from torch.utils.data import DataLoader
from torch.utils.data import Dataset
from sentence_transformers import InputExample
from sentence_transformers.losses import MatryoshkaLoss, MultipleNegativesRankingLoss
from sentence_transformers.evaluation import InformationRetrievalEvaluator

def fine_tune_model(model_id: str, samples_file: str):
    BATCH_SIZE = 16
    EPOCHS = 10

    model = SentenceTransformer(model_id)

    TRAIN_IDS = ["1", "2", "3", "4", "5", "6", "7"]
    VALIDATION_IDS = ["8", "9", "10"]
    # TEST_IDS = ["11", "12", "13"]

    train_examples = []

    with open("app/test/test_samples.json", "r") as f:
        data = json.load(f)
        samples = data["samples"]

        for sample in samples:
            if sample["id"] in TRAIN_IDS:
                user_input = sample["user_input"]
                for context in sample["reference_contexts"]:
                    train_examples.append(InputExample(texts=[user_input, context]))

    # Create a dataloader for the train examples
    train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=BATCH_SIZE)

    matryoshka_dimensions = [768, 512, 256, 128, 64]
    inner_train_loss = MultipleNegativesRankingLoss(model)
    train_loss = MatryoshkaLoss(
        model, inner_train_loss, matryoshka_dims=matryoshka_dimensions
    )

    with open("app/test/validation_samples.json", "r") as f:
        data = json.load(f)
        queries = data["queries"]
        corpus = data["corpus"]
        relevant_docs = data["relevant_docs"]

    evaluator = InformationRetrievalEvaluator(queries, corpus, relevant_docs)

    warmup_steps = int(len(train_dataloader) * EPOCHS * 0.1)

    # TODO: Fix API change in sentence-transformers
    # AttributeError: 'SentenceTransformer' object has no attribute 'tokenizer'. Did you mean: 'tokenize'?
    model.fit(
        train_objectives=[(train_dataloader, train_loss)],
        epochs=EPOCHS,
        warmup_steps=warmup_steps,
        output_path='app/test/fine_tuned_model',
        show_progress_bar=True,
        evaluator=evaluator,
        evaluation_steps=40
    )


def create_validation_sample_file(qid: str, sample_file: str):
    """
    Transforms a sample file into the evaluator format.
    
    Args:
        qid (str): Query identifier
        sample_file (str): Path to the sample JSON file
        
    Returns:
        None: Writes the transformed data to a new file
    """
    # Read the sample file
    with open(sample_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        samples = data["samples"]
    
    # Create the evaluator format
    evaluator_data = {
        "queries": {},
        "corpus": {},
        "relevant_docs": {}
    }
    
    # Use the first sample's query as the question for the specified qid
    if samples:
        evaluator_data["queries"][qid] = samples[0]["query"]
        
        # Add all contexts to the corpus
        for sample in samples:
            evaluator_data["corpus"][sample["id"]] = sample["context"]
        
        # Add all sample ids as relevant documents for the query
        evaluator_data["relevant_docs"][qid] = [sample["id"] for sample in samples]
    
    # Create the output filename
    output_file = f"{sample_file}-evaluator.json"
    
    # Write the evaluator data to the output file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(evaluator_data, f, indent=2, ensure_ascii=False)


def create_validation_dataset_file(validation_sample_files, output_file):
    """
    Merges multiple evaluator JSON files into a single output file.
    
    Args:
        validation_sample_files (list): List of paths to the input validation sample JSON files
        output_file (str): Path to the output merged JSON file
        
    Returns:
        None: Writes the merged data to the output file
    """
    # Initialize the merged data structure
    merged_data = {
        "queries": {},
        "corpus": {},
        "relevant_docs": {}
    }
    
    # Process each input file
    for file_path in validation_sample_files:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
            # Merge queries
            merged_data["queries"].update(data["queries"])
            
            # Merge corpus
            merged_data["corpus"].update(data["corpus"])
            
            # Merge relevant_docs
            merged_data["relevant_docs"].update(data["relevant_docs"])
    
    # Write the merged data to the output file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(merged_data, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    # create_validation_sample_file("10", "app/test/10_gpt_4_1_mini.json")
    
    # Merge the evaluator files for validation samples
    # create_validation_dataset_file([
    #     "app/test/8_gpt_4_1_mini.json-evaluator.json",
    #     "app/test/9_gpt_4_1_mini.json-evaluator.json",
    #     "app/test/10_gpt_4_1_mini.json-evaluator.json"
    # ], "app/test/validation_samples.json")

    model_id = os.getenv("EMBEDDING_MODEL")
    fine_tune_model(model_id, "app/test/validation_samples.json")