from fastapi import FastAPI, Request, HTTPException,status
from models import User,Repurposed_Content,Content,Platform,get_session,content_type
from fastapi import Depends
from datetime import datetime,timedelta
from dotenv import load_dotenv
from ResponseModels import RequestBody,ResponseModel,ConnectDevTo,RepurposeTextDevTo,RepurposeTextStoredContent
import httpx
import os
from store_token_redis import get_redis_object
from fastapi import Request
import requests
from newspaper import Article,ArticleException
from fastapi.responses import RedirectResponse,JSONResponse
from jose import jwt,JWTError
from paraphrase import get_response
load_dotenv()
db=get_session()
app = FastAPI()
redis_object=get_redis_object()
SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

GITHUB_CLIENT_ID = os.getenv('GITHUB_CLIENT_ID')
GITHUB_CLIENT_SECRET = os.getenv('GITHUB_CLIENT_SECRET')
NGROK_URL = os.getenv('NGROK_URL')

refresh_tokens_store = {} # normally done in redis data store.
dev_tokens={}

@app.get('/')
async def root(request:Request):
    return 'Home Page'
async def extract(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        return article.text,article.authors,article.source_url,article.title
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
async def create_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    print(encoded_jwt)
    return encoded_jwt


async def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token-username-not provided",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return username
    except Exception as e:
        print(e)
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

        user=db.query(User).filter(User.user_name==username).first()
        if not user:
            user=User(user_name=username)
            db.add(user)
            db.commit()
            db.refresh(user)
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        jwt_access_token = await create_token(data={"sub": username}, expires_delta=access_token_expires)
        jwt_refresh_token = await create_token(data={"sub": username}, expires_delta=refresh_token_expires)
        refresh_tokens_store[username] = jwt_refresh_token
        response = RedirectResponse('/')
        response.set_cookie(key="access_token", value=jwt_access_token, httponly=True, secure=True, samesite='Strict')
        response.set_cookie(key="refresh_token", value=jwt_refresh_token, httponly=True, secure=True, samesite='Strict')
        response.set_cookie(key='github_access_token',value=github_access_token, httponly=True, secure=True, samesite='Strict')
        return response


async def user_info(request: Request):
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return await decode_token(access_token)


@app.post("/refresh")
async def refresh_token(request: Request):
    refresh_token = request.cookies.get('refresh_token')
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token provided")

    username =  await decode_token(refresh_token)
    if refresh_tokens_store.get(username) != refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = await create_token(data={"sub": username}, expires_delta=access_token_expires)
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    new_refresh_token = await create_token(data={"sub": username}, expires_delta=refresh_token_expires)

    refresh_tokens_store[username] = new_refresh_token

    response = JSONResponse(content={"message": "Token refreshed Successfully"})

    response.set_cookie(key="access_token", value=new_access_token, httponly=True, secure=True, samesite='lax')#setting access tokens
    response.set_cookie(key="refresh_token", value=new_refresh_token, httponly=True, secure=True, samesite='lax')

    return response


@app.post("/extract/")
async def repurpose(request: Request, body: RequestBody, username: str = Depends(user_info)):
    user = db.query(User).filter(User.user_name == username).first()
    if not user:
        user = User(user_name=username)
        db.add(user)
        db.commit()
        db.refresh(user)  #update the latest state of db

    text, authors, platform_name, title = await extract(body.url)

    existing_content = db.query(Content).filter(Content.title == title).first()
    if existing_content:
        return JSONResponse("Content with this title already exists", status_code=status.HTTP_400_BAD_REQUEST)

    platform = db.query(Platform).filter(Platform.name == platform_name).first()
    if not platform:
        platform = Platform(name=platform_name)
        db.add(platform)
        db.commit()
        db.refresh(platform)

    try:
        post_type_enum = content_type(body.type_content.lower()) # converting from String to python-enum
    except ValueError:
        return JSONResponse("Invalid Content Type", status_code=status.HTTP_400_BAD_REQUEST)

    new_content = Content(
        user_id=user.id,
        title=title,
        original_content=text,
        p_name=platform.name,
        post_type=post_type_enum
    )
    db.add(new_content)
    db.commit()
    content=db.query(Content.original_content).filter(Content.user_id == user.id).first()
    print(content)
    return JSONResponse("Successfully added to db", status_code=status.HTTP_200_OK)

@app.post('/get_stored_content/')
async def get_all_content(request:Request,username:str=Depends(user_info)):
    user_id=db.query(User.id).filter(User.user_name==username).first()[0]
    if not user_id:
        return JSONResponse("Please Enter a valid content")
    titles=db.query(Content.title).filter(Content.user_id==user_id).all()
    print(titles)
    #all_titles=str(db.query(Content.title).filter(Content.user_id == user_id).all())
    return (titles)
@app.post('/store_dev_token/',response_model=str)
async def store_dev_token(request:Request,token:ConnectDevTo,username:str=Depends(user_info)):
    try:
        token_existing=redis_object.get(username)
        if not token_existing:
            redis_object.set(username,token.api_key)
        return redis_object.get(username)
    except Exception as e:
        return JSONResponse("Error Storing Token")
    #https://gist.github.com/298e887639407a20b50ba80da11e0df8.git
@app.post('/get_dev_content/')
async def get_dev_content(request:Request,username:str=Depends(user_info)):
    try:
        token=redis_object.get(username)
        if not token:
            return JSONResponse("No DevToken Found")
        headers={'api_key':token}
        response=requests.get(f"https://dev.to/api/articles/me",headers=headers)
        if response.status_code==200:
            articles=response.json()
            return [{'title':article['title'],"content":article['description']}for article in articles]
        else:
            return JSONResponse("Error fetching content")
    except Exception as e:
        return JSONResponse("Error fetching content")
@app.post('/repurpose_stored_content/')
async def repurpose_stored_content(request:Request,title:RepurposeTextStoredContent,username:str=Depends(user_info)):
    try:
        to_repurpose=title.title
        content_id=db.query(Content.id).filter(Content.title==to_repurpose).first()[0]
        stored_content=(db.query(Content.original_content).filter(Content.title==to_repurpose).first())[0][:150]
        if not stored_content:
            return ("No Content Found")
        user_id=db.query(User.id).filter(User.user_name==username).first()[0]
        repurposed_object=db.query(Repurposed_Content).filter(Repurposed_Content.content_id==content_id).first()
        if not repurposed_object:
            response = get_response(stored_content, title.platform)
            repurposed_object=Repurposed_Content(user_id=user_id,p_name=title.platform,content_id=content_id,title=to_repurpose,repurposed_content=response)
            db.add(repurposed_object)
            db.commit()
            db.refresh(repurposed_object)
            return response
        return db.query(Repurposed_Content).filter(Repurposed_Content.title==to_repurpose).first().repurposed_content
    except Exception as e:
        print(e)
        return JSONResponse("Invalid Content or No Such Platform")
@app.post('/repurpose_dev_content/')
async def repurpose_dev_content(request:Request,title:RepurposeTextDevTo,username:str=Depends(user_info)):
    try:
        content=title.content
        platform=title.platform
        response=get_response(content, platform)
        return response
    except Exception as e:
        return JSONResponse("Error repurposing content")
# @app.post('/logout')
# async def logout(request:Request,response:Response):
#     refresh_token=request.cookies.get("refresh_token")
#     if not refresh_token:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="There is not refresh Token to Logout")
#     response.delete_cookie(key='access_token')
#     response.delete_cookie(key="refresh_token")
#     return JSONResponse({
#         "message":"Successfully Logged out"},status_code=status.HTTP_200_OK)