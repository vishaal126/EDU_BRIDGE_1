"""Streamlit side of the EduBridge sign-in screen.

The futuristic login UI lives in `auth_component/` (HTML + CSS + JS) and runs as a Streamlit custom component.
Every button press is sent here as an action; this module calls `auth_service` (real SQLite accounts, real hashes,
real OAuth) and hands the outcome back to the component. Nothing the browser says is trusted: the component only
asks, the server decides, and `st.session_state.uid` is set here, server-side, after a genuine authentication.
"""
import logging
import uuid
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

import auth_service as A

log = logging.getLogger("edubridge.auth")
ss = st.session_state

_COMPONENT_DIR = Path(__file__).resolve().parent / "auth_component"
if not (_COMPONENT_DIR / "index.html").is_file():
    st.error("The sign-in screen files are missing from the deployment. Upload the whole `auth_component` folder "
             "(it only needs `index.html`) to the same place as `auth_ui.py` in your GitHub repo, "
             "then reboot the app.")
    st.stop()

_component = components.declare_component("edubridge_auth", path=str(_COMPONENT_DIR))

# The component iframe is stretched over the whole page so the original full-screen design is preserved.
_CSS = """<style>
iframe[title$="edubridge_auth"]{position:fixed;inset:0;width:100vw;height:100vh;height:100dvh;border:0;z-index:999990;background:#04050d;color-scheme:dark}
[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stSidebar"],[data-testid="collapsedControl"],footer{display:none!important}
.stApp{overflow:hidden}
</style>"""


def _secret(key):
    return st.secrets.get(key)


def _cookies():
    try:
        return dict(st.context.cookies)          # Streamlit >= 1.37; read-only view of the request cookies
    except Exception:
        return {}


def _oneshot(*names):
    ss["_clear"] = {"id": uuid.uuid4().hex, "names": list(names)}


# ---- session helpers (used by app.py) ------------------------------------------------------------
def require_session():
    """True only while st.session_state.uid has a live, server-side session behind it."""
    uid = ss.get("uid")
    if uid is None:
        return False
    if not A.session_valid(ss.get("eb_token"), uid):          # revoked (password reset, sign-out elsewhere) or expired
        _drop_login()
        return False
    return True


def _drop_login():
    for k in ("uid", "nav", "eb_token", "_pending", "_auth_result", "_auth_flash", "_pending_link", "_reset_token"):
        ss.pop(k, None)


def sign_out():
    A.revoke_session(ss.get("eb_token"))
    _drop_login()
    _oneshot("eb_rt")                                          # the component deletes the browser cookie on next render


def _restore_from_cookie():
    tok = _cookies().get("eb_rt")
    u = A.session_user(tok) if tok else None
    if not u:
        return False
    ss.uid, ss.eb_token = u["id"], tok
    return True


# ---- granting a session ----------------------------------------------------------------------------
def _grant(u, remember, created=False):
    token = A.create_session(u["id"], remember)
    ss["_pending"] = {"uid": u["id"], "token": token}          # promoted to uid only when the component says "continue"
    if ss.get("_clear") and "eb_rt" in ss["_clear"]["names"]:
        ss.pop("_clear")
    return {"ok": True, "created": created, "cookie": {"token": token, "persistent": bool(remember)},
            "user": {"name": u["name"], "email": u["email"] or u["phone"], "role": u["role"]}}


# ---- redirect handlers (OAuth callback, emailed reset link) ---------------------------------------
def _flash(**kw):
    ss["_auth_flash"] = dict(id=uuid.uuid4().hex, **kw)


def _handle_oauth_callback():
    qp = st.query_params
    if not (("code" in qp and "state" in qp) or ("error" in qp and "state" in qp)):
        return
    params = {k: qp.get(k) for k in ("code", "state", "error")}
    st.query_params.clear()                                    # never leave the code in the URL / history
    try:
        res = A.complete_oauth(params, _cookies().get("eb_oauth"))
        if res["status"] == "link":
            ss["_pending_link"] = res["pending"]
        else:
            ss["_auth_flash"] = dict(id=uuid.uuid4().hex, **_grant(res["user"], False, res["created"]))
    except A.AuthError as e:
        _flash(ok=False, error=str(e))
    except Exception:
        log.exception("OAuth callback failed")
        _flash(ok=False, error="Sign-in failed unexpectedly. Please try again.")
    _oneshot("eb_oauth")


