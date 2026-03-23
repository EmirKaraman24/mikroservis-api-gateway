from flask import Flask, request, jsonify
from src.services.auth import AuthService

app = Flask(__name__)
# Using a simple dictionary as an in-memory db_client for now
auth_service = AuthService(db_client={})

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200

@app.route('/auth/register', methods=['POST'])
def register():
    """Endpoint to register a new user."""
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password') or not data.get('email'):
        return jsonify({"error": "Missing required fields (username, email, password)"}), 400
        
    success = auth_service.register(data['username'], data['email'], data['password'])
    
    if success:
        return jsonify({"message": "User registered successfully"}), 201
    else:
        return jsonify({"error": "Username already exists"}), 409

@app.route('/auth/login', methods=['POST'])
def login():
    """Endpoint to login and receive a JWT token."""
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"error": "Missing username or password"}), 400
        
    token = auth_service.login(data['username'], data['password'])
    
    if token:
        return jsonify({"token": token}), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
