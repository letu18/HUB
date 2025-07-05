from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room

app = Flask(__name__)
app.config['SECRET_KEY'] = 'a_very_secret_key'  # Thay bằng một key bí mật thực sự
socketio = SocketIO(app, cors_allowed_origins="*")

# Hàng đợi người dùng đang chờ ghép cặp
waiting_queue = []
# Từ điển lưu phòng của mỗi người dùng
user_rooms = {}

@app.route('/')
def index():
    """Phục vụ trang index.html"""
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    """Xử lý khi có người dùng mới kết nối."""
    print(f'Client connected: {request.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    """Xử lý khi người dùng ngắt kết nối."""
    sid = request.sid
    print(f'Client disconnected: {sid}')
    
    # Nếu người dùng đang trong phòng chat, thông báo cho người còn lại.
    if sid in user_rooms:
        room = user_rooms[sid]
        emit('partner_left', {'message': 'Người lạ đã ngắt kết nối.'}, room=room, include_self=False)
        # Dọn dẹp phòng cho cả hai người dùng
        for user_sid, user_room in list(user_rooms.items()):
            if user_room == room:
                del user_rooms[user_sid]
    
    # Nếu người dùng đang trong hàng đợi, xóa họ khỏi hàng đợi.
    if sid in waiting_queue:
        waiting_queue.remove(sid)

@socketio.on('search_partner')
def handle_search_partner():
    """Xử lý yêu cầu tìm người lạ để chat."""
    sid = request.sid
    print(f'User {sid} is searching for a partner.')
    
    if sid in waiting_queue:
        return  # Đã ở trong hàng đợi rồi

    waiting_queue.append(sid)
    
    if len(waiting_queue) >= 2:
        # Ghép cặp hai người dùng
        user1_sid = waiting_queue.pop(0)
        user2_sid = waiting_queue.pop(0)
        
        room_name = f'room_{user1_sid}_{user2_sid}'
        
        join_room(room_name, sid=user1_sid)
        join_room(room_name, sid=user2_sid)
        
        user_rooms[user1_sid] = room_name
        user_rooms[user2_sid] = room_name
        
        print(f'Paired {user1_sid} and {user2_sid} in room {room_name}')
        
        # Thông báo cho cả hai người dùng đã tìm thấy nhau
        emit('partner_found', {'message': 'Đã kết nối với một người lạ!'}, room=room_name)
    else:
        # Thông báo cho người dùng rằng họ đang ở trong hàng đợi
        emit('waiting_for_partner', {'message': 'Đang tìm một người lạ...'}, room=sid)

@socketio.on('send_message')
def handle_send_message(data):
    """Xử lý tin nhắn gửi đến từ người dùng."""
    sid = request.sid
    if sid in user_rooms:
        room = user_rooms[sid]
        message = data.get('message')
        if message:
            # Gửi tin nhắn cho người còn lại trong phòng
            emit('new_message', {'message': message}, room=room, include_self=False)

@socketio.on('leave_chat')
def handle_leave_chat():
    """Xử lý khi người dùng rời khỏi cuộc trò chuyện."""
    sid = request.sid
    if sid in user_rooms:
        room = user_rooms[sid]
        print(f'User {sid} is leaving room {room}')
        
        # Thông báo cho người còn lại trong phòng
        emit('partner_left', {'message': 'Người lạ đã rời khỏi cuộc trò chuyện.'}, room=room, include_self=False)
        
        # Dọn dẹp phòng cho cả hai người dùng
        for user_sid, user_room in list(user_rooms.items()):
            if user_room == room:
                leave_room(room, sid=user_sid)
                del user_rooms[user_sid]

if __name__ == '__main__':
    socketio.run(app, debug=True)
