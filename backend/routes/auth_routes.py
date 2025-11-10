from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from jose import jwt, JWTError
import httpx, traceback, time

from settings import *
from utils.helpers import *


auth_router = APIRouter()


@auth_router.get("/github/login")
async def github_login() -> RedirectResponse:
    params = {
        "client_id": GITHUB_CLIENT_ID,
        "scope": "read:user user:email",
        "allow_signup": "false",
    }
    url = "https://github.com/login/oauth/authorize"
    redirect = httpx.URL(url).copy_with(params=params)
    return RedirectResponse(str(redirect))


@auth_router.get("/github/callback", response_model=None)
async def github_callback(code: str | None = None) -> RedirectResponse | dict:
    if code is None:
        return {"success": False, "error": "missing code"}
    try:
        async with httpx.AsyncClient() as client:

            # get github oauth access token
            token_resp = await client.post(
                url=f"https://github.com/login/oauth/access_token",
                data={
                    "client_id": GITHUB_CLIENT_ID,
                    "client_secret": GITHUB_CLIENT_SECRET,
                    "code": code,
                },
                headers={"Accept": "application/json"},
            )
            token_resp.raise_for_status()
            token_resp_json = token_resp.json()
            access_token = token_resp_json.get("access_token", None)
            if access_token is None:
                return {"success": False, "error": "access token not found"}

            # get user info
            user_info_resp = await client.get(
                url="https://api.github.com/user",
                headers={
                    "Authorization": f"token {access_token}",
                    "Accept": "application/vnd.github.v3+json",
                },
                timeout=10,
            )
            user_info_resp.raise_for_status()
            user = user_info_resp.json()
            username = user.get("login")
            name = user.get("name") or username

            # get primary email
            email = None
            emails_resp = await client.get(
                "https://api.github.com/user/emails",
                headers={"Authorization": f"token {access_token}"},
                timeout=10,
            )
            if emails_resp.status_code == 200:
                emails = emails_resp.json()
                for em in emails:
                    if em.get("primary") and em.get("verified"):
                        email = em.get("email")
                        break

        # create jwt session
        payload = {
            "sub": username,
            "name": name,
            "email": email,
            "iat": int(time.time()),
            "exp": int(time.time()) + 60 * 60 * 4,  # 4 hours
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")

        # set cookie and redirect back to frontend
        response = RedirectResponse(url=f"{FRONTEND_URL}/")

        # TODO: set secure = True for production
        response.set_cookie(
            key="session",
            value=token,
            httponly=True,  # XSS protection
            secure=False,
            samesite="lax",  # csrf protection
            max_age=60 * 60 * 4,
        )
        return response

    # handle github oauth api taking too much time exception
    except httpx.TimeoutException:
        print_debug("github oauth took too much time", debug_error)
        return {
            "success": False,
            "error": f"github oauth took too much time",
        }

    # handle other unexpected exceptions
    except Exception as e:
        print_debug(f"caught exception: {e}\n{traceback.format_exc()}", debug_error)
        return {
            "success": False,
            "error": f"something went wrong: {e}",
        }


@auth_router.get("/github/get_user")
async def get_current_user(request: Request) -> dict:
    token = request.cookies.get("session")
    if not token:
        return {"success": False, "error": "no session"}
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return {"success": True, "user": payload}
    except JWTError:
        return {"success": False, "error": "invalid or expired token"}
    except Exception as e:
        print_debug(f"caught exception: {e}\n{traceback.format_exc()}", debug_error)
        return {
            "success": False,
            "error": f"something went wrong: {e}",
        }
