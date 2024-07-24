from pydantic import BaseModel
class RequestBody(BaseModel):
    url:str
    type_content:str
    access_token:str
    refresh_token:str
class getContent(BaseModel):
    access_token:str
    refresh_token:str
class ConnectToDev(BaseModel):
    api_key:str
    access_token:str
    refresh_token:str
class getDevContent(BaseModel):
    access_token:str
    refresh_token:str
class RepurposeTextDevTo(BaseModel):
    title:str
    content:str
    platform:str
    access_token:str
    refresh_token:str
class RepurposeTextStoredContent(BaseModel):
    title:str
    platform:str
    access_token:str
    refresh_token:str
class RepurposeDevtoContent(BaseModel):
    access_token:str
    refresh_token:str
    description:str
    platform:str
class Refresh(BaseModel):
    access_token:str
    refresh_token:str