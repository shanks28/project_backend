from fastapi import FastAPI, Request, HTTPException,status
from models import User,Repurposed_Content,Content,Platform,get_session
from fastapi import Depends
from typing import Annotated
from fastapi import Cookie
from cryptography.fernet import Fernet
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
import httpx
from fastapi.responses import RedirectResponse
from fastapi.responses import JSONResponse
import os
from fastapi.middleware.cors import CORSMiddleware
origins=[
    '*',
]

load_dotenv()
key=Fernet.generate_key()
cipher=Fernet(key)
app=FastAPI()
db=get_session()
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
        access_token=token_response['access_token']
        if not access_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Failed")
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.github.com/user",
                headers={"Authorization": f"Bearer {access_token}"}
            )
        user_info = response.json()
        username = user_info.get("login")
        response=RedirectResponse('/')
        if not db.query(User).filter(User.user_name==username):
            db.add(User(user_name=username))
            db.commit()
        access_token=cipher.encrypt(access_token.encode('utf-8')).decode('utf-8')
        response.set_cookie(key="access_token",value=access_token,httponly=True,secure=False)
        response.set_cookie(key="username",value=username,httponly=True,secure=False)
    return response
async def user_info(request:Request):
    access_token=request.cookies.get("access_token")
    if not access_token:
        return JSONResponse({"error":"No access token"})
    try:
        access_token=cipher.decrypt(access_token.encode('utf-8')).decode('utf-8')
        async with httpx.AsyncClient() as client:
            response=await client.get(
                "https://api.github.com/user",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            if response.status_code!=200:
                return JSONResponse({"error":"Invalid token"})
    except Exception as e:
        return JSONResponse({"invalid Token":str(e)})
    return status.HTTP_200_OK
@app.post("/someurl/")
async def someurl(request:Request,status:dict=Depends(user_info)):
    return status