def _handle_reset_link():
    tok = st.query_params.get("reset")
    if not tok:
        return
    st.query_params.clear()
    if A.validate_reset_token(tok):
        ss["_reset_token"] = tok                               # kept server-side; the browser never sees it again
    else:
        _flash(ok=False, error="This reset link is invalid or has expired. Request a new one.")


# ---- component actions -------------------------------------------------------------------------------
def _dispatch(act, v):
    s = lambda k, n=300: str(v.get(k) or "")[:n]
    if act == "login":
        return _grant(A.login(s("ident", 254), s("password", 256), s("role", 20)), bool(v.get("remember")))
    if act == "register":
        prof = v.get("profile") if isinstance(v.get("profile"), dict) else {}
        u = A.register(s("name", 100), s("email", 254), s("password", 256), s("confirm", 256), s("role", 20),
                       v.get("terms") is True, {k: str(prof.get(k) or "")[:300] for k in ("skills", "wants", "city", "state", "country")})
        return _grant(u, False, created=True)
    if act == "social_start":
        return {"ok": True, "redirect": A.begin_oauth(s("provider", 20), s("role", 20), s("bid", 140))}
    if act == "forgot":
        return {"ok": True, "message": A.request_password_reset(s("email", 254))}
    if act == "reset":
        tok = ss.get("_reset_token")
        if not tok:
            raise A.AuthError("This reset link is invalid or has expired. Request a new one.", fatal=True)
        u = A.reset_password(tok, s("password", 256), s("confirm", 256))
        ss.pop("_reset_token", None)
        return {"ok": True, "email": u["email"]}
    if act == "reset_cancel":
        ss.pop("_reset_token", None)
        return None
    if act == "link_confirm":
        pending = ss.get("_pending_link")
        if not pending:
            raise A.AuthError("This link request expired. Please sign in with Google or GitHub again.", fatal=True)
        u = A.confirm_link(pending, s("password", 256))
        ss.pop("_pending_link", None)
        return _grant(u, False)
    if act == "link_cancel":
        ss.pop("_pending_link", None)
        return None
    if act == "simple":
        st.query_params["simple"] = "1"
        return None
    if act == "continue":
        p = ss.pop("_pending", None)
        if p:
            ss.uid, ss.eb_token = p["uid"], p["token"]
            ss.pop("_auth_result", None)
            ss.pop("_auth_flash", None)
        return None
    raise A.AuthError("Unknown request.")


def _handle_action(v):
    aid = str(v.get("id") or "")[:64]
    ss["_auth_last"] = aid
    ss.pop("_auth_flash", None)
    try:
        res = _dispatch(v.get("action"), v)
    except A.AuthError as e:
        res = {"ok": False, "error": str(e), "field": e.field, "fatal": e.fatal}
    except Exception:
        log.exception("auth action failed")
        res = {"ok": False, "error": "Something went wrong. Please try again."}
    if res is not None:
        res["id"] = aid
        ss["_auth_result"] = res
    st.rerun()


# ---- native Streamlit sign-in: fallback screen (?simple=1); the animated component is the default ----------------------------------
def _sign_in_now(u):
    ss.uid, ss.eb_token = u["id"], A.create_session(u["id"], False)
    st.rerun()


def _render_simple_reset(tok):
    st.title("🎓 EduBridge AI")
    st.subheader("Choose a new password")
    with st.form("simple_reset"):
        pw = st.text_input("New password", type="password", key="rs_pw")
        cf = st.text_input("Confirm new password", type="password", key="rs_cf")
        go = st.form_submit_button("Update password", use_container_width=True)
    if go:
        try:
            A.reset_password(tok, pw, cf)
            st.query_params.clear()
            st.success("Password updated. Sign in with your new password.")
            st.button("Go to sign in")
        except A.AuthError as e:
            st.error(str(e))
        except Exception:
            log.exception("simple password reset failed")
            st.error("Something went wrong. Please try again.")


