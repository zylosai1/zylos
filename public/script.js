document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Elements ---
    const backendUrlInput = document.getElementById('backend-url');
    const connectBackendBtn = document.getElementById('connect-backend');
    const backendStatus = document.getElementById('backend-status');
    const userIdInput = document.getElementById('user-id');
    const connectWsBtn = document.getElementById('connect-ws');
    const disconnectWsBtn = document.getElementById('disconnect-ws');
    const wsStatus = document.getElementById('ws-status');
    const wsLogContent = document.getElementById('ws-log-content');
    const chatView = document.getElementById('chat-view');
    const chatInput = document.getElementById('chat-input-box');
    const sendChatBtn = document.getElementById('send-chat');
    const typingIndicator = document.getElementById('typing-indicator');
    const micBtn = document.getElementById('mic-start-stop');
    const muteBtn = document.getElementById('mic-mute-unmute');
    const audioLevel = document.getElementById('audio-level-indicator');
    const ttsToggle = document.getElementById('tts-on-off');
    const replayBtn = document.getElementById('replay-last-response');
    const downloadAudioBtn = document.getElementById('download-audio');
    const voiceSelect = document.getElementById('voice-select');
    const startListeningBtn = document.getElementById('start-listening');
    const stopListeningBtn = document.getElementById('stop-listening');
    const clearLogsBtn = document.getElementById('clear-logs');
    const clearChatBtn = document.getElementById('clear-chat');
    const debugPanel = document.getElementById('debug-panel');
    const toggleDebugBtn = document.getElementById('toggle-debug-panel');
    const debugLogContent = document.getElementById('debug-log-content');
    const autoScrollToggle = document.getElementById('auto-scroll-logs');

    // --- State Management ---
    const state = {
        backendUrl: '',
        isBackendConnected: false,
        isWsConnected: false,
        ws: null,
        userId: '',
        lastAiResponse: '',
        isRecording: false,
        isMuted: false,
        isContinuousListening: false,
        recognition: null,
        audioContext: null,
        analyser: null,
        micStream: null,
    };

    // --- Sound Effects ---
    const tickSound = new Audio('data:audio/mpeg;base64,SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU4LjI5LjEwMAAAAAAAAAAAAAAA//tAwAAAAAAAAAAAAAAAAAAAAAA');
    const beepSound = new Audio('data:audio/mpeg;base64,SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU4LjI5LjEwMAAAAAAAAAAAAAAA//tAwAAAAAAAAAAAAAAAAAAAAAA');

    // --- Logging Utilities ---
    const logTo = (contentEl, message, prefix = '') => {
        const entry = document.createElement('div');
        entry.textContent = `[${new Date().toLocaleTimeString()}] ${prefix}${message}`;
        contentEl.appendChild(entry);
        if (autoScrollToggle.checked) contentEl.scrollTop = contentEl.scrollHeight;
    };
    const logDebug = (message) => logTo(debugLogContent, message);
    const logWs = (message, prefix = '') => logTo(wsLogContent, message, prefix);

    // --- UI Module ---
    const ui = {
        updateBackendStatus: (isConnected) => {
            state.isBackendConnected = isConnected;
            backendStatus.className = `status-indicator ${isConnected ? 'online' : 'offline'}`;
            logDebug(`Backend status updated: ${isConnected ? 'Online' : 'Offline'}`);
            [connectWsBtn, userIdInput, chatInput, sendChatBtn].forEach(el => el.disabled = !isConnected);
        },
        updateWsStatus: (isConnected) => {
            state.isWsConnected = isConnected;
            wsStatus.className = `status-indicator ${isConnected ? 'online' : 'offline'}`;
            logDebug(`WebSocket status updated: ${isConnected ? 'Online' : 'Offline'}`);
            [disconnectWsBtn, micBtn, muteBtn, startListeningBtn].forEach(el => el.disabled = !isConnected);
            connectWsBtn.disabled = isConnected;
        },
        addChatMessage: (sender, message) => {
            const bubble = document.createElement('div');
            bubble.classList.add('chat-bubble', sender === 'user' ? 'user-bubble' : 'ai-bubble');
            bubble.textContent = message;
            chatView.appendChild(bubble);
            chatView.scrollTop = chatView.scrollHeight;
            if (sender === 'ai') state.lastAiResponse = message;
            ui.saveChatHistory();
        },
        toggleTypingIndicator: (show) => {
            typingIndicator.style.display = show ? 'block' : 'none';
        },
        saveChatHistory: () => {
            const messages = Array.from(chatView.children).map(bubble => ({
                sender: bubble.classList.contains('user-bubble') ? 'user' : 'ai',
                message: bubble.textContent
            })).slice(-20);
            localStorage.setItem('zylosChatHistory', JSON.stringify(messages));
        },
        loadChatHistory: () => {
            const history = JSON.parse(localStorage.getItem('zylosChatHistory') || '[]');
            history.forEach(item => ui.addChatMessage(item.sender, item.message));
        },
        setRecordingState: (isRecording) => {
            state.isRecording = isRecording;
            micBtn.innerHTML = isRecording ? '<i class="fas fa-stop"></i>' : '<i class="fas fa-microphone"></i>';
            micBtn.classList.toggle('recording', isRecording);
        }
    };

    // --- API Module ---
    const api = {
        healthCheck: async () => {
            if (!backendUrlInput.value) {
                alert('Backend URL cannot be empty.');
                return;
            }
            state.backendUrl = backendUrlInput.value.replace(/^(https?:\/\/)|(\/)$/g, '');
            logDebug(`Connecting to backend at: ${state.backendUrl}`);
            try {
                const response = await fetch(`http://${state.backendUrl}/api/health`);
                if (response.ok) {
                    ui.updateBackendStatus(true);
                    alert('Backend connected successfully!');
                } else {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
            } catch (error) {
                ui.updateBackendStatus(false);
                logDebug(`Health check failed: ${error.message}`);
                alert('Failed to connect to backend.');
            }
        },
        sendChatMessage: async (message) => {
            if (!state.isBackendConnected) return;
            ui.toggleTypingIndicator(true);
            try {
                const response = await fetch(`http://${state.backendUrl}/api/chat/send`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text: message }),
                });
                const data = await response.json();
                if (!response.ok) throw new Error(data.detail || 'API Error');
                ui.addChatMessage('ai', data.text);
                if (ttsToggle.checked) voiceOutput.speak(data.text);
            } catch (error) {
                logDebug(`Chat send error: ${error.message}`);
                ui.addChatMessage('ai', `Error: ${error.message}`);
            } finally {
                ui.toggleTypingIndicator(false);
            }
        },
    };

    // --- WebSocket Module ---
    const wsManager = {
        connect: () => {
            state.userId = userIdInput.value;
            if (!state.userId) {
                alert('User ID cannot be empty.');
                return;
            }
            const wsUrl = `ws://${state.backendUrl}/ws/${state.userId}`;
            logDebug(`Connecting to WebSocket: ${wsUrl}`);
            state.ws = new WebSocket(wsUrl);

            state.ws.onopen = () => {
                ui.updateWsStatus(true);
                logWs('WebSocket Connected.');
            };
            state.ws.onmessage = (event) => {
                logDebug(`WS recv: ${event.data}`);
                logWs(event.data, 'RECV: ');
                const data = JSON.parse(event.data);
                if (data.text) {
                    ui.addChatMessage('ai', data.text);
                    if (ttsToggle.checked) voiceOutput.speak(data.text);
                }
            };
            state.ws.onclose = () => {
                ui.updateWsStatus(false);
                logWs('WebSocket Disconnected.');
            };
            state.ws.onerror = (error) => {
                logDebug(`WebSocket error: ${error.message || 'Unknown error'}`);
                logWs(`ERROR: ${error.message || 'Unknown error'}`);
            };
        },
        disconnect: () => {
            if (state.ws) {
                state.ws.close();
            }
        },
    };

    // --- Chat Module ---
    const chat = {
        send: (message, fromInput = true) => {
            const text = message || chatInput.value.trim();
            if (!text) return;

            ui.addChatMessage('user', text);

            if (state.isWsConnected) {
                const payload = JSON.stringify({ text: text });
                state.ws.send(payload);
                logDebug(`WS sent: ${payload}`);
                logWs(payload, 'SENT: ');
            } else {
                api.sendChatMessage(text);
            }
            if (fromInput) chatInput.value = '';
        },
    };

    // --- Voice Control Module ---
    const voiceControl = {
        init: () => {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (SpeechRecognition) {
                state.recognition = new SpeechRecognition();
                state.recognition.continuous = false;
                state.recognition.interimResults = false;
                state.recognition.onresult = (event) => {
                    const transcript = event.results[0][0].transcript;
                    logDebug(`Speech recognized: ${transcript}`);
                    chat.send(transcript, false);
                };
                state.recognition.onend = () => {
                    if (state.isContinuousListening) {
                        state.recognition.start();
                    } else {
                        voiceControl.stopRecording();
                    }
                };
                state.recognition.onerror = (event) => {
                    logDebug(`Speech recognition error: ${event.error}`);
                    if(state.isRecording) voiceControl.stopRecording();
                };
            } else {
                [micBtn, startListeningBtn, muteBtn].forEach(el => el.disabled = true);
                alert('Speech Recognition API not supported in this browser.');
            }
        },
        toggleRecording: () => {
            if (state.isRecording) {
                voiceControl.stopRecording();
            } else {
                voiceControl.startRecording();
            }
        },
        startRecording: () => {
            if (!state.recognition || state.isRecording) return;
            ui.setRecordingState(true);
            tickSound.play();
            try {
                state.recognition.start();
                voiceControl.startVisualizer();
                logDebug('Microphone recording started.');
            } catch(e) {
                logDebug(`Error starting recognition: ${e.message}`);
                ui.setRecordingState(false);
            }
        },
        stopRecording: () => {
            if (!state.recognition || !state.isRecording) return;
            ui.setRecordingState(false);
            beepSound.play();
            state.recognition.stop();
            voiceControl.stopVisualizer();
            logDebug('Microphone recording stopped.');
        },
        startVisualizer: async () => {
            try {
                if (!state.micStream) {
                    state.micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
                }
                if (!state.audioContext) {
                    state.audioContext = new (window.AudioContext || window.webkitAudioContext)();
                    state.analyser = state.audioContext.createAnalyser();
                    const source = state.audioContext.createMediaStreamSource(state.micStream);
                    source.connect(state.analyser);
                    state.analyser.fftSize = 256;
                }
                const dataArray = new Uint8Array(state.analyser.frequencyBinCount);
                const draw = () => {
                    if (!state.isRecording) {
                        audioLevel.style.width = '0%';
                        return;
                    }
                    requestAnimationFrame(draw);
                    state.analyser.getByteFrequencyData(dataArray);
                    const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
                    audioLevel.style.width = `${Math.min(100, (average / 128) * 100)}%`;
                };
                draw();
            } catch (err) {
                logDebug(`Audio visualizer error: ${err.message}`);
                alert('Could not access microphone. Please allow microphone permissions.');
            }
        },
        stopVisualizer: () => {
            audioLevel.style.width = '0%';
        },
        toggleContinuousListening: (start) => {
            state.isContinuousListening = start;
            if (start) {
                startListeningBtn.disabled = true;
                stopListeningBtn.disabled = false;
                voiceControl.startRecording();
            } else {
                startListeningBtn.disabled = false;
                stopListeningBtn.disabled = true;
                if(state.isRecording) voiceControl.stopRecording();
            }
            logDebug(`Continuous listening: ${start ? 'ON' : 'OFF'}`);
        }
    };

    // --- Voice Output (TTS) Module ---
    const voiceOutput = {
        speak: (text) => {
            if (!ttsToggle.checked || !text) return;
            try {
                const utterance = new SpeechSynthesisUtterance(text);
                const voices = window.speechSynthesis.getVoices();
                const selectedVoiceName = voiceSelect.value;
                if (selectedVoiceName === 'male') utterance.voice = voices.find(v => v.name.includes('Google US English') || v.name.includes('David') || v.name.includes('Male'));
                if (selectedVoiceName === 'female') utterance.voice = voices.find(v => v.name.includes('Google UK English Female') || v.name.includes('Zira') || v.name.includes('Female'));
                // 'robotic' will likely use a default voice, which can sound robotic.
                window.speechSynthesis.speak(utterance);
                logDebug(`TTS speaking: "${text}"`);
            } catch (e) {
                logDebug(`TTS Error: ${e.message}`);
            }
        },
        replay: () => {
            if (state.lastAiResponse) {
                voiceOutput.speak(state.lastAiResponse);
            } else {
                alert('No previous AI response to replay.');
            }
        }
    };

    // --- Event Listeners ---
    connectBackendBtn.addEventListener('click', api.healthCheck);
    connectWsBtn.addEventListener('click', wsManager.connect);
    disconnectWsBtn.addEventListener('click', wsManager.disconnect);
    sendChatBtn.addEventListener('click', () => chat.send());
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') chat.send();
    });
    micBtn.addEventListener('click', voiceControl.toggleRecording);
    startListeningBtn.addEventListener('click', () => voiceControl.toggleContinuousListening(true));
    stopListeningBtn.addEventListener('click', () => voiceControl.toggleContinuousListening(false));
    replayBtn.addEventListener('click', voiceOutput.replay);

    clearLogsBtn.addEventListener('click', () => {
        wsLogContent.innerHTML = '';
        debugLogContent.innerHTML = '';
        logDebug('Logs cleared.');
    });
    clearChatBtn.addEventListener('click', () => {
        chatView.innerHTML = '';
        localStorage.removeItem('zylosChatHistory');
        logDebug('Chat history cleared.');
    });
    toggleDebugBtn.addEventListener('click', () => {
        const isCollapsed = debugPanel.classList.toggle('collapsed');
        toggleDebugBtn.querySelector('i').className = isCollapsed ? 'fas fa-chevron-down' : 'fas fa-chevron-up';
    });

    // --- Initialization ---
    const init = () => {
        ui.updateBackendStatus(false);
        ui.updateWsStatus(false);
        stopListeningBtn.disabled = true;
        downloadAudioBtn.disabled = true; // Feature removed
        voiceControl.init();
        ui.loadChatHistory();
        debugPanel.classList.add('collapsed');
        toggleDebugBtn.querySelector('i').className = 'fas fa-chevron-down';
        logDebug('Zylos Control Portal Initialized.');
    };

    init();
});
