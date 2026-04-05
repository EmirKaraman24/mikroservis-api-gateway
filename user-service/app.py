from flask import Flask, request, jsonify
from repository import UserRepository

app = Flask(__name__)
repo = UserRepository()

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route('/users', methods=['POST'])
def create_user():
    data = request.json
    user_id = repo.create_user(data)
    return jsonify({"message": "User created", "id": user_id}), 201

@app.route('/users/<user_id>', methods=['GET'])
def get_user(user_id):
    user = repo.get_user(user_id)
    if user:
        user['_id'] = str(user['_id'])
        return jsonify(user), 200
    return jsonify({"error": "User not found"}), 404

@app.route('/users', methods=['GET'])
def list_users():
    # Basic implementation missing list functionality in repo, but returning empty for now
    return jsonify([]), 200

@app.route('/users/<user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.json
    repo.update_user(user_id, data)
    return jsonify({"message": "User updated"}), 200

@app.route('/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    repo.delete_user(user_id)
    return jsonify({"message": "User deleted"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