def _render_simple():
    tok = st.query_params.get("reset")
    if tok:
        if A.validate_reset_token(tok):
            _render_simple_reset(tok)
            return
        st.query_params.clear()
        st.error("This reset link is invalid or has expired. Request a new one.")
    st.title("🎓 EduBridge AI")
    st.caption("Sign in or create an account")
    tab_in, tab_up = st.tabs(["Sign in", "Create account"])
    with tab_in:
        with st.form("simple_login"):
            role = st.radio("I am a", ["Student", "Tutor"], horizontal=True, key="sl_role")
            ident = st.text_input("Email or mobile number", key="sl_id")
            pw = st.text_input("Password", type="password", key="sl_pw")
            go = st.form_submit_button("Sign in", use_container_width=True)
        if go:
            u = None
            try:
                u = A.login(ident, pw, role)
            except A.AuthError as e:
                st.error(str(e))
            if u:
                _sign_in_now(u)
    with tab_up:
        with st.form("simple_register"):
            role = st.radio("I am a", ["Student", "Tutor"], horizontal=True, key="sr_role")
            name = st.text_input("Full name", key="sr_name")
            email = st.text_input("Email", key="sr_email")
            c1, c2 = st.columns(2)
            pw = c1.text_input("Password", type="password", key="sr_pw", help="8+ characters, mixed case and a number or symbol")
            cf = c2.text_input("Confirm password", type="password", key="sr_cf")
            skills = st.text_input("Skills you can teach (optional)", key="sr_sk")
            wants = st.text_input("Skills you want to learn (optional)", key="sr_wn")
            d1, d2, d3 = st.columns(3)
            city = d1.text_input("City", key="sr_ci")
            state = d2.text_input("State", key="sr_st")
            country = d3.text_input("Country", value="India", key="sr_co")
            terms = st.checkbox("I accept the terms", key="sr_t")
            go = st.form_submit_button("Create account", use_container_width=True)
        if go:
            u = None
            try:
                u = A.register(name, email, pw, cf, role, bool(terms),
                               {"skills": skills, "wants": wants, "city": city, "state": state, "country": country})
            except A.AuthError as e:
                st.error(str(e))
            except Exception:
                log.exception("simple register failed")
                st.error("Something went wrong. Please try again.")
            if u:
                _sign_in_now(u)
    with st.expander("Forgot password?"):
        fe = st.text_input("Your account email", key="sf_email")
        if st.button("Send reset link", key="sf_go"):
            try:
                st.info(A.request_password_reset(fe))
            except A.AuthError as e:
                st.error(str(e))
            except Exception:
                log.exception("simple reset failed")
                st.error("Something went wrong. Please try again.")
    st.caption("Prefer the animated sign-in? Remove `?simple=1` from the page address.")


# ---- entry point -------------------------------------------------------------------------------------
def render():
    """Show the sign-in screen. Returns normally while the visitor is signed out; reruns once they are in."""
    A.set_secret_provider(_secret)
    if _restore_from_cookie():                                 # valid "remember me" / session cookie
        st.rerun()
    if st.query_params.get("simple"):                          # fallback: native Streamlit forms (?simple=1)
        _render_simple()
        return
    st.markdown(_CSS, unsafe_allow_html=True)
    _handle_oauth_callback()
    _handle_reset_link()
    pend = ss.get("_pending_link")
    link = {"provider": A.LABEL[pend["provider"]], "email": pend["email"]} if pend else None
    val = _component(key="eb_auth", default=None, providers=A.provider_status(), result=ss.get("_auth_result"),
                     flash=ss.get("_auth_flash"), clear=ss.get("_clear"), link=link,
                     mode="reset" if ss.get("_reset_token") else "login")
    if isinstance(val, dict) and val.get("id") and val.get("id") != ss.get("_auth_last"):
        _handle_action(val)
