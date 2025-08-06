from flask import Flask, request, jsonify
from flask_cors import CORS
import boto3
import json
import os
from dotenv import load_dotenv

# Load .env file from current directory
load_dotenv(dotenv_path='.env')

# Fallback: Set environment variables directly if .env fails
if not os.getenv("KB_ID"):
    os.environ["KB_ID"] = "ZLOXX0ZTQP"
    os.environ["AWS_ACCESS_KEY_ID"] = "ASIAVWQU5XXZ3FFK5ATX"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "sUJ57uPRA0S3yux5+kexbIiMJytp7E00nR/pPoyf"
    os.environ["AWS_SESSION_TOKEN"] = "IQoJb3JpZ2luX2VjEEcaCXVzLXdlc3QtMiJHMEUCIQDgwRl/CKig7rhhYIgCSodNFigQfyuxof3P67a5Oxg11gIgUy5GuC7JEIiSCRLdyfGmvrtpc3fNfr/EN3/iCRY2jBoqlgMIgP//////////ARAAGgwzOTE5NTk2NTc5NzEiDJFqF4ks3NpihpEJbSrqAuQEfx/Hm6AgDg2Wd1iUPtGFjasxN1Ro+g7+ySYJWdg1Bx5jg91YxSuJsh9qie5mtjT60L9N6HEYlf3ddTyCId+I0tW33XJaF4LTfJGH+j0i0l1dcWV1I/TRdk5wTD7EVM2mlHYhd/gYXuQqS5R9u0WV+oWm1SJipLjX9zvh7zw0WziGo9IgdF0VkqVHgK2NFwpNUtrLKXd0+94TqWgdy3Z/CCDzsv/aDOESF8ZVRnkTttDJyAfRZqxu8cPJQXjTURMezQQ29UX6npnVh3ZerInI7Jhvuyd9uxyf7cehlq4tCmj7fxMAGQbeyy6pxOj9NjQ4P6CbWxEJsRtno6GFzRNAWfDH7BJYkFfNpMYJS5Ks7PhhZfltuMRHfIO6Afa9/iC6kLiuW/41jp11JFWgJEPVbc4kvLqadQRJfxCKPiwJ7hyiu1YTtzmMNTND6J6yiTbJ6Oj98gc/mDoYlpTPZ5YI0prMo43rQCeWMMSwz8QGOqYB663X92X+tMs/RCUe2Fky9QA+jD+CUvVU0Gv29npSF5I7sE2zNxXpgAIE4rL6Fg2kx3koTBdNmJ6oTzs8JCCudMI05S97zKwrrXHkEA2u1mHrjqrze2HbHlSPWDYwD17wbgAtSy/gD9RhWC1fJ2bliuttJm5zPD0qjPODW8l6JSM2cZRGAHNs3AaBvSxsr5eV3PYk7AdPesnm5NJdzeangkKK9ZpS/A=="
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_SESSION_TOKEN = os.getenv("AWS_SESSION_TOKEN")
print(f"Debug - AWS credentials loaded: {AWS_ACCESS_KEY_ID}, {AWS_SECRET_ACCESS_KEY}, {AWS_SESSION_TOKEN}") 
app = Flask(__name__)
CORS(app)

kb_id = os.getenv("KB_ID")
print(f"Debug - KB_ID loaded: {kb_id}")

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

# Initialize AWS clients with explicit credentials
bedrock_client = boto3.client(
    "bedrock-runtime", 
    region_name="us-west-2",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    aws_session_token=os.getenv("AWS_SESSION_TOKEN")
)


print(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN)
bedrock_agent_client = boto3.client(
    "bedrock-agent-runtime", 
    region_name="us-west-2",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    aws_session_token=os.getenv("AWS_SESSION_TOKEN")
)

def retrieve_knowledge_results(kb_id: str, query: str) -> str:
    response = bedrock_agent_client.retrieve(
        knowledgeBaseId=kb_id,
        retrievalQuery={"text": query}
    )
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
        "messages": [{"role": "user", "content": prompt}]
    }
    response = bedrock_client.invoke_model(
        modelId="anthropic.claude-3-5-sonnet-20241022-v2:0",
        body=json.dumps(payload)
    )
    response_body = json.loads(response['body'].read())
    return response_body['content'][0]['text']

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message')
        
        search_results = retrieve_knowledge_results(kb_id, user_message)
        prompt = build_prompt_from_kb(user_message, search_results)
        response = call_model_with_prompt(prompt)
        
        return jsonify({'response': response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)