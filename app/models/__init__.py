diff --git a/app/models/__init__.py b/app/models/__init__.py
index 6e9aa4c0af22724ec9382a48d3455ac89f673e38..dfd9b9361c469b8caea64a8470fcbd24699abb47 100644
--- a/app/models/__init__.py
+++ b/app/models/__init__.py
@@ -1,30 +1,30 @@
 """Aggregated model imports with graceful fallbacks."""
 from __future__ import annotations
 
 from .user import User, USERS, USERNAME_TABLE
 from .base_enums import EstadoLicencia
 
 try:  # pragma: no cover - these imports require SQLAlchemy
     from .base import Base
     from .hospital import Hospital
     from .licencia import Licencia, TipoLicencia
     from .usuario import Usuario
 except Exception:  # pragma: no cover
     # Provide lightweight stand-ins when SQLAlchemy isn't available.
-    Base = object  # type: ignore
-    Hospital = object  # type: ignore
-    Licencia = object  # type: ignore
-    TipoLicencia = object  # type: ignore
-    Usuario = object  # type: ignore
+    Base = None  # type: ignore
+    Hospital = None  # type: ignore
+    Licencia = None  # type: ignore
+    TipoLicencia = None  # type: ignore
+    Usuario = None  # type: ignore
 
 __all__ = [
     "Base",
     "Hospital",
     "Licencia",
     "TipoLicencia",
     "EstadoLicencia",
     "Usuario",
     "User",
     "USERS",
     "USERNAME_TABLE",
 ]

