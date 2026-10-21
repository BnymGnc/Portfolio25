"""One explicitly authorized small real request, never prints key/error bodies."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from config import load_backend_env
load_backend_env()
from ai_service import configured,provider_call,model,output_text
from fastapi import HTTPException

result={'configured':configured(),'model':model(),'attempted':False,'success':False}
if configured():
    result['attempted']=True
    try:
        response=provider_call({'instructions':'Kısa bağlantı kontrolü. Yalnız OK yaz.','input':'Bağlantı kontrolü.','max_output_tokens':128},retry=False)
        result['success']=bool(output_text(response).strip());result['status']='completed' if result['success'] else 'empty_output'
    except HTTPException as error:result['status']='unavailable';result['message']=str(error.detail)
else:result['status']='not_configured'
out=Path(__file__).resolve().parents[1]/'artifacts/improvements/llm-connection.json'
out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=True))
