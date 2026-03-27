from flask import Flask, jsonify, request

app = Flask(__name__)

# Basic in-memory storage for demonstration purposes instead of full DB setup
messages_db = {}
message_counter = 1

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route('/messages', methods=['POST'])
def send_message():
    global message_counter
    data = request.json
    messages_db[str(message_counter)] = data
    message_counter += 1
    return jsonify({"message": "Message sent"}), 201

@app.route('/messages', methods=['GET'])
def get_messages():
    return jsonify(list(messages_db.values())), 200

@app.route('/messages/<msg_id>', methods=['DELETE'])
def delete_message(msg_id):
    if msg_id in messages_db:
        del messages_db[msg_id]
    return jsonify({"message": "Message deleted"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
