diff --git a/app/models/user.py b/app/models/user.py
index 9159a8b584e759ba75a71e6ba291c5ff149b1e9a..2ce8b6088397a1b0e46455d134643926a231c15e 100644
--- a/app/models/user.py
+++ b/app/models/user.py
@@ -1,28 +1,40 @@
+"""Very small user model used for authentication tests.
+
+The original project relied on ``werkzeug.security`` for password hashing, but
+that package is not available in the execution environment.  For testing
+purposes we implement a minimal hashing helper using :mod:`hashlib`.
+"""
+
 from dataclasses import dataclass
-from werkzeug.security import check_password_hash, generate_password_hash
+import hashlib
 
 
 @dataclass
 class User:
     """Simple user model without external dependencies."""
 
     id: int
     username: str
     password_hash: str
 
+    @staticmethod
+    def _hash_password(password: str) -> str:
+        """Return a stable hash for the provided password."""
+        return hashlib.sha256(password.encode("utf-8")).hexdigest()
+
     @classmethod
     def create(cls, id: int, username: str, password: str) -> "User":
         """Factory method to create users with a hashed password."""
-        return cls(id=id, username=username, password_hash=generate_password_hash(password))
+        return cls(id=id, username=username, password_hash=cls._hash_password(password))
 
     def check_password(self, password: str) -> bool:
-        return check_password_hash(self.password_hash, password)
+        return self.password_hash == self._hash_password(password)
 
 
 # In-memory user store
 USERS = {
     1: User.create(id=1, username="admin", password="admin"),
 }
 USERNAME_TABLE = {u.username: u for u in USERS.values()}
 
 __all__ = ["User", "USERS", "USERNAME_TABLE"]
