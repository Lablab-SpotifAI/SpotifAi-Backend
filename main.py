from typing import Union
from fastapi import FastAPI
import openai
import os
import uvicorn
import json


app = FastAPI()
openai.api_key = os.getenv("OPENAI_API_KEY")
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
    
    starting_prompt = '''I want you to give me a podcast script from the following text.
                        The podcast script should be long and should have many informations.
                        You should write a podcast script that will respect the directives given in the following text'''
    
    if len(messages) == 0:
        messages.append(create_message("system", starting_prompt))

    try:
        completion_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0613",
            messages=messages,
            max_tokens=5000
        )

        idea_script = {'idea': text,
                    'script': completion_response.choices[0].message
        }

        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(idea_script)
        }
    
    except Exception as e:
        print(e)
        return {
            "message" : "Server Error"
        }

async def script2audio(script: str):
    if script == '':
        return {
            "message": "Script Required"
        }
    
    

    




if __name__=="__main__":
    uvicorn.run(app,host="0.0.0.0",port=8000)
