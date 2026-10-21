def install(app):
    original=app.openapi
    def schema():
        result=original()
        for path,operations in result['paths'].items():
            if not path.startswith('/api/') or path.startswith('/api/auth/') or path=='/api/health':continue
            for operation in operations.values():
                if not isinstance(operation,dict):continue
                params=operation.setdefault('parameters',[])
                if not any(p.get('name')=='project_id' for p in params):
                    params.append({'name':'project_id','in':'query','required':False,
                        'description':'Seçili proje; erişim/yetki anahtarı değildir. Yalnız oturum kullanıcısının projeleri erişilebilir. Liste için /api/projects kullanın; eski yerel kampüs otomatik atanmaz.',
                        'schema':{'type':'string','default':'campus-demo-25','pattern':'^(campus-demo-25|project-[a-f0-9]{12})$'}})
                operation['security']=[{'sessionCookie':[]}]
                for code in ('401','403','404','409','422','429','503'):
                    operation.setdefault('responses',{})[code]={'description':'Tutarlı hata zarfı; girdi içeriği/anahtar yansıtılmaz.',
                        'content':{'application/json':{'schema':{'type':'object','required':['detail','error'],'properties':{
                            'detail':{'type':'string'},'error':{'type':'object','required':['code','message','fields'],'properties':{
                                'code':{'type':'string'},'message':{'type':'string'},'fields':{'type':'array','items':{'type':'object','properties':{
                                    'field':{'type':'string'},'message':{'type':'string'}}}}}}}}}}}
        result.setdefault('components',{}).setdefault('securitySchemes',{})['sessionCookie']={'type':'apiKey','in':'cookie','name':'portfolio25_session','description':'HttpOnly oturum. Yazma isteklerinde Origin ve X-CSRF-Token zorunlu.'}
        return result
    app.openapi=schema
