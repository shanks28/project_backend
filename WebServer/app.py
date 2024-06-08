from fastapi import FastAPI, Request, Response,HTTPException,status
# from database import SessionLocal,engine
# from models import Base,User
import asyncio
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
import httpx
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
origins=[
    'http://localhost:5500',
    '*',
]
from fastapi.responses import RedirectResponse
from fastapi.responses import JSONResponse
import os
load_dotenv()
app=FastAPI()
# Base.metadata.create_all(bind=engine)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SessionMiddleware, secret_key="String")
github_client=os.getenv('GITHUB_CLIENT_ID')
github_secret=os.getenv('GITHUB_CLIENT_SECRET')
ngrok_url=os.getenv('NGROK_URL')
@app.get("/login/github")
async def github_auth():
    print(github_client)
    return RedirectResponse('https://github.com/login/oauth/authorize'
                            f'?client_id={github_client}'
                            f'&redirect_uri={ngrok_url}/login/github/callback'
                            f'&scope=read:user user:email')
@app.get("/")
async def root():
    return {"hello"}
@app.get("/login/github/callback")
async def github_callback(request:Request,code:str):
    async with httpx.AsyncClient() as client:
        response= await client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": github_client,
                "client_secret":github_secret,
                "code": code,
                "redirect_uri": f"{ngrok_url}/login/github/callback",
            },
        )
        token_response=response.json()
        print(token_response)
        access_token=token_response['access_token']
        print(access_token)
        if not access_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Failed")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.github.com/user",
                headers={"Authorization": f"Bearer {access_token}"}
            )
        user_info = response.json()
        username = user_info.get("login")
        request.session['user']=username
    return RedirectResponse('/')
@app.get('/user/info')
async def user_info(request:Request):
    user_details=request.session.get('user')
    print(user_details)
    if not user_details:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return JSONResponse(user_details)