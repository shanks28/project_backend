from fastapi import FastAPI, Request, HTTPException,status
#from models import User,Repurposed_Content,Content,Platform,get_session
from fastapi import Depends
from starlette.middleware.sessions import SessionMiddleware
from datetime import datetime,timedelta
from dotenv import load_dotenv
from ResponseModels import RequestBody
import httpx
import os
from newspaper import Article
from fastapi.responses import RedirectResponse,JSONResponse
from jose import jwt,JWTError
load_dotenv()

app = FastAPI()

SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

GITHUB_CLIENT_ID = os.getenv('GITHUB_CLIENT_ID')
GITHUB_CLIENT_SECRET = os.getenv('GITHUB_CLIENT_SECRET')
NGROK_URL = os.getenv('NGROK_URL')

refresh_tokens_store = {}

@app.get('/')
async def root(request:Request):
    return 'Hello'
async def extract(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        return article.text
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
async def create_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return username
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


@app.get("/login/github")
async def github_auth():
    return RedirectResponse(
        f'https://github.com/login/oauth/authorize'
        f'?client_id={GITHUB_CLIENT_ID}'
        f'&redirect_uri={NGROK_URL}/login/github/callback'
        f'&scope=read:user user:email'
    )


@app.get("/login/github/callback")
async def github_callback(request: Request, code: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": f"{NGROK_URL}/login/github/callback",
            },
        )
        token_response = response.json()
        github_access_token = token_response.get('access_token')
        if not github_access_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Failed to obtain access token")

        user_response = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {github_access_token}"}
        )
        user_info = user_response.json()
        username = user_info.get("login")
        if not username:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Failed to obtain user information")

        # Create JWT tokens
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        jwt_access_token = create_token(data={"sub": username}, expires_delta=access_token_expires)
        jwt_refresh_token = create_token(data={"sub": username}, expires_delta=refresh_token_expires)

        refresh_tokens_store[username] = jwt_refresh_token
        response = RedirectResponse('/')

        response.set_cookie(key="access_token", value=jwt_access_token, httponly=True, secure=True, samesite='Strict')
        response.set_cookie(key="refresh_token", value=jwt_refresh_token, httponly=True, secure=True, samesite='Strict')

        return response


async def user_info(request: Request):
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return decode_token(access_token)


@app.post("/refresh")
async def refresh_token(request: Request):
    refresh_token = request.cookies.get('refresh_token')
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token provided")

    username = decode_token(refresh_token)
    if refresh_tokens_store.get(username) != refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_token(data={"sub": username}, expires_delta=access_token_expires)
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    new_refresh_token = create_token(data={"sub": username}, expires_delta=refresh_token_expires)

    refresh_tokens_store[username] = new_refresh_token

    response = JSONResponse(content={"message": "Token refreshed"})

    response.set_cookie(key="access_token", value=new_access_token, httponly=True, secure=True, samesite='lax')#setting access tokens
    response.set_cookie(key="refresh_token", value=new_refresh_token, httponly=True, secure=True, samesite='lax')

    return response


@app.post("/someurl/")
async def someurl(request: Request, body: RequestBody, username: str = Depends(user_info)):
    content = await extract(body.url)
    return {"content": content, "user": username}



