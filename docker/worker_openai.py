import json, os, boto3
from openai import OpenAI

REGION = os.environ.get('AWS_REGION', 'ap-southeast-2')
QUEUE_URL = os.environ.get('QUEUE_URL', 'https://sqs.ap-southeast-2.amazonaws.com/958175315966/clinical-processing-queue')
TABLE = os.environ.get('TABLE_NAME', 'clinical-results')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

sqs = boto3.client('sqs', region_name=REGION)
s3 = boto3.client('s3', region_name=REGION)
bedrock = boto3.client('bedrock-runtime', region_name=REGION)
dynamodb = boto3.resource('dynamodb', region_name=REGION)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

print("Ready!")
print("Waiting for requests....")

while True:
    resp = sqs.receive_message(QueueUrl=QUEUE_URL, MaxNumberOfMessages=1, WaitTimeSeconds=20)
    print(f"SQS Response: {resp.get('ResponseMetadata', {}).get('RequestId', 'No RequestId')}")
    if 'Messages' in resp:
        print(f"Found {len(resp['Messages'])} message(s)")
    else:
        print("No messages in queue")
    for msg in resp.get('Messages', []):
        try:
            body = json.loads(msg['Body'])
            bucket = body['Records'][0]['s3']['bucket']['name']
            key = body['Records'][0]['s3']['object']['key']
            print(f"Processing: {key}")
            
            local = f"/tmp/{os.path.basename(key)}"
            s3.download_file(bucket, key, local)
            
            with open(local, "rb") as audio_file:
                transcript = openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                ).text
            print(f"Transcript: {transcript[:100]}...")
            
            prompt = """Return ONLY valid JSON: {"tasks":["task1","task2"],"diagnosis":"string","medications":[],"follow_up":"string","notes":"string"}

Extract actionable tasks from this clinical consultation transcript: """ + transcript
            
            try:
                resp_ai = bedrock.invoke_model(
                    modelId='anthropic.claude-3-haiku-20240307-v1:0',
                    body=json.dumps({
                        'anthropic_version': 'bedrock-2023-05-31',
                        'max_tokens': 1024,
                        'messages': [{'role': 'user', 'content': prompt}]
                    })
                )
                import re
                ai_text = json.loads(resp_ai['body'].read())['content'][0]['text']
                match = re.search(r'\{.*\}', ai_text, re.DOTALL)
                extracted = json.loads(match.group()) if match else {"notes": ai_text}
            except Exception as e:
                print(f"Bedrock error: {e}")
                extracted = {"notes": "extraction failed"}
            
            dynamodb.Table(TABLE).put_item(Item={'audio_key': key, 'transcript': transcript, **extracted})
            s3.delete_object(Bucket=bucket, Key=key)
            os.remove(local)
            sqs.delete_message(QueueUrl=QUEUE_URL, ReceiptHandle=msg['ReceiptHandle'])
            print(f"Done: {key}")
        except Exception as e:
            print(f"Error: {e}")
