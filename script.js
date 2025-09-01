document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Elements ---
    const sendBtn = document.getElementById('sendBtn');
    const userInput = document.getElementById('userInput');
    const chatBody = document.querySelector('.chat-body');
    const modelSelector = document.getElementById('model-selector');
    const imageUploadInput = document.getElementById('image-upload');
    const imagePreviewContainer = document.getElementById('image-preview-container');
    const previewImg = document.getElementById('preview-img');
    const removeImgBtn = document.getElementById('remove-img-btn');

    // --- CRITICAL: YOUR LIVE BACKEND URL ---
    // This MUST be your real URL from Render, not a placeholder.
    const BACKEND_API_URL = "https://website-project-cq53.onrender.com/api/chat";

    // --- MODEL MAPPING ---
    const MODEL_MAPPING = {
        "pHi-2-2b": "openai/gpt-oss-120b",
        "Lfsscp-120b": "meta-llama/llama-4-scout-17b-16e-instruct"
    };

    let uploadedImageBase64 = null;

    // --- Event Listeners ---
    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } });
    imageUploadInput.addEventListener('change', handleImageSelect);
    removeImgBtn.addEventListener('click', removeImage);

    async function sendMessage() {
        const messageText = userInput.value.trim();
        if (messageText === '' && !uploadedImageBase64) return;

        appendMessage(messageText, 'sent', uploadedImageBase64);
        userInput.value = '';
        
        let payload;
        let modelId;

        if (uploadedImageBase64) {
            modelId = MODEL_MAPPING["Lfsscp-120b"];
            payload = {
                model: modelId,
                messages: [{ role: "user", content: [{ type: "text", text: messageText || "Analyze this image." }, { type: "image_url", image_url: { url: uploadedImageBase64 } }] }]
            };
        } else {
            const selectedModelKey = modelSelector.value;
            modelId = MODEL_MAPPING[selectedModelKey];
            payload = {
                model: modelId,
                messages: [{ role: "system", content: "You are an expert AI assistant for ISC and ICSE students." }, { role: "user", content: messageText }]
            };
        }

        appendMessage("...", 'received', null, true);

        try {
            // Check if the URL is still a placeholder
            if (BACKEND_API_URL.includes("your-app-name")) {
                throw new Error("Backend URL is not configured. Please set the correct URL in script.js.");
            }
            
            const response = await fetch(BACKEND_API_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const errData = await response.json().catch(() => ({ error: "Server returned a non-JSON error response." }));
                const errMsg = errData.error || `HTTP error! Status: ${response.status}`;
                throw new Error(errMsg);
            }

            const data = await response.json();
            // Ensure we access the content correctly from the response
            updateLastMessage(data.content);

        } catch (error) {
            // This is where "Failed to fetch" will be caught
            updateLastMessage(`Error: ${error.message}`);
        }
        
        removeImage();
    }
    
    function handleImageSelect(event) {
        const file = event.target.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = () => {
            uploadedImageBase64 = reader.result;
            previewImg.src = uploadedImageBase64;
            imagePreviewContainer.style.display = 'block';
            modelSelector.value = 'Lfsscp-120b';
        };
        reader.readAsDataURL(file);
    }

    function removeImage() {
        uploadedImageBase64 = null;
        imageUploadInput.value = '';
        imagePreviewContainer.style.display = 'none';
    }

    function appendMessage(text, type, imgSrc = null, isTyping = false) {
        const welcomeMsg = document.querySelector('.welcome-message');
        if (welcomeMsg) welcomeMsg.remove();
        
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', type);
        const p = document.createElement('p');
        
        if (isTyping) {
            p.innerHTML = '● ● ●';
        } else {
            if (imgSrc) {
                const img = document.createElement('img');
                img.src = imgSrc;
                img.style.maxWidth = '200px';
                p.appendChild(img);
            }
            if (text) {
                p.appendChild(document.createTextNode(text));
            }
        }
        
        messageDiv.appendChild(p);
        chatBody.appendChild(messageDiv);
        anime({
            targets: messageDiv,
            translateY: [20, 0],
            opacity: [0, 1],
            duration: 400,
            easing: 'easeOutQuart'
        });
        chatBody.scrollTop = chatBody.scrollHeight;
    }

    function updateLastMessage(newText) {
        const typingIndicator = chatBody.querySelector('.message.received:last-child p');
        if (typingIndicator && typingIndicator.textContent === "● ● ●") {
            typingIndicator.textContent = newText;
        }
    }
});
