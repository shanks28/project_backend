from fastapi import FastAPI, Request, HTTPException,status,Response
from models import User,Repurposed_Content,Content,get_session,content_type
from fastapi import Depends
from datetime import datetime,timedelta
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from ResponseModels import RequestBody,getContent,ConnectToDev,getDevContent,RepurposeTextStoredContent,RepurposeDevtoContent,Refresh
import httpx
import os
from store_token_redis import get_redis_object
from fastapi import Request
import requests
from newspaper import Article,ArticleException
from fastapi.responses import RedirectResponse,JSONResponse
from jose import jwt,JWTError
from paraphrase import get_response
origins = [
    "*"  # Adjust this to the URL of your frontend applicationd
]

load_dotenv()
db=get_session()
app = FastAPI()
redis_object=get_redis_object()
SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30
REFRESH_TOKEN_EXPIRE_DAYS = 365
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

GITHUB_CLIENT_ID = os.getenv('GITHUB_CLIENT_ID')
GITHUB_CLIENT_SECRET = os.getenv('GITHUB_CLIENT_SECRET')
NGROK_URL = os.getenv('NGROK_URL')

refresh_tokens_store = {} # normally done in redis data store.
dev_tokens_store={}
@app.get('/')
async def root(request:Request):
    return "HOME PAGE"
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
        access_token_expires = timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
        refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        jwt_access_token = await create_token(data={"sub": username}, expires_delta=access_token_expires)
        jwt_refresh_token = await create_token(data={"sub": username}, expires_delta=refresh_token_expires)
        refresh_tokens_store[username] = jwt_refresh_token
        response = RedirectResponse('/')
        # response.set_cookie(key="access_token", value=jwt_access_token, httponly=True, secure=True, samesite='Strict')
        # response.set_cookie(key="refresh_token", value=jwt_refresh_token, httponly=True, secure=True, samesite='Strict')
        # response.set_cookie(key='github_access_token',value=github_access_token, httponly=True, secure=True, samesite='Strict')
        return JSONResponse({"access_token":jwt_access_token,"refresh_token":jwt_refresh_token})


async def user_info(token:str):
    access_token=token
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return await decode_token(access_token)


@app.post("/refresh")
async def refresh_token(request: Request,tokens:Refresh):
    refresh_token = tokens.refresh_token
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token provided")

    username =  await decode_token(refresh_token)
    if refresh_tokens_store.get(username) != refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    access_token_expires = timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    new_access_token = await create_token(data={"sub": username}, expires_delta=access_token_expires)
    # refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    # new_refresh_token = await create_token(data={"sub": username}, expires_delta=refresh_token_expires)
    #
    # refresh_tokens_store[username] = new_refresh_token
    return {"access_token":new_access_token}


@app.post("/extract/")
async def repurpose(request: Request, body: RequestBody):
    access_token=body.access_token
    username=await user_info(access_token)
    user = db.query(User).filter(User.user_name == username).first()
    text, authors, platform_name, title = await extract(body.url)
    existing_content = db.query(Content).filter(Content.title == title).first()
    if existing_content:
        return JSONResponse("This Title is already stored", status_code=status.HTTP_200_OK)
    try:
        post_type_enum = content_type(body.type_content.lower()) # converting from String to python-enum
    except Exception:
        return JSONResponse("Enter Either blog,social_media,tweet or story only", status_code=status.HTTP_400_BAD_REQUEST)
    new_content = Content(
        user_id=user.id,
        title=title,
        original_content=text,
        post_type=post_type_enum
    )
    db.add(new_content)
    db.commit()
    db.refresh(new_content)
    return JSONResponse("Extracted and Stored in DB", status_code=status.HTTP_200_OK)

@app.post('/get_stored_content/')
async def get_all_content(request:Request,body:getContent):
    try:
        access_token=body.access_token
        username=await user_info(access_token)
        user=db.query(User).filter(User.user_name==username).first()
        print(user.id)
        titles=db.query(Content.title).filter(Content.user_id==user.id).all()
        print(titles)
        print(type(titles))
        titles_json={index:title[0] for index,title in enumerate(titles)}
        #all_titles=str(db.query(Content.title).filter(Content.user_id == user_id).all())
        return titles_json
    except Exception:
        return JSONResponse("User does not exist", status_code=status.HTTP_404_NOT_FOUND)
@app.post('/store_dev_token/',response_model=str)
async def store_dev_token(request:Request,token:ConnectToDev):
    try:
        access_token=token.access_token
        username=await user_info(access_token)
        dev_token=token.api_key
        dev_tokens_store[username]=dev_token
        return dev_tokens_store.get(username)
    except Exception as e:
        return JSONResponse("Error Storing Token")
    #https://gist.github.com/298e887639407a20b50ba80da11e0df8.git
@app.post('/get_dev_content/')
async def get_dev_content(request:Request,body:getDevContent):
    try:
        access_token=body.access_token
        username=await user_info(access_token)
        token=dev_tokens_store.get(username)
        if not token:
            return JSONResponse("No DevToken Found")
        headers={'api_key':token}
        response=requests.get(f"https://dev.to/api/articles/me",headers=headers)
        if response.status_code==200:
            articles=response.json()
            extracted_articles = [{"title": article["title"], "content": article.get("description", "")} for article in
                                  articles]
            return extracted_articles
        else:
            return JSONResponse("Error fetching content")
    except Exception as e:
        return JSONResponse("Error fetching content")
@app.post('/repurpose_stored_content/')
async def repurpose_stored_content(request:Request,body:RepurposeTextStoredContent):
    try:
        access_token=body.access_token
        username=await user_info(access_token)
        title_to_repurpose=body.title
        content=db.query(Content).filter(Content.title==title_to_repurpose).first()
        if not content:
            return JSONResponse("No ContentWith that Title found")
        cid=content.id
        stored_content=(db.query(Content).filter(Content.title==title_to_repurpose).first()).original_content
        user_id=db.query(User).filter(User.user_name==username).first().id
        repurposed_object=db.query(Repurposed_Content).filter(Repurposed_Content.content_id==cid).first()
        if not repurposed_object:
            response = get_response(stored_content, body.platform)
            repurposed_object=Repurposed_Content(user_id=user_id,content_id=cid,title=title_to_repurpose,repurposed_content=response)
            db.add(repurposed_object)
            db.commit()
            db.refresh(repurposed_object)
            return response
        return repurposed_object.repurposed_content
    except Exception as e:
        print(e)
        return JSONResponse("Invalid Content or no User Found")
@app.post('/repurpose_dev_content/')
async def repurpose_dev_content(request:Request,body:RepurposeDevtoContent):
    try:
        access_token=body.access_token
        username=await user_info(access_token)
        content=body.description
        platform=body.platform
        response=get_response(content, platform)
        return response
    except Exception as e:
        return JSONResponse("Error repurposing content")
@app.post('/logout')
async def logout(request:Request,response:Response,body:Refresh):
    try:
        access_token=body.access_token
        refresh_token=body.refresh_token
        if access_token and refresh_token:
            return JSONResponse({
                "message":"Successfully Logged out"},status_code=status.HTTP_200_OK)
        else:
            return "Either the access token or refresh token is invalid"
    except Exception as e:
        return JSONResponse("Error logging out")