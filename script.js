const chatMessages = document.getElementById('chatMessages');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');

// Flask LLM endpoint configuration
const LLM_ENDPOINT = 'http://localhost:3000/chat'; // Local Flask server

// Typewriter effect function with paragraph support
function typeWriter(element, text, speed = 3) {
    return new Promise((resolve) => {
        // Split text into paragraphs
        const paragraphs = text.split(/\n\n|\n/).filter(p => p.trim().length > 0);
        element.innerHTML = '';
        
        let currentParagraph = 0;
        let currentChar = 0;
        
        function type() {
            if (currentParagraph < paragraphs.length) {
                if (currentChar === 0) {
                    // Create new paragraph element
                    const p = document.createElement('p');
                    element.appendChild(p);
                }
                
                const currentP = element.lastElementChild;
                const paragraph = paragraphs[currentParagraph];
                
                if (currentChar < paragraph.length) {
                    currentP.innerHTML += paragraph.charAt(currentChar);
                    currentChar++;
                    
                    // Check if this paragraph contains subpoints and indent
                    const text = currentP.textContent.trim();
                    if (text.match(/^\s*[a-e]\.|^\s*[1-5]\./)) {
                        currentP.style.marginLeft = '20px';
                    }
                    
                    setTimeout(type, speed);
                } else {
                    // Move to next paragraph
                    currentParagraph++;
                    currentChar = 0;
                    setTimeout(type, speed * 10); // Pause between paragraphs
                }
            } else {
                resolve();
            }
        }
        type();
    });
}

