from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit, join_room, leave_room
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

users = {}

@app.route('/')
def index():
    return index.html

@socketio.on('store_user')
def handle_store_user(data):
    print(f"Received data in store_user: {data}")
    
    # Ensure data is a dictionary
    if isinstance(data, str):
        data = json.loads(data)
    
    username = data.get('name')
    if username:
        if username in users:
            emit('user already exists', {'type': 'user already exists'}, room=request.sid)
        else:
            users[username] = request.sid
            join_room(request.sid)
            print(f"User {username} stored with SID {request.sid}")
    else:
        print("No username found in data")

@socketio.on('start_call')
def handle_start_call(data):
    target = data['target']
    caller = data['name']
    if target in users:
        emit('call_response', {'type': 'call_response', 'data': 'user is ready for call'}, room=request.sid)
    else:
        emit('call_response', {'type': 'call_response', 'data': 'user is not online'}, room=request.sid)

@socketio.on('create_offer')
def handle_create_offer(data):
    target = data['target']
    if target in users:
        emit('offer_received', {
            'type': 'offer_received',
            'name': data['name'],
            'target': target,
            'data': {'sdp': data['data']['sdp']}
        }, room=users[target])
    else:
        print(f"Target {target} not found in users")

@socketio.on('create_answer')
def handle_create_answer(data):
    target = data['target']
    if target in users:
        emit('answer_received', {
            'type': 'answer_received',
            'name': data['name'],
            'target': target,
            'data': data['data']
        }, room=users[target])
    else:
        print(f"Target {target} not found in users")

@socketio.on('ice_candidate')
def handle_ice_candidate(data):
    target = data['target']
    if target in users:
        emit('ice_candidate', {
            'type': 'ice_candidate',
            'name': data['name'],
            'data': {
                'sdpMLineIndex': data['data']['sdpMLineIndex'],
                'sdpMid': data['data']['sdpMid'],
                'sdpCandidate': data['data']['sdpCandidate']
            }
        }, room=users[target])
    else:
        print(f"Target {target} not found in users")

if __name__ == '__main__':
    socketio.run(app, host='192.168.1.8', port=5000, debug=True)
