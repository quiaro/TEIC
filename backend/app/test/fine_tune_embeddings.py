import os
import json
# from torch.utils.data import DataLoader
# from torch.utils.data import Dataset
from sentence_transformers import SentenceTransformer, InputExample, SentenceTransformerTrainingArguments, SentenceTransformerTrainer
from sentence_transformers.losses import MultipleNegativesRankingLoss
from sentence_transformers.evaluation import InformationRetrievalEvaluator
from transformers import AutoTokenizer
from datasets import Dataset, load_dataset
from app.setup.environment import setup

# Initialize environment
setup()

class PairDataset(Dataset):
    def __init__(self, raw_dataset):
        self.samples = []
        for item in raw_dataset:
            # Assuming each item has 'user_input' and 'reference' fields
            # Adjust field names if they're different in your actual data
            if 'user_input' in item and 'reference_contexts' in item:
                self.samples.append(InputExample(texts=[item['user_input'], item['reference_contexts']]))
            
    def __len__(self):
        return len(self.samples)
        
    def __getitem__(self, idx):
        return self.samples[idx]


def fine_tune_model(model_id: str):
    BATCH_SIZE = 1
    MAX_STEPS = 8  # 84
    OUTPUT_PATH = "app/test/fine_tuned_model"

    model = SentenceTransformer(model_id)
    tokenizer = AutoTokenizer.from_pretrained(model_id)

    # TRAIN_IDS = ["1", "2", "3", "4", "5", "6", "7"]
    # VALIDATION_IDS = ["8", "9", "10"]
    # TEST_IDS = ["11", "12", "13"]

    # raw_train_dataset = load_dataset("json", data_files={"train": "app/test/test_samples-v2.json"}, split="train[:7]")
    # raw_eval_dataset = load_dataset("json", data_files={"train": "app/test/test_samples-v2.json"}, split="train[7:10]")

    # train_dataset = PairDataset(raw_train_dataset)
    # eval_dataset = PairDataset(raw_eval_dataset)

    # train_examples = [
    #     {
    #         "anchor": "A person on a horse jumps over a broken down airplane.",
    #         "positive": ["A person is outdoors, on a horse.", "There's a broken down airplane on the ground."],
    #         "negative": "A person is at a diner, ordering an omelette.",
    #     },
    #     {
    #         "anchor": "Children smiling and waving at camera",
    #         "positive": ["There are children present", "The children's hands are in the air."],
    #         "negative": "The kids are frowning",
    #     },
    # ]
    # train_dataset = load_dataset("json", data_files={"train": "app/test/test_samples-v2.json"}, split="train[:7]")
    train_dataset = load_dataset("json", data_files={"train": "app/test/test_samples-v3.json"}, split="train")
    # train_dataset = Dataset.from_list(train_dataset)


    print(train_dataset.shape)
    print(train_dataset[0]['anchor'])
    print(train_dataset[0]['positive'])

    print(train_dataset[-1]['anchor'])
    print(train_dataset[-1]['positive'])

    # print(eval_dataset[0]['anchor'])
    # print(eval_dataset[0]['positive'])

    # print(eval_dataset[-1]['anchor'])
    # print(eval_dataset[-1]['positive'])

    # train_examples = []

    # with open("app/test/test_samples.json", "r") as f:
    #     data = json.load(f)
    #     samples = data["samples"]

    #     for sample in samples:
    #         if sample["id"] in TRAIN_IDS:
    #             user_input = sample["user_input"]
    #             for context in sample["reference_contexts"]:
    #                 train_examples.append(InputExample(texts=[user_input, context]))

    # Create a dataloader for the train examples
    # train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=BATCH_SIZE)
    train_loss = MultipleNegativesRankingLoss(model)

    # with open("app/test/validation_samples.json", "r") as f:
    #     data = json.load(f)
    #     queries = data["queries"]
    #     corpus = data["corpus"]
    #     relevant_docs = data["relevant_docs"]

    # evaluator = InformationRetrievalEvaluator(queries, corpus, relevant_docs)

    training_args = SentenceTransformerTrainingArguments(
        output_dir=OUTPUT_PATH,
        overwrite_output_dir=True,
        # eval_strategy="steps",
        # eval_steps=7,
        logging_strategy="steps",
        logging_steps=4,
        save_strategy="steps",
        save_steps=7,
        gradient_accumulation_steps=5,
        learning_rate=2e-4,
        weight_decay=0.01,
        warmup_ratio=0.2,
        lr_scheduler_type="cosine",
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=BATCH_SIZE,
        max_steps=MAX_STEPS,
        logging_dir=f"{OUTPUT_PATH}/logs",
        # eval_on_start=True,
        report_to="wandb"
    )

    trainer = SentenceTransformerTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        # eval_dataset=eval_dataset,
        loss=train_loss,
        # evaluator=evaluator,
        tokenizer=tokenizer,
    )

    trainer.train()


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
    # create_validation_sample_file("1", "app/test/1_gpt_4_1_mini.json")
    for i in range(2, 8):
        create_validation_sample_file(str(i), f"app/test/{i}_gpt_4_1_mini.json")
    
    # Merge the evaluator files for validation samples
    create_validation_dataset_file([
        "app/test/1_gpt_4_1_mini.json-evaluator.json",
        "app/test/2_gpt_4_1_mini.json-evaluator.json",
        "app/test/3_gpt_4_1_mini.json-evaluator.json",
        "app/test/4_gpt_4_1_mini.json-evaluator.json",
        "app/test/5_gpt_4_1_mini.json-evaluator.json",
        "app/test/6_gpt_4_1_mini.json-evaluator.json",
        "app/test/7_gpt_4_1_mini.json-evaluator.json"
    ], "app/test/training_samples.json")

    # model_id = os.getenv("EMBEDDING_MODEL")
    # fine_tune_model(model_id)