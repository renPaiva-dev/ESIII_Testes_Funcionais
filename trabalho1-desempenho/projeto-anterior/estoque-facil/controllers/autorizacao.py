"""Controle de acesso das telas: RN02 (exige login) e RN03 (perfil admin)."""
from functools import wraps

from flask import flash, redirect, session, url_for


def login_obrigatorio(f):
    @wraps(f)
    def wrapper(*a, **kw):
        if "usuario" not in session:
            return redirect(url_for("web.login"))
        return f(*a, **kw)
    return wrapper


def admin_obrigatorio(f):
    @wraps(f)
    def wrapper(*a, **kw):
        if session.get("perfil") != "admin":
            flash("Acesso restrito ao administrador.", "erro")
            return redirect(url_for("web.produtos"))
        return f(*a, **kw)
    return login_obrigatorio(wrapper)
