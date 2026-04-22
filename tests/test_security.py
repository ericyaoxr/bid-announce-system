from src.core.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_and_verify(self):
        password = "test_password_123"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed)

    def test_wrong_password(self):
        password = "test_password_123"
        hashed = get_password_hash(password)
        assert not verify_password("wrong_password", hashed)

    def test_different_hashes(self):
        password = "test_password_123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        assert hash1 != hash2

    def test_empty_password(self):
        hashed = get_password_hash("")
        assert verify_password("", hashed)


class TestJWT:
    def test_create_and_decode_token(self):
        data = {"sub": "testuser"}
        token = create_access_token(data)
        assert token is not None

        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == "testuser"

    def test_token_expiration(self):
        from datetime import timedelta

        data = {"sub": "testuser"}
        token = create_access_token(data, expires_delta=timedelta(seconds=-1))
        payload = decode_access_token(token)
        assert payload is None

    def test_invalid_token(self):
        payload = decode_access_token("invalid.token.here")
        assert payload is None

    def test_token_with_extra_data(self):
        data = {"sub": "testuser", "role": "admin"}
        token = create_access_token(data)
        payload = decode_access_token(token)
        assert payload["role"] == "admin"
