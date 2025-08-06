import boto3
import json
import os
from dotenv import load_dotenv
load_dotenv()


kb_id = os.getenv("KB_ID")

PROMPT_TEMPLATE = """
You are an academic writing assistant. The user is creating a full-sentence working outline for an academic essay.

Use the examples, rubrics, and format guidelines from the search results below to guide your structure and tone.

Search Results:
\"\"\"
$search_results$
\"\"\"

Task:
Using the structure and voice from the examples above, generate a full-sentence working outline on the topic below. If topic is broad, advise user to narrow it down and provide suggestions.

Topic: {{user_input}}

Guidelines:
If the topic is too broad (e.g., "Technology", "Education", "Environment"), respond with a suggestion to narrow it down and provide 2–3 specific subtopics the user could choose from.
If the search results do not contain outline structure examples, use your own knowledge to produce a well-organized full-sentence outline.
If the search results include a rubric, follow it exactly when formatting the outline.
If the topic appears unrelated to the retrieved content, use only the structure (not the content) to guide your response.
"""

history = []

bedrock_client = boto3.client("bedrock-runtime", region_name="us-west-2")
bedrock_agent_client = boto3.client("bedrock-agent-runtime", region_name="us-west-2")

def retrieve_knowledge_results(kb_id: str, query: str) -> str:
    response = bedrock_agent_client.retrieve(
        knowledgeBaseId=kb_id,
        retrievalQuery={"text": query}
    )
     # Extract retrieved text chunks
    results = response.get("retrievalResults", [])
    docs = []

    for item in results:
        content = item.get("content", {}).get("text", "")
        docs.append(content.strip())

    return "\n\n".join(docs)



def build_prompt_from_kb(user_input, search_results):
   prompt = PROMPT_TEMPLATE
   prompt = prompt.replace("{{user_input}}", user_input)
   prompt = prompt.replace("$search_results$", search_results)
   return prompt.strip()

def call_model_with_prompt(prompt):
   payload = {
      "anthropic_version": "bedrock-2023-05-31",
      "max_tokens": 1000,
      "messages": [
         {"role": "user", "content":prompt}
      ]
   }

   response = bedrock_client.invoke_model(
      modelId = "anthropic.claude-3-5-sonnet-20241022-v2:0",
      body = json.dumps(payload)
   )

   body = json.loads(response["body"].read())
   return body["content"][0]["text"]

def chat_loop_with_kb():
   print("Welcome to the chat! Please enter your essay topic below!")
   while True:
      user_input = input("\You: ")
      if user_input.strip().lower() in ["exit", "quit"]:
         break
      
      search_results = retrieve_knowledge_results(kb_id, user_input)
      prompt = build_prompt_from_kb(user_input, search_results)
      response = call_model_with_prompt(prompt)
      print("\nAssistant: ", response)



if __name__ == "__main__":
  chat_loop_with_kb()