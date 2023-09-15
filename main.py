from fastapi import FastAPI
from fastapi.responses import FileResponse
import openai
import uvicorn
from dotenv import load_dotenv
import os
import re
import boto3
from botocore.exceptions import BotoCoreError, ClientError

load_dotenv()
app = FastAPI()
openai.api_key=os.getenv("OPENAI_API_KEY")
openai.organization=os.getenv("OPENAI_ORG")
polly = boto3.client('polly')
messages = list()


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
    
    details_prompt = "\nI want the script to be no long than 100 words long and the reader of the script is female"

    try:
        
        messages.append(create_message('user', text+details_prompt))
        completion_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0613",
            messages=messages,
            max_tokens=300,
            temperature=1
        )

        script = completion_response.choices[0].message.content
        script = clean_script(script)

        idea_script = {'idea': text,
                    'script': script
        }

        return script
    
    except Exception as e:
        return "There is an exception in creating the script:\n"+str(e)

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
        polly = boto3.client('polly')
        try:
            response = polly.synthesize_speech(
                Text=script,
                OutputFormat="mp3",
                VoiceId="Joanna")
        
        except (BotoCoreError, ClientError) as error:
            print(error)
            return {
                'statusCode': 500,
                "message": "There was a BotoError or ClientError:\n"+str(error)
            }
        
        if "AudioStream" in response:
            try:
                with open('audio.mp3', 'wb') as file:
                    file.write(response['AudioStream'].read())
                    print("Audio saved as 'output.mp3'")
            except IOError as error:
            # Could not write to file, exit gracefully
                return {
                'statusCode': 500,
                "message": "There was a IOError in saving the audio.mp3:\n"+str(error)
            }

        else:
            return {
                'statusCode': 500,
                "message": "There was a problem in saving the audio.mp3 file"
            }

        audio_path = "audio.mp3"
        filename = os.path.basename(audio_path)
        headers = {'Content-Disposition': f'attachment; filename="{filename}"'}
        return FileResponse(audio_path, headers=headers,media_type="audio/mp3")
    

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
