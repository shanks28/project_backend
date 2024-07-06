from pydantic import BaseModel
class RequestBody(BaseModel):
    url:str
    platform:str
    type_content:str
    user_id:int
class ResponseModel(BaseModel):
    user_name:str
    userid:int