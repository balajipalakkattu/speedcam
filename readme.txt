##to run backend in https
uvicorn app.main:app --host 0.0.0.0 --port 8000 --ssl-keyfile "C:/DEV/AI-samples/certs/local.key" --ssl-certfile "C:/DEV/AI-samples/certs/local.crt"

## to run frontend in https using liveserver in vs code
## user preferences (user settings json)

{
    "liveServer.settings.https": {
    "enable": true,
    "cert": "C:/DEV/AI-samples/certs/local.crt",
    "key": "C:/DEV/AI-samples/certs/local.key",
    "passphrase": "admin"
},
"liveServer.settings.host": "0.0.0.0",
"liveServer.settings.useLocalIp": true,
"liveServer.settings.port": 5500
}


OR

## python https_server.py
