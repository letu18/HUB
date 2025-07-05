document.addEventListener('DOMContentLoaded', () => {
    // Kết nối tới server Socket.IO
    const socket = io();

    // Lấy các element từ DOM
    const messagesContainer = document.getElementById('messages');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const controlButton = document.getElementById('control-button');
    const statusDiv = document.getElementById('status');

    let chatState = 'idle'; // Trạng thái: idle, waiting, chatting

    // --- Hàm tiện ích ---
    function addMessage(type, text) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', type);
        messageElement.textContent = text;
        messagesContainer.appendChild(messageElement);
        messagesContainer.scrollTop = messagesContainer.scrollHeight; // Tự động cuộn xuống
    }

    function setUIState(state) {
        chatState = state;
        if (state === 'idle') {
            messageInput.disabled = true;
            sendButton.disabled = true;
            controlButton.textContent = 'Tìm người lạ';
            controlButton.className = 'start';
            statusDiv.textContent = 'Sẵn sàng để tìm kiếm.';
        } else if (state === 'waiting') {
            messageInput.disabled = true;
            sendButton.disabled = true;
            controlButton.textContent = 'Dừng tìm kiếm';
            controlButton.className = 'stop';
            statusDiv.textContent = 'Đang tìm một người lạ...';
        } else if (state === 'chatting') {
            messageInput.disabled = false;
            sendButton.disabled = false;
            controlButton.textContent = 'Kết thúc chat';
            controlButton.className = 'stop';
            statusDiv.textContent = 'Đã kết nối! Nói lời chào đi.';
            messageInput.focus();
        }
    }

    // --- Xử lý sự kiện từ người dùng ---
    controlButton.addEventListener('click', () => {
        if (chatState === 'idle') {
            socket.emit('search_partner');
            setUIState('waiting');
        } else {
            socket.emit('leave_chat');
            addMessage('system', 'Bạn đã rời khỏi cuộc trò chuyện.');
            setUIState('idle');
        }
    });

    function sendMessage() {
        const message = messageInput.value.trim();
        if (message && chatState === 'chatting') {
            socket.emit('send_message', { message: message });
            addMessage('sent', message);
            messageInput.value = '';
        }
    }

    sendButton.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    // --- Lắng nghe sự kiện từ Server ---
    socket.on('connect', () => {
        console.log('Connected to server!');
        setUIState('idle');
    });

    socket.on('disconnect', () => {
        console.log('Disconnected from server!');
        addMessage('system', 'Mất kết nối tới server. Vui lòng tải lại trang.');
        setUIState('idle');
    });

    socket.on('waiting_for_partner', (data) => {
        statusDiv.textContent = data.message;
    });

    socket.on('partner_found', (data) => {
        addMessage('system', data.message);
        setUIState('chatting');
    });

    socket.on('new_message', (data) => {
        addMessage('received', data.message);
    });

    socket.on('partner_left', (data) => {
        addMessage('system', data.message);
        setUIState('idle');
    });

    // Khởi tạo UI ban đầu
    setUIState('idle');
});
