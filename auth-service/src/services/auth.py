import jwt
import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class AuthService:
    """
    OOP Login Class for the Authentication Microservice.
    Handles user login, registration, and token generation.
    """
    
    def __init__(self, db_client=None):
        """
        Initialize the AuthService.
        :param db_client: Database client for user operations.
        """
        self.db = db_client if db_client is not None else {}
        self.secret_key = "super-secret-key"
        
    def login(self, username, password):
        """
        Authenticate a user with username and password.
        Returns a token if successful.
        """
        user = self.db.get(username)
        if not user:
            return None
            
        if not check_password_hash(user['password'], password):
            return None
            
        payload = {
            'username': username,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
        
    def register(self, username, email, password):
        """
        Register a new user to the system.
        """
        if username in self.db:
            return False
            
        self.db[username] = {
            'email': email,
            'password': generate_password_hash(password)
        }
        return True
        
    def verify_token(self, token):
        """
        Verify an authentication token.
        """
        try:
            jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return True
        except Exception:
            return False
