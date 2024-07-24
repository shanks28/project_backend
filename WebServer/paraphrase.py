import os
import openai
from dotenv import load_dotenv
load_dotenv()
api_key=os.getenv("OPEN_AI_KEY")
openai.api_key=api_key
def get_response(content,platform="TIMES"):
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "your task is to rephrase the content i give for this platform{}".format(platform)},
            {"role": "user", "content": "re phrase this {}".format(content)},
        ],
        max_tokens=250,
        temperature=0.7,
    )
    return response.choices[0].message['content'].strip()