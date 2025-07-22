from datetime import datetime, timedelta, timezone
from jose import jwt
from functools import wraps
from flask import request, jsonify
import jose
import os

SECRET_KEY = os.getenv("SECRET_KEY", "your_default_secret_key")


def encode_token(
    user_id,
):
    payload = {
        "exp": datetime.now(timezone.utc)
        + timedelta(days=0, hours=1),  # Setting the expiration time to an hour past now
        "iat": datetime.now(timezone.utc),  # Issued at
        "sub": str(
            user_id
        ),  # This needs to be a string or the token will be malformed and won't be able to be decoded.
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token


def encode_mechanic_token(mechanic_id):

    payload = {
        "exp": datetime.now(timezone.utc) + timedelta(days=0, hours=3),
        "iat": datetime.now(timezone.utc),
        "sub": str(mechanic_id),
        "role": "mechanic",
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # Look for the token in the Authorization header
        if "Authorization" in request.headers:
            token = request.headers["Authorization"].split(" ")[1]

        if not token:
            return jsonify({"message": "Token is missing!"}), 401

        try:
            # Decode the token
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = data["sub"]  # Fetch the user ID

        except jose.exceptions.ExpiredSignatureError:
            return jsonify({"message": "Token has expired!"}), 401
        except jose.exceptions.JWTError:
            return jsonify({"message": "Invalid token!"}), 401

        return f(user_id, *args, **kwargs)

    return decorated


def mechanic_token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if "Authorization" in request.headers:
            auth_header = request.headers["Authorization"]
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]

        if not token:
            return jsonify({"message": "Token is missing!"}), 401

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            if payload.get("role") != "mechanic":
                return jsonify({"message": "Unauthorized: Not a mechanic token"}), 403
            mechanic_id = payload["sub"]
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token expired!"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid token!"}), 401

        return f(mechanic_id, *args, **kwargs)

    return decorated
