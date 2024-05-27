from fastapi import FastAPI, Request, Response,HTTPException,status
# from database import SessionLocal,engine
# from models import Base,User
import asyncio
import httpx
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse
import os
app=FastAPI()
# Base.metadata.create_all(bind=engine)

github_client=os.getenv('GITHUB_CLIENT')
github_secret=os.getenv('GITHUB_SECRET')
ngrok_url=os.getenv('NGROK_URL')
@app.get("/login/github")
async def github_auth():
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
                "redirect_uri": f"{ngrok_url}/auth/callback",
            },
        )
        token_response=response.json()
        access_token=token_response('access_token')
        if not access_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Failed")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.github.com/user",
                headers={"Authorization": f"Bearer {access_token}"}
            )
        user_info = response.json()

        email = user_info.get("email")
        username = user_info.get("login")