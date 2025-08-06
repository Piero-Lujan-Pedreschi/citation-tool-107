import boto3
import json

import os
from dotenv import load_dotenv
load_dotenv()

bedrock_client = boto3.client("bedrock-runtime", region_name="us-west-2")
bedrock_agent_client = boto3.client("bedrock-agent-runtime", region_name="us-west-2")

def retrieve_knowledge_results(kb_id: str, user_input: str):
    response = bedrock_agent_client.retrieve(
        knowledgeBaseId=kb_id,
        retrievalQuery={"text": user_input}
    )
     # Extract retrieved text chunks
    results = []
    for doc in response.get("retrievalResults", []):
        content = doc.get("content", {}).get("text", "")
        if content:
            results.append(content.strip())
    return "\n\n".join(results)



def call_bedrock_model_with_kb(user_input: str, search_results: str):
    prompt = f"""
You are an academic writing assistant. The user is creating a full-sentence working outline for an academic essay.

Use the examples, rubrics, and format guidelines from the search results below to guide your structure and tone.

Search Results:
\"\"\"
{search_results}
\"\"\"

Task:
Using the structure and voice from the examples above, generate a full-sentence working outline on the topic below. If topic is broad, advise user to narrow it down and provide suggestions. 

Topic: {user_input}

Guidelines:
- If the topic is too broad (e.g., "Technology", "Education", "Environment"), respond with a suggestion to narrow it down and provide 2–3 specific subtopics the user could choose from.
- If the search results do not contain outline structure examples, use your own knowledge to produce a well-organized full-sentence outline.
- If the search results include a rubric, follow it exactly when formatting the outline.
- If the topic appears unrelated to the retrieved content, use only the structure (not the content) to guide your response.

Return only the full-sentence outline.
"""

    payload = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1000,
        "messages": [{"role": "user", "content": prompt}]
    }

    response = bedrock_client.invoke_model(
        modelId="anthropic.claude-3-5-sonnet-20241022-v2:0",
        body=json.dumps(payload)
    )

    response_body = json.loads(response["body"].read())
    return response_body["content"][0]["text"]


# def call_bedrock_model_with_streaming(message: str):

#   payload = json.dumps({
#     "anthropic_version": "bedrock-2023-05-31",
#     "max_tokens": 4000,
#     "messages": [
#       {
#         "role": "user",
#         "content": message
#       }
#     ]
#   })

#   response = client.invoke_model_with_response_stream(
#     modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
#     body=payload
#   )

#   stream = response.get('body')

#   for event in stream:
#     chunk = event.get('chunk')
#     if not chunk:
#       continue

#     chunk_data = json.loads(chunk.get('bytes').decode())
#     if chunk_data.get("type") == "content_block_delta":
#       delta = chunk_data.get("delta", {})
#       text = delta.get("text")
#       if text:
#         print(text, end='', flush=True)


def main():
  kb_id = os.getenv("KB_ID")
  user_input = "What is the capital of France?"

  search_results = retrieve_knowledge_results(kb_id, user_input)

  print(call_bedrock_model_with_kb(user_input, search_results))

#   call_bedrock_model_with_streaming('\n\nHuman: what is the capital of the United States\n\nAssistant:')


if __name__ == "__main__":
  main()