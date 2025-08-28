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

    // --- IMPORTANT: CONFIGURE YOUR BACKEND URL ---
    // Make sure this is your real, live URL from Render
    const BACKEND_API_URL = "https://website-project-cq53.onrender.com/api/chat";

    // --- SIMPLIFIED MODEL MAPPING ---
    const MODEL_MAPPING = {
        "gpt-oss-120b": "openai/gpt-oss-120b",
        "llama-4-scout": "meta-llama/llama-4-scout-17b-16e-instruct"
    };

    let uploadedImageBase64 = null;

    // --- Event Listeners ---
    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } });
    imageUploadInput.addEventListener('change', handleImageSelect);
    removeImgBtn.addEventListener('click', removeImage);

    // --- Core Functions ---
    async function sendMessage() {
        const messageText = userInput.value.trim();
        if (messageText === '' && !uploadedImageBase64) return;

        appendMessage(messageText, 'sent', uploadedImageBase64);
        userInput.value = '';
        
        let payload;
        let modelId;

        if (uploadedImageBase64) {
            modelId = MODEL_MAPPING["llama-4-scout"];
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
            if (BACKEND_API_URL.includes("your-app-name")) throw new Error("Backend URL not set in script.js");
            
            const response = await fetch(BACKEND_API_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const errData = await response.json();
                const errMsg = errData.error.message || JSON.stringify(errData.error);
                throw new Error(errMsg);
            }

            const data = await response.json();
            updateLastMessage(data);

        } catch (error) {
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
        const welcome = document.querySelector('.welcome-message');
        if(welcome) welcome.remove();

        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${type}`;
        const p = document.createElement('p');
        
        if (isTyping) {
            p.textContent = "● ● ●";
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
        
        msgDiv.appendChild(p);
        chatBody.appendChild(msgDiv);
        chatBody.scrollTop = chatBody.scrollHeight;
    }

    function updateLastMessage(newText) {
        const typingIndicator = chatBody.querySelector('.message.received:last-child p');
        if (typingIndicator && typingIndicator.textContent === "● ● ●") {
            typingIndicator.textContent = newText;
        }
    }
    
    // Animation Observer
    const aosElements = document.querySelectorAll('[data-aos]');
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => { if (entry.isIntersecting) entry.target.classList.add('is-visible'); });
    }, { threshold: 0.1 });
    aosElements.forEach(el => observer.observe(el));
});
