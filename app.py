[2025-06-04 20:52:13,385] ERROR in app: Exception on / [GET]
Traceback (most recent call last):
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/flask/app.py", line 2529, in wsgi_app
    response = self.full_dispatch_request()
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/flask/app.py", line 1825, in full_dispatch_request
    rv = self.handle_user_exception(e)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/flask/app.py", line 1823, in full_dispatch_request
    rv = self.dispatch_request()
         ^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/flask/app.py", line 1799, in dispatch_request
    return self.ensure_sync(self.view_functions[rule.endpoint])(**view_args)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/flask_login/utils.py", line 284, in decorated_view
    elif not current_user.is_authenticated:
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/werkzeug/local.py", line 311, in __get__
    obj = instance._get_current_object()
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/werkzeug/local.py", line 515, in _get_current_object
    return get_name(local())
                    ^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/flask_login/utils.py", line 25, in <lambda>
    current_user = LocalProxy(lambda: _get_user())
                                      ^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/flask_login/utils.py", line 372, in _get_user
    current_app.login_manager._load_user()
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/flask_login/login_manager.py", line 364, in _load_user
    user = self._user_callback(user_id)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/app.py", line 30, in load_user
    return User.query.get(int(user_id))
                          ^^^^^^^^^^^^
ValueError: invalid literal for int() with base 10: 'admin'
127.0.0.1 - - [04/Jun/2025:20:52:13 +0000] "GET / HTTP/1.1" 500 265 "-" "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
