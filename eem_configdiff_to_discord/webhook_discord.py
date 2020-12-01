import requests
#from discord_webhook import DiscordWebhook

#webhook = DiscordWebhook(url='https://discordapp.com/api/v6/webhooks/725878280405778483/s_6mBVT_H3aymE1-MRRgXoaiwycAxbrm8QVYSmTWgNCVOY_LAwawCePMhTjffEDaPuj6', content='Webhook Message')
#response = webhook.execute()

#print("Respuesta aquí:", response)

API_URL='https://discordapp.com/api/v6/webhooks/'
API_TOKEN= '725878280405778483/s_6mBVT_H3aymE1-MRRgXoaiwycAxbrm8QVYSmTWgNCVOY_LAwawCePMhTjffEDaPuj6'
url = API_URL + API_TOKEN


header = {
            'Content-Type': 'application/json'
        }
payload= {  "username": "JSON Estefania",
            "content": "Información en JSON por Atom"
        }
data = '{"username": "DATA Hernandez", "content": "Informacion en data por Atom"}'


response=requests.post(url,headers=header, json=payload)
print(response.status_code, response)

response=requests.post(url,headers=header, data=data)
print(response.status_code, response)
