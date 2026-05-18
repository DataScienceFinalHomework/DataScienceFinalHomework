"""
Test script to process 10 dreams via LLM API
Records time to help set appropriate timeout values
"""
import sys
import os
import json
import asyncio
import aiohttp
import time
import re

sys.path.append(os.path.abspath("../utils"))

from CallLLM import call_llm
from SetupLogging import setup_logging

logger = setup_logging("test_process")

# Prompts
system_prompt = """
# Role
You are a senior expert in Computational Linguistics, Affective Computing, and Oneirology (Dream Science), specializing in extracting structured entity relations, behavioral sequences, and emotional polarity from large-scale unstructured dream narratives.
"""

user_prompt_base = """
# Background
I am conducting a high-throughput study on the topological and emotional features of dream structures. This research requires analyzing multiple dreams simultaneously to calculate entity frequency (Zipf's Law), character interaction networks, sequence mapping (for directed graph networks), and affective distribution (positive vs. nightmare states).

# Input Data Format
You will receive a batch of multiple dream texts. Each dream is wrapped in explicit XML tags with a unique identifier, like this:
<dream id="alta_1"> [Dream text content here] </dream>
<dream id="alta_2"> [Dream text content here] </dream>

# Task
Analyze each dream text in the provided batch independently and execute the following five tasks for each entry:
1. **Named Entity Recognition (NER)**: Extract all significant entities. Categories include: Characters (e.g., "mother", "stranger"), Objects (e.g., "wolf", "key"), Locations (e.g., "forest"), and Natural Phenomena (e.g., "rain").
2. **Global Entity Frequency**: Count the exact total occurrences of *every* unique entity (including characters) within that specific dream.
3. **Character Frequency Isolation**: Isolate entities categorized strictly as **Characters** (human, human-like figures, or personified entities, e.g., "mother", "ghost", "speaking dog") and count their frequencies independently.
4. **Textual Sequence Extraction**: List all entities in the exact order they appear in the reading flow. Record recurring entities multiple times to capture "looping" or "jumping" characteristics.
5. **Sentiment Classification**: Evaluate the overall emotional tone of the dream. Classify it as a boolean value: `true` if it is a positive/neutral-pleasant dream, and `false` if it is a negative dream/nightmare (characterized by fear, anxiety, pursuit, or distress).

# Constraints & Rules (Critical)
1. **Entity Atomization & Lemmatization**: Extract only the core noun in **lowercase** and **singular form** (e.g., "a massive black wolf" -> "wolf", "my mother's old houses" -> "house").
2. **Pronoun Resolution**: Map pronouns ("he", "it", "the beast") back to their specific antecedent entity if clearly identifiable.
3. **Sequence Order**: Follow the strict **Textual Reading Order** from first word to last, not the chronological plot backstory.
4. **Character Definition**: A "Character" is defined as any entity capable of agency, speech, or intentional behavior within the dream context.
5. **Data Consistency**: Ensure that every key in `character_frequency` is also present in `entities_frequency` with the exact same frequency count.
6. **Independent Evaluation**: Do not let the sentiment or entities of one dream cross-contaminate another dream in the batch.
7. **Language**: The entire JSON output (including summaries and entity names) must be in **English**.

# Output Format
Respond ONLY with a valid JSON array containing objects for each dream. Do not include any markdown conversational text outside the code block.

[
  {
    "dream_id": "alta_1",
    "dream_summary": "A concise one-sentence summary of the dream theme.",
    "positive_or_not": true,
    "entities_frequency": {
      "mother": 3,
      "wolf": 2,
      "forest": 1
    },
    "character_frequency": {
      "mother": 3
    },
    "entity_sequence": ["mother", "forest", "wolf", "mother", "wolf", "mother"],
    "metadata": {
      "total_unique_entities": 3,
      "total_unique_characters": 1,
      "sequence_total_length": 6
    }
  }
]

Input Data:
"""

def extract_dream_id(line):
    match = re.search(r'<dream id="([^"]+)">', line)
    return match.group(1) if match else None

def extract_json_from_response(result):
    """Extract JSON array from LLM response that may contain markdown"""
    json_match = re.search(r'\[\s*\{.*\}\s*\]', result, re.DOTALL)
    if json_match:
        return json_match.group(0)
    return result

async def test_batch_processing():
    # Read data
    data_file_path = "../../Datasets/DB_wrapped.xml"
    with open(data_file_path, "r", encoding="utf-8") as f:
        data = f.readlines()

    # Get first 10 dreams
    test_dreams = []
    for line in data[:10]:
        dream_id = extract_dream_id(line)
        if dream_id:
            test_dreams.append((dream_id, line.strip()))

    print(f"Testing with {len(test_dreams)} dreams")
    print(f"Dream IDs: {[d[0] for d in test_dreams]}")

    # Build prompt
    batch_texts = [d[1] for d in test_dreams]
    user_prompt = user_prompt_base + "\n".join(batch_texts)

    # Time the request
    start_time = time.time()

    async with aiohttp.ClientSession() as session:
        result, in_tokens, out_tokens = await call_llm(
            system_prompt,
            user_prompt,
            session,
            logger,
            timeout=180,  # 3 minutes timeout for test
            model_used="deepseek-ai/DeepSeek-V3"
        )

    elapsed_time = time.time() - start_time

    print(f"\n=== Timing Results ===")
    print(f"Total time: {elapsed_time:.2f} seconds")
    print(f"Input tokens: {in_tokens}")
    print(f"Output tokens: {out_tokens}")
    print(f"Time per dream: {elapsed_time/len(test_dreams):.2f} seconds")

    print(f"\n=== Response ===")
    print(f"Result type: {type(result)}")
    print(f"Result length: {len(result) if result else 0}")

    # Try to parse JSON
    if result and not result.startswith(("Error:", "Exception:", "Failed")):
        json_str = extract_json_from_response(result.strip())
        try:
            result_list = json.loads(json_str)
            print(f"\n=== JSON Parse Success ===")
            print(f"Number of results: {len(result_list)}")

            # Validate
            expected_ids = [d[0] for d in test_dreams]
            result_ids = [item.get("dream_id") for item in result_list]
            print(f"Expected IDs: {expected_ids}")
            print(f"Got IDs: {result_ids}")

            if set(result_ids) == set(expected_ids):
                print("✓ IDs match!")
            else:
                print("✗ IDs mismatch!")

            # Save result for inspection
            output_file = "test_result.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result_list, f, ensure_ascii=False, indent=2)
            print(f"\nSaved result to {output_file}")

            # Print first result as sample
            print(f"\n=== Sample Result (first dream) ===")
            print(json.dumps(result_list[0], ensure_ascii=False, indent=2))

        except json.JSONDecodeError as e:
            print(f"\n✗ JSON Parse Failed: {e}")
            print(f"Raw result (first 500 chars):\n{result[:500]}")
    else:
        print(f"\n✗ Error result: {result}")

    return elapsed_time, result

if __name__ == "__main__":
    elapsed, result = asyncio.run(test_batch_processing())

    # Suggest timeout based on test
    suggested_timeout = max(180, int(elapsed * 1.5))
    print(f"\n=== Timeout Recommendation ===")
    print(f"For 10 dreams: use timeout >= {suggested_timeout} seconds")
    print(f"For 5 dreams (batch size): use timeout >= {suggested_timeout//2} seconds")