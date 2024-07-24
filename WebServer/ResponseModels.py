from pydantic import BaseModel
class RequestBody(BaseModel):
    url:str
    platform:str
    type_content:str
    access_token:str
    refresh_token:str
class ResponseModel(BaseModel):
    user_name:str
    userid:int
class ConnectDevTo(BaseModel):
    api_key:str
class RepurposeTextDevTo(BaseModel):
    title:str
    content:str
    platform:str
class RepurposeTextStoredContent(BaseModel):
    title:str
    platform:str
class FrontEndRequest(BaseModel):
    access_token:str
    refresh_token:str