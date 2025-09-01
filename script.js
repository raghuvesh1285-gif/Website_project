document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Elements ---
    const sendBtn = document.getElementById('send-button');
    const userInput = document.getElementById('user-input');
    const chatBody = document.querySelector('.chat-body');
    const modelSelector = document.getElementById('model-select');
    const imageUploadInput = document.getElementById('image-upload-input');
    const imagePreviewContainer = document.getElementById('image-preview-container');
    const previewImg = document.getElementById('preview-img');
    const removeImgBtn = document.getElementById('remove-img-btn');

    // --- CRITICAL: YOUR LIVE BACKEND URL ---
    const BACKEND_API_URL = "https://website-project-cq53.onrender.com/api/chat";

    const MODEL_MAPPING = {
        "gpt-oss-120b": "openai/gpt-oss-120b",
        "llama-4-scout": "meta-llama/llama-4-scout-17b-16e-instruct"
    };

    // --- Event Listeners ---
    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } });
    imageUploadInput.addEventListener('change', handleImageSelect);
    if(removeImgBtn) removeImgBtn.addEventListener('click', removeImage);

    async function sendMessage() {
        const messageText = userInput.value.trim();
        if (messageText === '' && !uploadedImageBase64) return;

        appendMessage(messageText, 'sent', uploadedImageBase64);
        userInput.value = '';
        
        let payload;
        const selectedModelKey = modelSelector.value;
        const modelId = MODEL_MAPPING[selectedModelKey];

        if (uploadedImageBase64) {
            payload = {
                model: MODEL_MAPPING['llama-4-scout'], // Vision model is fixed
                messages: [{ role: "user", content: [{ type: "text", text: messageText || "Analyze this image." }, { type: "image_url", image_url: { url: uploadedImageBase64 } }] }]
            };
        } else {
            payload = {
                model: modelId,
                messages: [{ role: "system", content: "You are an expert AI assistant for ISC and ICSE students." }, { role: "user", content: messageText }]
            };
        }

        appendMessage("...", 'received', null, true);

        try {
            const response = await fetch(BACKEND_API_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await response.json();
            if (!response.ok) throw new Error(data.error || "An unknown server error occurred.");
            
            updateLastMessage(data.content);

        } catch (error) {
            updateLastMessage(`Error: ${error.message}`);
        }
        
        removeImage();
    }
    
    let uploadedImageBase64 = null;
    function handleImageSelect(event) {
        const file = event.target.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = () => {
            uploadedImageBase64 = reader.result;
            previewImg.src = uploadedImageBase64;
            imagePreviewContainer.style.display = 'block';
            modelSelector.value = 'llama-4-scout';
        };
        reader.readAsDataURL(file);
    }

    function removeImage() {
        uploadedImageBase64 = null;
        imageUploadInput.value = '';
        imagePreviewContainer.style.display = 'none';
    }

    function appendMessage(text, type, imgSrc = null, isTyping = false) {
        const welcomeMsg = document.querySelector('.message.welcome');
        if (welcomeMsg) welcomeMsg.remove();
        
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', type);
        const p = document.createElement('p');
        
        if (isTyping) {
            p.innerHTML = '<span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>';
        } else {
            if (imgSrc) {
                const img = document.createElement('img');
                img.src = imgSrc;
                img.style.maxWidth = '200px';
                img.style.borderRadius = '0.75rem';
                img.style.marginBottom = '0.5rem';
                img.style.display = 'block';
                p.appendChild(img);
            }
            if (text) {
                p.appendChild(document.createTextNode(text));
            }
        }
        
        messageDiv.appendChild(p);
        chatBody.appendChild(messageDiv);
        chatBody.scrollTop = chatBody.scrollHeight;
    }

    function updateLastMessage(newText) {
        const typingIndicator = chatBody.querySelector('.message.received:last-child p');
        if (typingIndicator && typingIndicator.querySelector('.typing-dot')) {
            typingIndicator.innerHTML = '';
            typingIndicator.textContent = newText;
        }
    }
});
