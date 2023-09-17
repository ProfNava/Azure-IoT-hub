from machine import Pin, ADC, Timer
import time
import json
import utime
from util import create_mqtt_client, get_telemetry_topic, get_c2d_topic, parse_connection
import urequests
import ujson

ConnString_Azure = "HostName=IoTcourse-hub.azure-devices.net;DeviceId=Esp002;SharedAccessKey=PUArEYpdvFuXw/WOEBDzFoM9nWvFzn+UguL26nVFOuU="

dict_keys = parse_connection(ConnString_Azure)

HOST_NAME = "HostName"
SHARED_ACCESS_KEY_NAME = "SharedAccessKeyName"
SHARED_ACCESS_KEY = "SharedAccessKey"
SHARED_ACCESS_SIGNATURE = "SharedAccessSignature"
DEVICE_ID = "DeviceId"
MODULE_ID = "ModuleId"
GATEWAY_HOST_NAME = "GatewayHostName"

# Crear un temporizador para enviar pings periódicamente
ping_timer = Timer(-1)
ping_interval = 60  # Intervalo en segundos (ajusta según tus necesidades)
ping_timer.init(period=ping_interval * 1000, mode=Timer.PERIODIC, callback=lambda t: send_ping())


shared_access_key = dict_keys.get(SHARED_ACCESS_KEY)
shared_access_key_name =  dict_keys.get(SHARED_ACCESS_KEY_NAME)
gateway_hostname = dict_keys.get(GATEWAY_HOST_NAME)
hostname = dict_keys.get(HOST_NAME)
device_id = dict_keys.get(DEVICE_ID)
module_id = dict_keys.get(MODULE_ID)

# username = '<HOSTNAME>/<DEVICE_ID>'
#username = hostname + '/' + device_id
username = hostname + '/' + device_id + '/?api-version=2018-06-30'

################## Funciones IoT##################
def getsas(hubname, deviceid, key):

    dict = {}
    dict["resourceUri"] = hubname+'.azure-devices.net/devices/'+deviceid
    dict["key"] = key
    dict["expiryInSeconds"]=86400
    payload = ujson.dumps(dict)
    response = urequests.post('https://getsasiot.azurewebsites.net/api/HttpTrigger1?code=b4kTDT_J2cd4ZI3JzKCugB9-U1DV-QxkaPcYDurhnedcAzFueSsRAA==', data=payload)
    
    return response.text

def callback_handler(topic, message):
    print('Received topic={} message={}'.format(topic, message))
    message_text = message.decode('utf-8')
    topic_str = topic.decode('utf-8')
    
    if topic_str.startswith('$iothub/methods/POST/'):
        print("Mensaje de método directo. Contenido: ", message_text)
        print("Tópico:", topic_str)
        rid_index = topic_str.find('?$rid=')
        
        if rid_index != -1:
            rid = topic_str[rid_index + 6:]
            response_topic = '$iothub/methods/res/200/?$rid='+ str(rid)
            parsed_message = ujson.loads(message_text)
            comando = parsed_message.get("Comando")

            if comando == "ON":
                # Ejecutar el comando para encender un LED
                response_data = {"result": "Success", "message": "Led ON"}
                
            elif comando == "OFF":
                # Ejecutar el comando para apagar un LED
                response_data = {"result": "Success", "message": "Led OFF"}
            
            elif comando == "POT":                
                response_data = {"result": "Success", "value": read_Pot()}

            else:
                print(f"Comando desconocido: {comando}")
                    
            
            response_message = json.dumps(response_data)
            mqtt_client.publish(topic=response_topic, msg=response_message)
            print('Respuesta topico={} mensaje={}'.format(response_topic, response_message))

        else:
            print("No se encontro el identificador de solicitud ($rid) en el topico.")
    else:
        print("Mensaje de nube a dispositivo. Contenido: ", message_text)


def send_ping():
    print("Enviando Ping....")
    mqtt_client.ping()

def read_Pot():
    pot_value = pot.read()
    return pot_value

############### Programa principal ############################################
sas_token_str = getsas(hostname,device_id,shared_access_key)

# Creando cliente MQTT
mqtt_client = create_mqtt_client(client_id=device_id, hostname=hostname, username=username, password=sas_token_str, port=8883, keepalive=120, ssl=True)
mqtt_client.set_callback(callback_handler)

#conectando a Azure IoT
print("Conectando al Broker MQTT de Azure")
mqtt_client.connect()
print("Conectado!!")

dm_topic = '$iothub/methods/POST/#'
t = mqtt_client.subscribe(topic=dm_topic) 
print("suscrito a:", dm_topic)

pot = ADC(Pin(33))
pot.atten(ADC.ATTN_11DB) 

while True:
    mqtt_client.wait_msg()
    gc.collect()
