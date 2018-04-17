import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.ssl_ import create_urllib3_context

CIPHERS = (
    'ECDH+AESGCM:DH+AESGCM:ECDH+AES256:DH+AES256:ECDH+AES128:DH+AES:ECDH+HIGH:'
    'DH+HIGH:ECDH+3DES:DH+3DES:RSA+AESGCM:RSA+AES:RSA+HIGH:RSA+3DES:!aNULL:'
    '!eNULL:!MD5'
)

class DESAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context(ciphers=CIPHERS)
        kwargs['ssl_context'] = context
        return super(DESAdapter, self).init_poolmanager(*args, **kwargs)


login_url = "https://app.eafit.edu.co/ulises/login-submit.do"

users = [{'login': 'jmoral33', 'clave': 'JuaZ1212', 'codigo': '201519101010'}]

notas_usuarios = {}
#Hacer el split del nombre de la materia por espacio-espacio, coger el codigo de la materia y el nombre. 
#La estructura propuesta es que el index del dataframe sea codigoest,semestre,codigomateria y las columnas 

for user in users:
    login_params = {param:value for param, value in user.items() if param in ['login', 'clave']}
    session = requests.Session()
    session.mount('https://app.eafit.edu.co/ulises/', DESAdapter())
    req_login = session.post(login_url, data=login_params, verify=True)
    if(req_login.status_code != 200):
        continue
    codigo = user['codigo']
    notas_usuarios[codigo] = {}
    cookies = session.cookies.get_dict()
    print(cookies)
    notas_url = 'https://app.eafit.edu.co/ulises/consultas/consultarNotas.do'
    semestres = ['20172', '20181']

    for semestre in semestres:
        notas_params = {'semestre': semestre, 'codest': codigo}
        print(notas_params)
        print(notas_url)
        req_notas = session.post(notas_url, data=notas_params)
        soup = BeautifulSoup(req_notas.text, 'html.parser')

        tables = soup.find_all('table', {"class" : "texto"}, recursive=True)

        for i, table in enumerate(tables):
            rows = table.findAll("tr")
            if(i%2 == 0):
                for j,row in enumerate(rows):
                    if(j == 0):
                        print(f"Nombre materia: {row.findAll('td')[1].text}")
                        cod_materia = row.findAll('td')[1].text.split(' - ')[0].strip()
                    elif(j == 2):
                        grupo_materia = row.findAll('td')[1].text.strip()
                    elif(j == 4 and semestre < '20181'):
                        print(f"Le quedo en: {float(row.findAll('td')[1].text)}")
                        notas_usuarios[codigo][cod_materia] = {'definitiva' : True, 'grupo': grupo_materia ,'nota_final': float(row.findAll('td')[1].text), 'notas':{}, 'semestre': semestre}
                    elif(j == 5 and semestre == '20181'):
                        print(f"La lleva en: {float(row.findAll('td')[1].text)}")
                        notas_usuarios[codigo][cod_materia] = {'definitiva': False, 'grupo': grupo_materia ,'nota_parcial': float(row.findAll('td')[1].text), 'notas': {}, 'semestre': semestre}
            else:
                if(len(rows) == 1):
                    print("No hay notas en esta materia")
                else:
                    print("Estas son sus notas: ")
                    for j,row in enumerate(rows):
                        if(j!=0):
                            tds = row.findAll("td")
                            print(f"{tds[0].text}: {float(tds[1].text)} que representa el: {float(tds[2].text)}%")
                            notas_usuarios[codigo][cod_materia]['notas'][tds[0].text] = (float(tds[1].text), float(tds[2].text))

                print('-' * 100)

print(notas_usuarios)