diff --git a/app/models/user.py b/app/models/user.py
index 1de4e304cf992cf527af45650ec98184545bb63c..59edce8fc18aa6de1cb50b693f44c6b9dad39bf3 100644
--- a/app/models/user.py
+++ b/app/models/user.py
@@ -1,38 +1,59 @@
+"""User model used by the minimal test application.
+
+This module intentionally keeps the implementation extremely small while still
+providing a couple of conveniences used throughout the tests:
+
+* Passwords are always stored hashed using Werkzeug when available or a small
+  hashlib based fallback when it isn't.
+* ``User.create`` automatically registers newly created users in the in-memory
+  ``USERS`` and ``USERNAME_TABLE`` registries so both remain consistent.
+"""
+
 from dataclasses import dataclass
+from typing import Dict
 
 try:
     from werkzeug.security import check_password_hash, generate_password_hash
 except Exception:  # pragma: no cover - executed when Werkzeug isn't installed
     import hashlib
 
     def generate_password_hash(password: str) -> str:
         return hashlib.sha256(password.encode()).hexdigest()
 
     def check_password_hash(pwhash: str, password: str) -> bool:
         return pwhash == hashlib.sha256(password.encode()).hexdigest()
 
 
 @dataclass
 class User:
     """Simple user model without external dependencies."""
 
     id: int
     username: str
     password_hash: str
 
     @classmethod
     def create(cls, id: int, username: str, password: str) -> "User":
-        """Factory method to create users with a hashed password."""
-        return cls(id=id, username=username, password_hash=generate_password_hash(password))
+        """Factory method to create users with a hashed password.
+
+        The created user is also stored in the global ``USERS`` dictionary and
+        its username mapped in ``USERNAME_TABLE`` so both registries remain
+        synchronised.
+        """
+        user = cls(id=id, username=username, password_hash=generate_password_hash(password))
+        USERS[id] = user
+        USERNAME_TABLE[username] = user
+        return user
 
     def check_password(self, password: str) -> bool:
         return check_password_hash(self.password_hash, password)
 
 
-# In-memory user store
-USERS = {
-    1: User.create(id=1, username="admin", password="admin"),
-}
-USERNAME_TABLE = {u.username: u for u in USERS.values()}
+# In-memory user store. ``User.create`` keeps these dictionaries synchronised.
+USERS: Dict[int, User] = {}
+USERNAME_TABLE: Dict[str, User] = {}
+
+# Default administrative user
+User.create(id=1, username="admin", password="admin")
 
 __all__ = ["User", "USERS", "USERNAME_TABLE"]
