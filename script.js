const chatMessages = document.getElementById('chatMessages');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');

// Flask LLM endpoint configuration
const LLM_ENDPOINT = 'http://localhost:5000/chat'; // Local Flask server

function addMessage(content, isUser = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
    
    messageDiv.innerHTML = `
        <div class="avatar">${isUser ? '👨‍🚀' : '🤖'}</div>
        <div class="content">
            <p>${content}</p>
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

async function generateResponse(userMessage) {
    try {
        const response = await fetch(LLM_ENDPOINT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: userMessage,
                context: 'academic_writing_assistant'
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        return data.response || data.message || 'Sorry, I had trouble processing that. Could you try rephrasing?';
    } catch (error) {
        console.error('Error calling LLM endpoint:', error);
        return 'I\'m having trouble connecting right now. Please check that the LLM server is running and try again.';
    }
}

async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message) return;
    
    addMessage(message, true);
    messageInput.value = '';
    
    // Show typing indicator
    addMessage('🤖 Thinking...', false);
    
    try {
        const response = await generateResponse(message);
        // Remove typing indicator
        chatMessages.removeChild(chatMessages.lastChild);
        addMessage(response);
    } catch (error) {
        // Remove typing indicator
        chatMessages.removeChild(chatMessages.lastChild);
        addMessage('Sorry, I encountered an error. Please try again.');
    }
}

async function suggestOutline() {
    const message = "I'd like help structuring my essay outline";
    addMessage(message, true);
    addMessage('🤖 Thinking...', false);
    
    try {
        const response = await generateResponse(message);
        chatMessages.removeChild(chatMessages.lastChild);
        addMessage(response);
    } catch (error) {
        chatMessages.removeChild(chatMessages.lastChild);
        addMessage('Sorry, I encountered an error. Please try again.');
    }
}

async function suggestResearch() {
    const message = "I need guidance on research strategies";
    addMessage(message, true);
    addMessage('🤖 Thinking...', false);
    
    try {
        const response = await generateResponse(message);
        chatMessages.removeChild(chatMessages.lastChild);
        addMessage(response);
    } catch (error) {
        chatMessages.removeChild(chatMessages.lastChild);
        addMessage('Sorry, I encountered an error. Please try again.');
    }
}

async function suggestStructure() {
    const message = "How should I structure my essay?";
    addMessage(message, true);
    addMessage('🤖 Thinking...', false);
    
    try {
        const response = await generateResponse(message);
        chatMessages.removeChild(chatMessages.lastChild);
        addMessage(response);
    } catch (error) {
        chatMessages.removeChild(chatMessages.lastChild);
        addMessage('Sorry, I encountered an error. Please try again.');
    }
}

function clearChat() {
    chatMessages.innerHTML = `
        <div class="message bot-message">
            <div class="avatar">🤖</div>
            <div class="content">
                <p>Ready for a new writing adventure! What topic are you exploring this time?</p>
            </div>
        </div>
    `;
}

sendButton.addEventListener('click', sendMessage);
messageInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

document.getElementById('fileInput').addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        addMessage(`📎 Uploaded: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`, true);
        (async () => {
            addMessage('🤖 Thinking...', false);
            try {
                const response = await generateResponse(`I've uploaded a file called "${file.name}". Can you help me analyze and improve my work?`);
                chatMessages.removeChild(chatMessages.lastChild);
                addMessage(response);
            } catch (error) {
                chatMessages.removeChild(chatMessages.lastChild);
                addMessage('I can see your file upload. How can I help you with your writing today?');
            }
        })();
    }
});

messageInput.focus();