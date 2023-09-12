from fastapi import FastAPI
from fastapi.responses import FileResponse
import openai
import uvicorn
import json
from elevenlabs import generate, save, set_api_key
from dotenv import load_dotenv
import os
import re

load_dotenv()
app = FastAPI()
openai.api_key=os.getenv("OPENAI_API_KEY")
openai.organization=os.getenv("OPENAI_ORG")
messages = list()
set_api_key(os.getenv("XI_API_KEY"))


@app.get("/")
def read_root():
    return {"message": "SpotifAi API"}


def create_message(role: str, content: str):
    return {"role": role,
            "content": content}

def clean_script(script: str):
    pattern = r'\[[^\]]+\]'
    script = re.sub(pattern, '', script)
    host_flags = ["Host:", "Speaker:"]
    for ind in host_flags:
        script = script.replace(ind, '')
    
    return script

#@app.get("/text2script")
async def text2script(text: str):
    if text == '':
        return {
            'statusCode': 500,
            "message": "Text Required"
        }
    
    starting_prompt = '''You are a professional writer specializing in writing podcast scripts.
                        I will tell you what is the subject that I want and you will give me an entertaining script to use.
                        You will make sure there are no placeholders or fields to replace.
                        You can imagine the hosts's name and other personal information.
                        You will have to stick to the subject of the podcast.
                        Don't put any indicators for music (for example [Upbeat music] or [Opening Music] or [Closing Music])
                        Give me just the actual script of the podcast.
                        The podcast will have only one person who talks.
                        Don't specify the person who is talking the script (for example [Host] or [Guest] or [Speaker])
                        I will tell you the number of words I want in the script.
                        I will also tell you what is the gender of the speaker in the podcast.
                        Do not specify any music or sound effects or laughs or coughs or any sound-related detail.
                        And Do Not mention that the speaker is talking like this: "Speaker:" or "Host:"
                        All the details will be included in my prompt.'''
    
    if len(messages) == 0:
        messages.append(create_message("system", starting_prompt))
    
    details_prompt = "\nI want the script to be no long than 2400 characters long and the reader of the script is female"

    try:
        
        messages.append(create_message('user', text+details_prompt))
        completion_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0613",
            messages=messages,
            max_tokens=600,
            temperature=1
        )

        script = completion_response.choices[0].message.content
        #print("Original Script:\n"+script)
        script = clean_script(script)
        #For debugging
        #print(script)
        #print('all response')
        #print(completion_response)

        idea_script = {'idea': text,
                    'script': script
        }

        return script

        '''return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(idea_script)
        }'''
    
    except Exception as e:
        return "There is an exception in creating the script:\n"+str(e)

#@app.get("/script2audio")
async def script2audio(script: str):
    if script == '':
        return {
            'statusCode': 500,
            "message": "Script Required"
        }
    
    if script.startswith("There is an exception"):
        return {
            'statusCode': 500,
            "message": script
        }
    
    try:
        generated_audio = generate(text=script[:200],
                        voice="Bella",
                        model="eleven_monolingual_v1")
        save(generated_audio, "audio.wav")
        
        audio_path = "audio.wav"
        filename = os.path.basename(audio_path)
        headers = {'Content-Disposition': f'attachment; filename="{filename}"'}
        return FileResponse(audio_path, headers=headers,media_type="audio/wav")
    
    except Exception as e:
        return {
            'statusCode': 500,
            "message": "There was an exception in the audio creation:\n"+str(e)
        }


@app.post('/generate')
async def generate_podcast(text: str):
    script_toread = await text2script(text)
    assert isinstance(script_toread, str)
    response = await script2audio(script_toread)
    return response



if __name__=="__main__":
    uvicorn.run(app,host="127.0.0.1",port=8000)
