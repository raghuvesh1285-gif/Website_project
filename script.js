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
    const BACKEND_API_URL = "https://website-project-cq53.onrender.com/api/chat"; // Your live URL

    // --- YOUR REQUESTED MODEL MAPPING ---
    const MODEL_MAPPING = {
        atlas: "openai/gpt-oss-120b",
        scholar: "deepseek-ai/deepseek-r1-distill-llama-70b",
        vision: "meta-llama/llama-4-scout-17b-16e-instruct"
    };

    let uploadedImageBase64 = null;

    // --- Event Listeners and Core Functions (No changes needed here) ---
    // (The rest of the JavaScript from the previous response remains exactly the same)
    
    async function sendMessage() {
        const messageText = userInput.value.trim();
        if (messageText === '' && !uploadedImageBase64) return;

        appendMessage(messageText, 'sent', uploadedImageBase64);
        userInput.value = '';
        
        let payload;
        let modelId;

        if (uploadedImageBase64) {
            modelId = MODEL_MAPPING.vision;
            payload = {
                model: modelId,
                messages: [{ role: "user", content: [{ type: "text", text: messageText || "Analyze this image." }, { type: "image_url", image_url: { url: uploadedImageBase64 } }] }]
            };
        } else {
            const selectedModelKey = modelSelector.value;
            if (selectedModelKey === 'vision') {
                appendMessage("Error: Please upload an image to use the Scout (Vision) model.", 'received');
                return;
            }
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
                const err = await response.json();
                throw new Error(err.error || "An unknown error occurred.");
            }

            const data = await response.json();
            updateLastMessage(data);

        } catch (error) {
            updateLastMessage(`Error: ${error.message}`);
        }
        
        removeImage();
    }

    // ... (rest of the helper functions: handleImageSelect, removeImage, appendMessage, updateLastMessage, observer)
});
