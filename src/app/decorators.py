"""Shared Flask route decorators for SoulPrint."""

from functools import wraps
import sys

from flask import abort, current_app, render_template, request


def require_license(f):
    """Gate a route behind the freemium license check.

    Unlicensed GET requests render the upgrade page.
    Unlicensed POST requests return 403 Forbidden.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Look up via module attribute so unittest.mock.patch
        # on "src.app.is_licensed" takes effect at call time.
        app_mod = sys.modules["src.app"]
        if not app_mod.is_licensed(instance_dir=current_app.instance_path):
            if request.method == "POST":
                abort(403)
            return render_template("upgrade.html")
        return f(*args, **kwargs)

    return decorated_function