function addMessage(content, isUser = false, useTypewriter = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user-message' : 'assistant-message'}`;
    
    messageDiv.innerHTML = `
        <div class="message-content">
            <div class="avatar">${isUser ? '👨🎓' : '🤖'}</div>
            <div class="text">
            </div>
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    const textElement = messageDiv.querySelector('.text');
    
    if (useTypewriter && !isUser && !content.includes('<span class="thinking-dots">')) {
        // Use typewriter effect for AI responses
        typeWriter(textElement, content, 3);
    } else {
        // Format content into paragraphs for immediate display
        let formattedContent;
        if (content.includes('<span class="thinking-dots">')) {
            formattedContent = `<p>${content}</p>`;
        } else {
            const paragraphs = content.split(/\n\n|\n/).filter(p => p.trim().length > 0);
            formattedContent = paragraphs.map(p => {
                const trimmed = p.trim();
                const isSubpoint = trimmed.match(/^\s*[a-e]\.|^\s*[1-5]\./); 
                return `<p${isSubpoint ? ' style="margin-left: 20px;"' : ''}>${trimmed}</p>`;
            }).join('');
        }
        textElement.innerHTML = formattedContent;
    }
    
    // Update sidebar chat history for authenticated users
    const userEmail = localStorage.getItem('userEmail');
    if (userEmail && isUser) {
        updateChatHistorySidebar(content);
    }
}

async function generateResponse(userMessage) {
    try {
        const userEmail = localStorage.getItem('userEmail');
        // Get selected accessibility needs
        const selectedNeeds = Array.from(document.querySelectorAll('.accessibility-checkbox:checked')).map(cb => cb.value);
        const response = await fetch(LLM_ENDPOINT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: userMessage,
                userEmail: userEmail,
                context: 'academic_writing_assistant',
                accessibilityNeeds: selectedNeeds
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

async function generateResponseWithFile(userMessage, fileContent, fileName) {
    try {
        const userEmail = localStorage.getItem('userEmail');
        const response = await fetch(LLM_ENDPOINT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: userMessage,
                userEmail: userEmail,
                fileContent: fileContent,
                fileName: fileName,
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

    // Keyword detection for satisfaction/goodbye
    const satisfactionKeywords = [
        "i'm done", "i am done", "i'm satisfied", "i am satisfied", "thank you", "thanks", "that's all", "that's it", "i'm finished", "i am finished", "goodbye", "bye"
    ];
    const lowerMessage = message.toLowerCase();
    if (satisfactionKeywords.some(kw => lowerMessage.includes(kw))) {
        addMessage(
          "Great job! You now have a structured outline to build on. Keep working, or export your outline anytime. I’m here if you need more help!",
          false,
          true
        );
        return;
    }

    // Show typing indicator
    addMessage('🦆 Thinking <span class="thinking-dots"><span class="dot">.</span><span class="dot">.</span><span class="dot">.</span></span>', false);

    try {
        const response = await generateResponse(message);
        // Remove typing indicator
        chatMessages.removeChild(chatMessages.lastChild);
        addMessage(response, false, true);
    } catch (error) {
        // Remove typing indicator
        chatMessages.removeChild(chatMessages.lastChild);
        addMessage('Sorry, I encountered an error. Please try again.');
    }
}

async function suggestOutline() {
    const message = "I'd like help structuring my essay outline";
    addMessage(message, true);
    addMessage('🦆 Thinking <span class="thinking-dots"><span class="dot">.</span><span class="dot">.</span><span class="dot">.</span></span>', false);
    
    try {
        const response = await generateResponse(message);
        chatMessages.removeChild(chatMessages.lastChild);
        addMessage(response, false, true);
    } catch (error) {
        chatMessages.removeChild(chatMessages.lastChild);
        addMessage('Sorry, I encountered an error. Please try again.');
    }
}

async function suggestResearch() {
    const message = "I need guidance on research strategies";
    addMessage(message, true);
    addMessage('🦆 Thinking <span class="thinking-dots"><span class="dot">.</span><span class="dot">.</span><span class="dot">.</span></span>', false);
    
    try {
        const response = await generateResponse(message);
        chatMessages.removeChild(chatMessages.lastChild);
        addMessage(response, false, true);
    } catch (error) {
        chatMessages.removeChild(chatMessages.lastChild);
        addMessage('Sorry, I encountered an error. Please try again.');
    }
}

async function suggestStructure() {
    const message = "How should I structure my essay?";
    addMessage(message, true);
    addMessage('🦆 Thinking <span class="thinking-dots"><span class="dot">.</span><span class="dot">.</span><span class="dot">.</span></span>', false);
    
    try {
        const response = await generateResponse(message);
        chatMessages.removeChild(chatMessages.lastChild);
        addMessage(response, false, true);
    } catch (error) {
        chatMessages.removeChild(chatMessages.lastChild);
        addMessage('Sorry, I encountered an error. Please try again.');
    }
}

function clearChat() {
    chatMessages.innerHTML = `
        <div class="message assistant-message">
            <div class="message-content">
                <div class="avatar">🤖</div>
                <div class="text">
                    <p>Welcome to NeuroScript. I’m here to help you turn your thoughts into a clear outline. Ready to get started?</p>
                </div>
            </div>
        </div>
    `;
}

// Start new chat function
function startNewChat() {
    clearChat();
}

// Update chat history sidebar with new message
function updateChatHistorySidebar(userMessage) {
    const userEmail = localStorage.getItem('userEmail');
    if (!userEmail) return;
    
    const historyList = document.getElementById('chatHistoryList');
    if (!historyList) return;
    
    // Show chat history section if hidden
    document.getElementById('chatHistory').style.display = 'block';
    
    // Add new chat item to top
    const historyItem = document.createElement('div');
    historyItem.className = 'chat-history-item';
    historyItem.innerHTML = `
        <div class="chat-preview">${userMessage.substring(0, 40)}...</div>
        <div class="chat-time">${new Date().toLocaleDateString()}</div>
    `;
    
    // Insert at the beginning
    historyList.insertBefore(historyItem, historyList.firstChild);
    
    // Keep only last 10 items
    while (historyList.children.length > 10) {
        historyList.removeChild(historyList.lastChild);
    }
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
        
        const reader = new FileReader();
        reader.onload = async (event) => {
            const fileContent = event.target.result;
            addMessage('🦆 Thinking <span class="thinking-dots"><span class="dot">.</span><span class="dot">.</span><span class="dot">.</span></span>', false);
            
            try {
                const response = await generateResponseWithFile(`Please analyze this document and provide feedback:`, fileContent, file.name);
                chatMessages.removeChild(chatMessages.lastChild);
                addMessage(response, false, true);
            } catch (error) {
                chatMessages.removeChild(chatMessages.lastChild);
                addMessage('Sorry, I had trouble reading the file. Please try again.');
            }
        };
        
        if (file.type === 'text/plain' || file.name.endsWith('.txt')) {
            reader.readAsText(file);
        } else {
            addMessage('Currently only .txt files are supported. Please upload a text file.', false);
        }
    }
});

messageInput.focus();

// Show welcome message when chat loads
window.addEventListener('DOMContentLoaded', function() {
    clearChat();

    // Accessibility dropdown logic
    const dropdownBtn = document.getElementById('accessibilityDropdownBtn');
    const dropdownMenu = document.getElementById('accessibilityDropdownMenu');
    if (dropdownBtn && dropdownMenu) {
        dropdownBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            dropdownMenu.style.display = dropdownMenu.style.display === 'block' ? 'none' : 'block';
        });
        document.addEventListener('click', function(e) {
            if (!dropdownMenu.contains(e.target) && e.target !== dropdownBtn) {
                dropdownMenu.style.display = 'none';
            }
        });
        // Update button text with selected needs
        dropdownMenu.addEventListener('change', function() {
            const selected = Array.from(dropdownMenu.querySelectorAll('.accessibility-checkbox:checked')).map(cb => cb.value);
            dropdownBtn.textContent = selected.length ? selected.join(', ') + ' ▼' : 'Select needs ▼';
        });
    }
});
