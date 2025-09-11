import importlib
import sys
import hashlib


def test_hashlib_fallback():
    """The user module should fall back to hashlib when Werkzeug is unavailable."""
    # Backup original module if present
    original = sys.modules.get("werkzeug.security")
    sys.modules["werkzeug.security"] = None
    try:
        import app.models.user as user_module
        importlib.reload(user_module)
        hashed = user_module.generate_password_hash("secret")
        assert hashed == hashlib.sha256(b"secret").hexdigest()
        assert user_module.check_password_hash(hashed, "secret")
    finally:
        # Restore original module and reload user module to normal state
        if original is not None:
            sys.modules["werkzeug.security"] = original
        else:
            sys.modules.pop("werkzeug.security", None)
        importlib.reload(user_module)
