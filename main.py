from fastapi import FastAPI
from fastapi.responses import FileResponse
import openai
import uvicorn
import json
from elevenlabs import generate, save, set_api_key
from dotenv import load_dotenv
import os

load_dotenv()
app = FastAPI()
openai.api_key=os.environ.get("OPENAI_API_KEY")
openai.organization=os.environ.get("OPENAI_ORG_KEY")
messages = list()
set_api_key(os.environ.get("XI_API_KEY"))


@app.get("/")
def read_root():
    return {"message": "LeonardoAI API"}


def create_message(role: str, content: str):
    return {"role": role,
            "content": content}

def duration2tokenswords(duration_min: int):
    #Rates considered for words per minute and words per token
    wpm_rate=150
    wpt_rate=0.75
    
    #Calculate words and tokens and assert they're integers
    words=duration_min*wpm_rate
    assert isinstance(words, int)
    tokens=int(words/wpt_rate)
    assert isinstance(tokens, int)

    return words, tokens


@app.get("/text2script")
async def text2script(text: str, duration: int, gender: str):
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
                        Don't put any indicators for music (for example [Upbeat music] or [Starting Song])
                        Give me just the actual script of the podcast.
                        The podcast will have only one person who talks.
                        Don't specify the person who says the script (for example [Host] or [Guest])
                        I will tell you the number of words I want in the script.
                        I will also tell you what is the gender of the speaker in the podcast in my prompts.
                        All the details will be included in my prompt.'''
    
    if len(messages) == 0:
        messages.append(create_message("system", starting_prompt))
    
    words, tokens = duration2tokenswords(duration)
    details_prompt = "\nI want the script to be "+str(words)+" long and the reader of the script is a "+str(gender)

    try:
        
        messages.append(create_message('user', text+details_prompt))
        completion_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0613",
            messages=messages,
            max_tokens=tokens,
            temperature=1
        )

        script = completion_response.choices[0].message

        #For debugging
        #print(script)
        #print('all response')
        #print(completion_response)

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

@app.get("/script2audio")
async def script2audio(script: str, gender:str):
    if script == '':
        return {
            'statusCode': 500,
            "message": "Script Required"
        }
    
    voice = "Readwell" if gender=='male' else "Anya"
    save(generate(text=script,
                    voice=voice,
                    model="eleven_monolingual_v1"),
        "audio.wav")
    
    audio_path = "audio.wav"
    return FileResponse(audio_path, media_type="audio/wav")


if __name__=="__main__":
    uvicorn.run(app,host="127.0.0.1",port=8000)
