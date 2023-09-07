from typing import Union
from fastapi import FastAPI
import openai
import os
import uvicorn
import json


app = FastAPI()
openai.api_key=""
messages = list()


@app.get("/")
def read_root():
    return {"message": "LeonardoAI API"}


def create_message(role: str, content: str):
    return {"role": role,
            "content": content}


@app.get("/text2script")
async def text2script(text: str):
    if text == '':
        return {
            "message": "Text Required"
        }
    
    starting_prompt = '''You are a professional writer specializing in writing podcast scripts.
                        I will tell you what is the subject that I want and you will give me an entertaining script to use.
                        You will make sure there are no placeholders or fields to replace.
                        You can imagine the hosts's name and other personal information.
                        You will have to stick to the subject of the podcast.'''
    
    if len(messages) == 0:
        messages.append(create_message("system", starting_prompt))

    try:
        messages.append(create_message('user', text))
        completion_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0613",
            messages=messages,
            max_tokens=2000,
            temperature=1
        )

        script = completion_response.choices[0].message
        print(script)

        print('all response')
        print(completion_response)

        idea_script = {'idea': text,
                    'script': script
        }

        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(idea_script)
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'message': str(e)
        }

async def script2audio(script: str):
    if script == '':
        return {
            "message": "Script Required"
        }
    

if __name__=="__main__":
    uvicorn.run(app,host="127.0.0.1",port=8000)
