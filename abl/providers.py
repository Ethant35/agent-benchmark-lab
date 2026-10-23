"""OpenRouter / explicit OpenAI-compatible adapters. No synthetic tool parsing."""
import asyncio
import json
import math
import os
import time
import httpx

class ProviderError(RuntimeError): pass
class Unsupported(ProviderError): pass
class CredentialsMissing(ProviderError): pass
class BudgetExceeded(ProviderError): pass

def reject_nonfinite(_):
    raise ValueError('Non-finite JSON number')

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
    @staticmethod
    def decode(value):
        try:
            data = json.loads(value, parse_constant=reject_nonfinite)
        except (ValueError, UnicodeError, RecursionError):
            raise ProviderError('Malformed provider JSON') from None
        if not isinstance(data, dict):
            raise ProviderError('Provider response must be an object')
        return data

    def scrub(self, value):
        if isinstance(value, str): return value.replace(self.key, '[REDACTED]')
        if isinstance(value, list): return [self.scrub(v) for v in value]
        if isinstance(value, dict): return {self.scrub(k):self.scrub(v) for k,v in value.items()}
        return value

    @staticmethod
    def usage(value):
        if value is None: return None
        if not isinstance(value, dict): raise ProviderError('Invalid usage object')
        for key in ('prompt_tokens', 'completion_tokens', 'total_tokens'):
            n = value.get(key)
            if n is not None and (type(n) is not int or n < 0):
                raise ProviderError('Invalid usage token count')
        details = value.get('prompt_tokens_details')
        if details is not None:
            if not isinstance(details, dict): raise ProviderError('Invalid usage details')
            n = details.get('cached_tokens')
            if n is not None and (type(n) is not int or n < 0):
                raise ProviderError('Invalid cached token count')
        cost = value.get('cost')
        if cost is not None and (type(cost) not in (int,float) or not 0 <= cost <= 1e100):
            raise ProviderError('Invalid usage cost')
        return value

    @staticmethod
    def validate_message(message):
        if not isinstance(message, dict) or message.get('role') != 'assistant':
            raise ProviderError('Invalid assistant message')
        if message.get('content') is not None and not isinstance(message['content'],str):
            raise ProviderError('Invalid assistant content')
        calls = message.get('tool_calls') or []
        if not isinstance(calls,list) or len(calls)>64:
            raise ProviderError('Tool call limit exceeded or invalid tool list')
        ids = set()
        for call in calls:
            if not isinstance(call,dict) or call.get('type') != 'function':
                raise ProviderError('Invalid tool call')
            function = call.get('function')
            if not isinstance(function,dict) or not isinstance(function.get('name'),str) or not function['name'] or not isinstance(function.get('arguments'),str):
                raise ProviderError('Invalid tool function')
            cid = call.get('id')
            if not isinstance(cid,str) or not cid or cid in ids:
                raise ProviderError('Invalid or duplicate tool call ID')
            ids.add(cid)
        return message

    async def chunks(self, response, check):
        # Ask for identity and reject compression so decoding cannot inflate a small
        # wire chunk into an unbounded allocation before our byte check.
        if response.headers.get('content-encoding', 'identity').lower() != 'identity':
            raise ProviderError('Compressed provider responses are unsupported')
        total = 0
        async for chunk in response.aiter_raw():
            check()
            total += len(chunk)
            if total > 8_000_000: raise ProviderError('Provider response byte limit exceeded')
            yield chunk

    async def events(self, response, check):
        pending = bytearray()
        fields = []
        size = 0
        async for chunk in self.chunks(response, check):
            pending.extend(chunk)
            while b'\n' in pending:
                line, _, rest = pending.partition(b'\n')
                pending = bytearray(rest)
                if len(line)>1_000_000: raise ProviderError('Stream line limit exceeded')
                line = line.rstrip(b'\r')
                if not line:
                    if fields: yield b'\n'.join(fields)
                    fields = []; size = 0
                elif line.startswith(b'data:'):
                    value = bytes(line[5:])
                    if value.startswith(b' '): value = value[1:]
                    size += len(value)
                    if size>1_000_000: raise ProviderError('Stream event byte limit exceeded')
                    fields.append(value)
            if len(pending)>1_000_000: raise ProviderError('Stream line limit exceeded')

    async def _request(self,messages,allowed,check,remaining_budget,progress):
        c=self.config
        body=dict(model=c.model,messages=messages,tools=[t for t in TOOLS if t['function']['name'] in allowed],
            max_tokens=c.max_output_tokens,stream=c.streaming)
        if c.temperature is not None: body['temperature']=c.temperature
        if c.reasoning_effort is not None:
            if c.provider=='openrouter': body['reasoning']={'effort':c.reasoning_effort}
            else: body['reasoning_effort']=c.reasoning_effort
        if c.provider=='openrouter': body['provider']={'require_parameters':True,'allow_fallbacks':False}
        elif c.streaming and c.stream_usage: body['stream_options']={'include_usage':True}
        request_bytes=len(json.dumps(body).encode())
        reserve=((request_bytes+4096)*c.input_price_per_million+c.max_output_tokens*c.output_price_per_million)/1e6
        if not math.isfinite(remaining_budget) or reserve>remaining_budget:
            raise BudgetExceeded(f'Request reserve {reserve:.6f} exceeds remaining budget {remaining_budget:.6f}')
        headers={'Authorization':'Bearer '+self.key,'Content-Type':'application/json','Accept-Encoding':'identity'}
        start=time.monotonic(); first=None; usage=None; raw=[]; message={'role':'assistant','content':''}; calls={}; response_id=None
        def generation(value):
            nonlocal response_id
            if value is None: return
            if not isinstance(value,str) or not value or len(value)>256:
                raise ProviderError('Invalid generation ID')
            if value != response_id:
                response_id = self.redact(value)
                progress('generation', response_id=response_id)
        check()
        async with httpx.AsyncClient(timeout=httpx.Timeout(60,connect=10),follow_redirects=False) as client:
            # Persist intent immediately before transmission, after all preflight checks.
            progress('request_started', request_reserve_usd=reserve, request_bytes=request_bytes)
            async with client.stream('POST',c.endpoint.rstrip('/')+'/chat/completions',headers=headers,json=body) as response:
                generation(response.headers.get('x-generation-id'))
                if response.status_code>=300:
                    raise ProviderError(f'Provider HTTP {response.status_code}')
                if not c.streaming:
                    content=bytearray()
                    async for chunk in self.chunks(response,check): content.extend(chunk)
                    data=self.scrub(self.decode(content)); raw.append(data)
                    generation(data.get('id'))
                    if data.get('error'): raise ProviderError('Provider returned an error')
                    choices=data.get('choices')
                    if not isinstance(choices,list) or not choices or not isinstance(choices[0],dict):
                        raise ProviderError('Response contains no valid choices')
                    message=self.validate_message(choices[0].get('message'))
                    usage=self.usage(data.get('usage'))
                else:
                    done=False; had_choice=False
                    async for value in self.events(response,check):
                        if value==b'[DONE]': done=True; break
                        data=self.scrub(self.decode(value)); raw.append(data)
                        if len(raw)>20000: raise ProviderError('Stream event limit exceeded')
                        generation(data.get('id'))
                        if data.get('error'): raise ProviderError('Provider returned a stream error')
                        if data.get('usage') is not None: usage=self.usage(data['usage'])
                        choices=data.get('choices',[])
                        if not isinstance(choices,list): raise ProviderError('Invalid stream choices')
                        for choice in choices:
                            if not isinstance(choice,dict): raise ProviderError('Invalid stream choice')
                            if choice.get('index',0)!=0: continue
                            had_choice=True
                            d=choice.get('delta',{})
                            if not isinstance(d,dict): raise ProviderError('Invalid stream delta')
                            if first is None and (d.get('content') or d.get('tool_calls') or d.get('reasoning')): first=time.monotonic()-start
                            content=d.get('content')
                            if content is not None and not isinstance(content,str): raise ProviderError('Invalid streamed content')
                            message['content']+=content or ''
                            details=d.get('reasoning_details')
                            if details is not None:
                                if not isinstance(details,list): raise ProviderError('Invalid reasoning details')
                                message.setdefault('reasoning_details',[]).extend(details)
                            deltas=d.get('tool_calls') or []
                            if not isinstance(deltas,list): raise ProviderError('Invalid tool deltas')
                            for call in deltas:
                                if not isinstance(call,dict): raise ProviderError('Invalid tool delta')
                                index=call.get('index')
                                if type(index) is not int or not 0<=index<64: raise ProviderError('Tool call index limit exceeded')
                                target=calls.setdefault(index,{'id':'','type':'function','function':{'name':'','arguments':''}})
                                if call.get('id'): target['id']=call['id']
                                function=call.get('function') or {}
                                if not isinstance(function,dict): raise ProviderError('Invalid function delta')
                                for k in ('name','arguments'):
                                    part=function.get(k)
                                    if part is not None and not isinstance(part,str): raise ProviderError('Invalid function fragment')
                                    target['function'][k]+=part or ''
                    if not done or not had_choice: raise ProviderError('Stream incomplete: missing completion marker or choices')
                    if calls: message['tool_calls']=[calls[i] for i in sorted(calls)]
                    self.validate_message(message)
        return dict(message=message,usage=usage,response_id=response_id,ttft_seconds=first,
            api_seconds=time.monotonic()-start,raw=raw,request_reserve_usd=reserve,
            request_bytes=request_bytes)
    def request(self,messages,allowed,check,remaining_budget,progress=None):
        async def guarded():
            task=asyncio.create_task(self._request(messages,allowed,check,remaining_budget,progress or (lambda kind,**data:None)))
            try:
                while not task.done():
                    check(); await asyncio.sleep(.05)
                try:
                    return await task
                except httpx.HTTPError as error:
                    raise ProviderError(self.redact(error)) from None
            finally:
                if not task.done():
                    task.cancel()
                    try: await task
                    except asyncio.CancelledError: pass
        return asyncio.run(guarded())
