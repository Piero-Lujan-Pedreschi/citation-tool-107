from flask import Flask, request, jsonify
from flask_cors import CORS
import boto3
import json
import os
from dotenv import load_dotenv
import hashlib
import uuid
from datetime import datetime
import jwt

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
You're a friendly peer tutor who helps students talk through their ideas and turn them into clear, structured outlines for essays, speeches, or assignments. You make the process feel easy, safe, and step-by-step — even if they’re stuck or unsure.

Your style is:
- Warm, encouraging, and patient
- Simple and clear language, avoiding jargon
- Conversational and interactive: always ask a question after your response to invite more input
- Adapt your responses for accessibility needs if mentioned:
  - ADHD: Keep prompts short and include brief summaries
  - Dyslexia: Use simple sentences and break information into smaller chunks
  - ESL: Use plain English, avoid idioms
  - Anxiety: Provide gentle reassurance and reduce pressure

You will use the search results below to guide your responses about outline structure, feedback, and academic expectations.

Search Results:
\"\"\"
$search_results$
\"\"\"

TASK:

Step 1: Check the user input.

- If the user has NOT provided a clear topic or just says they don't know what to write about:
  • Offer 2 3 simple, relatable topic ideas across different categories.
  • Use very casual language, e.g., "Here are a few ideas to get you started..."
  • End by asking: "Do any of these sound interesting? Or want to tell me a little about something you're curious about?"

- If the user HAS provided a topic but no thesis/main point:
  • Ask them gently: "Great! What's your main point or argument about this topic? Think of it like your thesis."
  • Offer encouragement if they seem unsure.

- If the user has a thesis but no supporting points:
  • Ask: "Awesome! Now, what are 2 or 3 main reasons or points that support your thesis?"
  • Keep it conversational, e.g., "No worries if you're not sure—just try your best!"

- If the user has topic, thesis, and supporting points:
  • Generate a clear, full-sentence outline with this structure:

I. Introduction  
   - Hook  
   - Thesis Statement  

II. Main Point 1  
   - Explanation  
   - Example or Evidence  

III. Main Point 2  
   - Explanation  
   - Example or Evidence  

IV. Main Point 3  
   - Explanation  
   - Example or Evidence  

V. Conclusion  
   - Summary  
   - Final Insight  

- After generating the outline, ask:  
  "Would you like some tips to improve this outline? Just say yes or no."

- If yes, provide 2 3 short, friendly suggestions to strengthen clarity, flow, or details.

- Always thank the student and encourage them to keep going.

- Log all inputs and outputs (handled by backend).

Remember to keep the conversation short and focused—pause after suggestions to invite the next input.
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

# Initialize DynamoDB
dynamodb = boto3.resource(
    'dynamodb',
    region_name='us-west-2',
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    aws_session_token=os.getenv("AWS_SESSION_TOKEN")
)

# Create tables if they don't exist
def create_tables():
    try:
        # Users table
        users_table = dynamodb.create_table(
            TableName='neuroadapt_users',
            KeySchema=[
                {'AttributeName': 'email', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'email', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        users_table.wait_until_exists()
    except Exception as e:
        pass
    
    try:
        # Chat history table
        chats_table = dynamodb.create_table(
            TableName='neuroadapt_chats',
            KeySchema=[
                {'AttributeName': 'userId', 'KeyType': 'HASH'},
                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'userId', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        chats_table.wait_until_exists()
    except Exception as e:
        pass

create_tables()
users_table = dynamodb.Table('neuroadapt_users')
chats_table = dynamodb.Table('neuroadapt_chats')

# JWT Secret Key
JWT_SECRET = 'neuroadapt_secret_key_2024'

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token(user_data):
    payload = {
        'email': user_data['email'],
        'fullName': user_data['fullName'],
        'exp': datetime.utcnow().timestamp() + 86400  # 24 hours
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

@app.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        full_name = data.get('fullName')
        
        # Check if user already exists
        response = users_table.get_item(Key={'email': email})
        if 'Item' in response:
            return jsonify({'error': 'User already exists'}), 400
        
        # Create new user
        user_id = str(uuid.uuid4())
        hashed_password = hash_password(password)
        
        users_table.put_item(
            Item={
                'userId': user_id,
                'email': email,
                'fullName': full_name,
                'password': hashed_password,
                'createdAt': datetime.utcnow().isoformat()
            }
        )
        
        return jsonify({
            'message': 'Successfully signed up! Welcome to NeuroScript.',
            'token': generate_token({
                'userId': user_id,
                'email': email,
                'fullName': full_name
            }),
            'user': {
                'email': email,
                'fullName': full_name
            }
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/signin', methods=['POST'])
def signin():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        
        # Get user from database
        response = users_table.get_item(Key={'email': email})
        if 'Item' not in response:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        user = response['Item']
        hashed_password = hash_password(password)
        
        if user['password'] != hashed_password:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Generate token
        token = generate_token(user)
        
        return jsonify({
            'token': token,
            'user': {
                'email': user['email'],
                'fullName': user['fullName']
            }
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message')
        user_email = data.get('userEmail')
        
        search_results = retrieve_knowledge_results(kb_id, user_message)
        prompt = build_prompt_from_kb(user_message, search_results)
        response = call_model_with_prompt(prompt)
        
        # Save chat if user is authenticated
        if user_email:
            timestamp = datetime.utcnow().isoformat()
            chats_table.put_item(
                Item={
                    'userId': user_email,
                    'timestamp': timestamp,
                    'userMessage': user_message,
                    'botResponse': response
                }
            )
        
        return jsonify({'response': response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/chat-history/<email>', methods=['GET'])
def get_chat_history(email):
    try:
        response = chats_table.query(
            KeyConditionExpression='userId = :email',
            ExpressionAttributeValues={':email': email},
            ScanIndexForward=True
        )
        
        chats = []
        for item in response['Items']:
            chats.append({
                'timestamp': item['timestamp'],
                'userMessage': item['userMessage'],
                'botResponse': item['botResponse']
            })
        
        return jsonify({'chats': chats})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/delete-chat', methods=['DELETE'])
def delete_chat():
    try:
        data = request.json
        user_email = data.get('userEmail')
        timestamp = data.get('timestamp')
        
        # Delete the specific chat entry
        chats_table.delete_item(
            Key={
                'userId': user_email,
                'timestamp': timestamp
            }
        )
        
        return jsonify({'message': 'Chat deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def home():
    return app.send_static_file('index.html')

if __name__ == '__main__':
    app.run(debug=True, port=3000)