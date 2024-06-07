import re
import os
import logging
import json
from typing import Any, Dict, List, Union
import boto3
from acai.cache_query.validate_query import ValidateQuery

# Set up logging
LOGLEVEL = os.environ.get('LOG_LEVEL', 'DEBUG').upper()
logging.getLogger().setLevel(LOGLEVEL)
for noisy_log_source in ["boto3", "botocore", "nose", "s3transfer", "urllib3"]:
    logging.getLogger(noisy_log_source).setLevel(logging.WARN)
LOGGER = logging.getLogger()

# Define environment variables
BEDROCK_SERVICE_REGION = os.environ['BEDROCK_SERVICE_REGION']
BEDROCK_MODEL_ID = os.environ.get('BEDROCK_MODEL_ID', 'anthropic.claude-3-haiku-20240307-v1:0')
BEDROCK_SERVICE_NAME = os.environ['BEDROCK_SERVICE_NAME']

# Initialize Bedrock client
BEDROCK_CLIENT = boto3.client(service_name=BEDROCK_SERVICE_NAME, region_name=BEDROCK_SERVICE_REGION)

def _generate_prompt(chat_query: str, context: str, previous_query: Union[str, Dict[str, Any]], validation_results: List[str]) -> str:
    prompt = f"""Here are some documents for you to reference for your task in xml tag <documents>:
<documents>{context}</documents>

Your task is creating a JSON query-policy for the ACAI account-context cache.
ONLY respond with JSON configuration policy in code format.
"""

    if previous_query:
        prompt += f"""
For this suggested query:
<json>{previous_query}</json>
the following validation results apply: {validation_results}
"""

    prompt += f"""
Human: {chat_query}

Assistant: """

    return prompt

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    try:
        with open('wiki.md', 'r') as file:
            context_content = file.read()

        validation = ValidateQuery(LOGGER)
        
        # Retrieve the prompt from the event
        chat_query = event.get('chat_query', '')

        previous_query: Union[str, Dict[str, Any]] = ""
        validation_results: List[str] = []
        query_json: Dict[str, Any] = {}

        # If validation results are not empty, repeat up to 3 times
        for _ in range(3):
            prompt = _generate_prompt(chat_query, context_content, previous_query, validation_results)
            LOGGER.info(prompt)
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            })
            response = BEDROCK_CLIENT.invoke_model(
                body=body,
                modelId=BEDROCK_MODEL_ID,
                accept='application/json',
                contentType='application/json',
            )
            LOGGER.info(response)
            response_body = json.loads(response['body'].read().decode('utf-8'))
            LOGGER.info(response_body)
            
            # Extract JSON code blocks from the content text
            content = response_body.get('content', [])
            if content and isinstance(content, list) and 'text' in content[0]:
                text = content[0]['text']
                code_blocks = re.findall(r'```json\n([\s\S]*?)```', text)
                query_json = json.loads(code_blocks[0]) if code_blocks else {}
                response_body['policy_json'] = query_json

                LOGGER.info(type(query_json))
                LOGGER.info(query_json)

                validation_results = validation.validate_patterns(query_json)
                LOGGER.info(validation_results)
                if not validation_results:
                    break
                previous_query = query_json

        return {
            'statusCode': 200,
            'body': json.dumps({
                'chat_query': chat_query,
                'policy_json': query_json,
                'response': response_body
            })
        }
    except Exception as e:
        LOGGER.error(f"Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }
