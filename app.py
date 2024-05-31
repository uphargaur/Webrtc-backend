from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from flask_socketio import SocketIO, emit, join_room, leave_room, close_room, rooms, disconnect
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Change this to a random secret key
app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key'  # Change this to a random secret key

jwt = JWTManager(app)
socketio = SocketIO(app, cors_allowed_origins="*")

users = {}

# Example user for login
users_db = {'user1': 'password1'}

@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username', None)
    password = request.json.get('password', None)
    if username not in users_db or users_db[username] != password:
        return jsonify({'msg': 'Bad username or password'}), 401

    access_token = create_access_token(identity=username)
    return jsonify(access_token=access_token)

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')
    for username, user in list(users.items()):
        if user['conn'] == request.sid:
            del users[username]
            break

@socketio.on('message')
def handle_message(message):
    print('Received message:', message)
    data = json.loads(message)
    user = users.get(data.get('name'))

    if data['type'] == 'store_user':
        if user:
            emit('message', json.dumps({"type": "user already exists"}), room=request.sid)
        else:
            print('User stored:', data['name'], "Id :", request.sid)
            users[data['name']] = {'conn': request.sid}
    elif data['type'] == 'start_call':
        user_to_call = users.get(data['target'])
        if user_to_call:
            emit('message', json.dumps({"type": "call_response", "data": "user is ready for call"}), room=request.sid)
        else:
            emit('message', json.dumps({"type": "call_response", "data": "user is not online"}), room=request.sid)
    elif data['type'] == 'create_offer':
        user_to_receive_offer = users.get(data['target'])
        if user_to_receive_offer:
            emit('message', json.dumps({
                "type": "offer_received",
                "name": data['name'],
                "data": {"sdp": data['data']['sdp']}
            }), room=user_to_receive_offer['conn'])
    elif data['type'] == 'create_answer':
        user_to_receive_answer = users.get(data['target'])
        if user_to_receive_answer:
            emit('message', json.dumps({
                "type": "answer_received",
                "name": data['name'],
                "data": {"sdp": data['data']['sdp']}
            }), room=user_to_receive_answer['conn'])
    elif data['type'] == 'ice_candidate':
        user_to_receive_ice_candidate = users.get(data['target'])
        if user_to_receive_ice_candidate:
            emit('message', json.dumps({
                "type": "ice_candidate",
                "name": data['name'],
                "data": {
                    "sdpMLineIndex": data['data']['sdpMLineIndex'],
                    "sdpMid": data['data']['sdpMid'],
                    "sdpCandidate": data['data']['sdpCandidate']
                }
            }), room=user_to_receive_ice_candidate['conn'])

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0',port=8080, debug=True)
