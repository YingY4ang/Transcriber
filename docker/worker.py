import json, os, boto3, whisper

REGION = os.environ.get('AWS_REGION', 'ap-southeast-2')
QUEUE_URL = os.environ.get('QUEUE_URL', 'https://sqs.ap-southeast-2.amazonaws.com/958175315966/clinical-processing-queue')
TABLE = os.environ.get('TABLE_NAME', 'clinical-results')

sqs = boto3.client('sqs', region_name=REGION)
s3 = boto3.client('s3', region_name=REGION)
bedrock = boto3.client('bedrock-runtime', region_name=REGION)
dynamodb = boto3.resource('dynamodb', region_name=REGION)

print("Loading Whisper...")
model = whisper.load_model("base")
print("Ready!")

while True:
    resp = sqs.receive_message(QueueUrl=QUEUE_URL, MaxNumberOfMessages=1, WaitTimeSeconds=20)
    for msg in resp.get('Messages', []):
        try:
            body = json.loads(msg['Body'])
            bucket = body['Records'][0]['s3']['bucket']['name']
            key = body['Records'][0]['s3']['object']['key']
            print(f"Processing: {key}")
            
            local = f"/tmp/{os.path.basename(key)}"
            s3.download_file(bucket, key, local)
            transcript = model.transcribe(local)["text"]
            print(f"Transcript: {transcript[:100]}...")
            
            prompt = """Return ONLY valid JSON: {"diagnosis":"string","medications":[],"follow_up":"string","notes":"string"}

Transcript: """ + transcript
            
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
