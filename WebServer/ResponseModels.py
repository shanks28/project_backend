from pydantic import BaseModel
class RequestBody(BaseModel):
    url:str
    platform:str
    type_content:str
class ResponseModel(BaseModel):
    user_name:str
    userid:int