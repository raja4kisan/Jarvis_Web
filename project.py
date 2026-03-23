from openai import AzureOpenAI
import os
from config import apikey, api_base, api_version, deployment_name

# Initialize Azure OpenAI client
client = AzureOpenAI(
    api_key=apikey,
    api_version=api_version,
    azure_endpoint=api_base
)

try:
    response = client.chat.completions.create(
        model=deployment_name,
        messages=[
            {"role": "system", "content": "You are a professional email writer."},
            {"role": "user", "content": "Dear Hiring Manager,\nI am writing to express my interest in the [position] position at [company]."}
        ],
        max_completion_tokens=300
    )

    print(response)
    print("\n--- Generated Email ---")
    print(response.choices[0].message.content)
except Exception as e:
    print(f"Invalid Request! Error: {e}")


'''
{
  "id": "chatcmpl-8zKczwq7ZTwkGozygrjS6R3Hf1aX5",
  "object": "chat.completion",
  "created": 1709627993,
  "model": "gpt-3.5-turbo-0125",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "there was a young girl named Lily who lived in a small village nestled in the rolling hills of the countryside. Lily was known for her kindness and curiosity, always eager to help others and explore the world around her."
      },
      "logprobs": null,
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 22,
    "completion_tokens": 43,
    "total_tokens": 65
  },
  "system_fingerprint": "fp_2b778c6b35"
}
'''
