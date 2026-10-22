"""OpenRouter / explicit OpenAI-compatible adapters. No synthetic tool parsing."""
import asyncio
import json
import os
import time
import httpx

class ProviderError(RuntimeError): pass
class Unsupported(ProviderError): pass
class CredentialsMissing(ProviderError): pass
class BudgetExceeded(ProviderError): pass

TOOLS = [
 {'type':'function','function':{'name':'read_file','description':'Read a UTF-8 workspace file','parameters':{'type':'object','properties':{'path':{'type':'string'}},'required':['path'],'additionalProperties':False}}},
 {'type':'function','function':{'name':'write_file','description':'Write a UTF-8 workspace file','parameters':{'type':'object','properties':{'path':{'type':'string'},'content':{'type':'string'}},'required':['path','content'],'additionalProperties':False}}},
 {'type':'function','function':{'name':'shell','description':'Run a shell command inside the isolated workspace','parameters':{'type':'object','properties':{'command':{'type':'string'}},'required':['command'],'additionalProperties':False}}},
 {'type':'function','function':{'name':'finish','description':'Signal task completion; independent verifier decides success','parameters':{'type':'object','properties':{'message':{'type':'string'}},'required':['message'],'additionalProperties':False}}},
]

class CompatibleProvider:
    def __init__(self,config):
        self.config=config
        self.key=os.environ.get(config.api_key_env)
        if not self.key: raise CredentialsMissing(f'Missing credential environment variable {config.api_key_env}')
        if not config.supports_tools: raise Unsupported('Tool capability not explicitly enabled for this model/endpoint')
        if config.input_price_per_million is None or config.output_price_per_million is None:
            raise BudgetExceeded('Live execution requires conservative input/output price bounds for preflight spend checks')
    def redact(self,value):
        return str(value).replace(self.key,'[REDACTED]')
    async def _request(self,messages,allowed,check,remaining_budget):
        c=self.config
        body=dict(model=c.model,messages=messages,tools=[t for t in TOOLS if t['function']['name'] in allowed],
            max_tokens=c.max_output_tokens,stream=c.streaming)
        if c.temperature is not None: body['temperature']=c.temperature
        if c.reasoning_effort is not None:
            if c.provider=='openrouter': body['reasoning']={'effort':c.reasoning_effort}
            else: body['reasoning_effort']=c.reasoning_effort
        if c.provider=='openrouter': body['provider']={'require_parameters':True,'allow_fallbacks':False}
        elif c.streaming and c.stream_usage: body['stream_options']={'include_usage':True}
        # A byte upper estimate plus protocol margin, never substituted for measured tokens.
        reserve=((len(json.dumps(body).encode())+4096)*c.input_price_per_million+c.max_output_tokens*c.output_price_per_million)/1e6
        if reserve>remaining_budget: raise BudgetExceeded(f'Request reserve {reserve:.6f} exceeds remaining budget {remaining_budget:.6f}')
        headers={'Authorization':'Bearer '+self.key,'Content-Type':'application/json'}
        start=time.monotonic(); first=None; usage=None; raw=[]; message={'role':'assistant','content':''}; calls={}; response_id=None
        async with httpx.AsyncClient(timeout=httpx.Timeout(60,connect=10),follow_redirects=False) as client:
            if not c.streaming:
                response=await client.post(c.endpoint.rstrip('/')+'/chat/completions',headers=headers,json=body)
                if response.status_code>=400: raise ProviderError(f'HTTP {response.status_code}: '+self.redact(response.text[:1000]))
                data=response.json(); raw.append(data)
                if data.get('error'): raise ProviderError(self.redact(data['error']))
                if not data.get('choices'): raise ProviderError('Response contains no choices')
                message=data['choices'][0]['message']; usage=data.get('usage'); response_id=data.get('id')
            else:
                async with client.stream('POST',c.endpoint.rstrip('/')+'/chat/completions',headers=headers,json=body) as response:
                    if response.status_code>=400:
                        await response.aread(); raise ProviderError(f'HTTP {response.status_code}: '+self.redact(response.text[:1000]))
                    async for line in response.aiter_lines():
                        check()
                        if not line.startswith('data:'): continue
                        value=line[5:].strip()
                        if value=='[DONE]': break
                        data=json.loads(value); raw.append(data)
                        if len(raw)>20000: raise ProviderError('Stream event limit exceeded')
                        if data.get('error'): raise ProviderError(self.redact(data['error']))
                        response_id=data.get('id',response_id)
                        if data.get('usage') is not None: usage=data['usage']
                        for choice in data.get('choices',[]):
                            if choice.get('index',0)!=0: continue
                            d=choice.get('delta',{})
                            if first is None and (d.get('content') or d.get('tool_calls') or d.get('reasoning')): first=time.monotonic()-start
                            message['content']+=d.get('content') or ''
                            # Preserve provider reasoning details required for subsequent tool rounds.
                            if d.get('reasoning_details'): message.setdefault('reasoning_details',[]).extend(d['reasoning_details'])
                            for call in d.get('tool_calls',[]):
                                target=calls.setdefault(call['index'],{'id':'','type':'function','function':{'name':'','arguments':''}})
                                if call.get('id'): target['id']=call['id']
                                for k in ('name','arguments'): target['function'][k]+=call.get('function',{}).get(k) or ''
                    if calls: message['tool_calls']=[calls[i] for i in sorted(calls)]
        return dict(message=message,usage=usage,response_id=response_id,ttft_seconds=first,
            api_seconds=time.monotonic()-start,raw=raw,request_reserve_usd=reserve,
            request_bytes=len(json.dumps(body).encode()))
    def request(self,messages,allowed,check,remaining_budget):
        async def guarded():
            task=asyncio.create_task(self._request(messages,allowed,check,remaining_budget))
            try:
                while not task.done():
                    check(); await asyncio.sleep(.05)
                return await task
            finally:
                if not task.done():
                    task.cancel()
                    try: await task
                    except asyncio.CancelledError: pass
        return asyncio.run(guarded())
