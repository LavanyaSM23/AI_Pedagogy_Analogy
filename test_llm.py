import os
import sys
# Add the current directory to sys.path so we can import services
sys.path.append(os.getcwd())

from services.llm_service import query_llm

print("--- TESTING LLM SERVICE ---")
prompt = "Explain why the sky is blue in 2 sentences."
print(f"PROMPT: {prompt}")

response = query_llm(prompt)
print(f"RESPONSE: {response}")
print("--- TEST COMPLETE ---")
