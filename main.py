import pymupdf
from boto3 import Session
from botocore.exceptions import BotoCoreError, ClientError
from contextlib import closing
import os
import sys
import glob
from dotenv import load_dotenv

INPUT_FOLDER = 'text-input'
OUTPUT_FOLDER = 'audio-output'
AWS_REGION = 'us-east-1'
OUTPUT_FORMAT = 'mp3'
VOICE_ID = 'Matthew'
ENGINE = 'generative'

# Load variables from .env file
load_dotenv()

# Get the PDF file name
filename = glob.glob(f'{INPUT_FOLDER}/*.pdf')[0]

# Read in the PDF text file
with pymupdf.open(filename) as pdf:
    page_0 = pdf[0].get_text()

# Create AWS Session
session = Session(
    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
    region_name=AWS_REGION
)
polly = session.client('polly')

try:
    # Request speech synthesis
    response = polly.synthesize_speech(Text=page_0, OutputFormat=OUTPUT_FORMAT,
                                       VoiceId=VOICE_ID, Engine=ENGINE)
except (BotoCoreError, ClientError) as error:
    # The service returned an error, exit gracefully
    print(error)
    sys.exit(-1)

# Access the audio stream from the response
if 'AudioStream' in response:
    # Note: Closing the stream is important because the service throttles on the
    # number of parallel connections. Here we are using contextlib.closing to
    # ensure the close method of the stream object will be called automatically
    # at the end of the with statement's scope.
    with closing(response['AudioStream']) as stream:
        output = os.path.join(OUTPUT_FOLDER, f'{filename.split('\\')[1].split('.')[0]}.{OUTPUT_FORMAT}')

        try:
            # Open a file for writing the output audio as a binary stream
            with open(output, 'wb') as file:
                file.write(stream.read())
        except IOError as error:
            # Could not write to file, exit gracefully
            print(error)
            sys.exit(-1)

else:
    # The response didn't contain audio data, exit gracefully
    print('Could not stream audio')
    sys.exit(-1)
