diff --git a/app/models/user.py b/app/models/user.py
index 1de4e304cf992cf527af45650ec98184545bb63c..7a0600d0fa6c2e9fde55ef649c063ca76dbadcbe 100644
--- a/app/models/user.py
+++ b/app/models/user.py
@@ -1,37 +1,40 @@
 from dataclasses import dataclass
 
 try:
     from werkzeug.security import check_password_hash, generate_password_hash
 except Exception:  # pragma: no cover - executed when Werkzeug isn't installed
     import hashlib
+    import hmac
 
     def generate_password_hash(password: str) -> str:
         return hashlib.sha256(password.encode()).hexdigest()
 
     def check_password_hash(pwhash: str, password: str) -> bool:
-        return pwhash == hashlib.sha256(password.encode()).hexdigest()
+        """Validate a password against its hash using the fallback hasher."""
+        expected = generate_password_hash(password)
+        return hmac.compare_digest(pwhash, expected)
 
 
 @dataclass
 class User:
     """Simple user model without external dependencies."""
 
     id: int
     username: str
     password_hash: str
 
     @classmethod
     def create(cls, id: int, username: str, password: str) -> "User":
         """Factory method to create users with a hashed password."""
         return cls(id=id, username=username, password_hash=generate_password_hash(password))
 
     def check_password(self, password: str) -> bool:
         return check_password_hash(self.password_hash, password)
 
 
 # In-memory user store
 USERS = {
     1: User.create(id=1, username="admin", password="admin"),
 }
 USERNAME_TABLE = {u.username: u for u in USERS.values()}
 
