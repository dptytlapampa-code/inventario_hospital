diff --git a/app/__init__.py b/app/__init__.py
index 083fadd1c1d3b637fe052d85dd6678465aad400c..1353e589302e317394e63f7135c298b6066789dd 100644
--- a/app/__init__.py
+++ b/app/__init__.py
@@ -9,46 +9,49 @@ from licencias import usuario_con_licencia_activa
 
 
 @dataclass
 class Response:
     status_code: int
     headers: Dict[str, str] = field(default_factory=dict)
 
 
 class SimpleClient:
     def __init__(self, app: SimpleApp) -> None:
         self.app = app
 
     def post(self, path: str, data: Optional[Dict[str, Any]] = None, follow_redirects: bool = False) -> Response:
         data = data or {}
         if path == "/auth/login":
             user = USERNAME_TABLE.get(data.get("username"))
             if user and user.check_password(data.get("password", "")):
                 if usuario_con_licencia_activa(user.id):
                     return Response(200)
                 self.app.logged_in = True
                 return Response(302, {"Location": "/"})
             return Response(200)
         return Response(404)
 
     def get(self, path: str) -> Response:
+        if path == "/auth/logout":
+            self.app.logged_in = False
+            return Response(302, {"Location": "/auth/login"})
         if path == "/licencias/listar":
             if self.app.logged_in:
                 return Response(200)
             return Response(302, {"Location": "/auth/login"})
         return Response(404)
 
 
 class SimpleApp:
     def __init__(self) -> None:
         self.config: Dict[str, Any] = {}
         self.logged_in = False
 
     def test_client(self) -> SimpleClient:
         return SimpleClient(self)
 
 
 def create_app() -> SimpleApp:
     return SimpleApp()
 
 
 __all__ = ["create_app"]
