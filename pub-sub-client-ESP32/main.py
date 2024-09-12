from machine import Pin, ADC, Timer
import time
import json
import utime
from util import create_mqtt_client, get_telemetry_topic, get_c2d_topic, parse_connection

ConnString_Azure = "CONN STRING"

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
data_interval = 20
ping_timer.init(period=ping_interval * 1000, mode=Timer.PERIODIC, callback=lambda t: send_ping())
ping_timer.init(period=data_interval * 1000, mode=Timer.PERIODIC, callback=lambda t: send_data())

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
    import urequests
    import ujson
    dict = {}
    dict["resourceUri"] = hubname+'.azure-devices.net/devices/'+deviceid
    dict["key"] = key
    dict["expiryInSeconds"]=86400
    payload = ujson.dumps(dict)
    response = urequests.post('COLOCAR AQUI SU FUNCION SAS AUTOMATICO', data=payload)
    
    return response.text

#Funcion encargada de manejar el mensaje recibido
def callback_handler(topic, message_receive):
    print('Received topic={} message={}'.format(topic, message_receive))
    message_text = message_receive.decode('utf-8')
    print(message_text)

def send_ping():
    print("Enviando Ping....")
    mqtt_client.ping()

def send_data():
    pot_value = pot.read()
    msg = json.dumps({"Data": {"sensor":"Pot", "Value": pot_value}})
    print("Publicando.. " + str(msg))
    mqtt_client.publish(topic=topic, msg=msg)

############### Programa principal ############################################
sas_token_str = getsas(hostname,device_id,shared_access_key)

# Creando cliente MQTT
mqtt_client = create_mqtt_client(client_id=device_id, hostname=hostname, username=username, password=sas_token_str, port=8883, keepalive=120, ssl=True)

#conectando a Azure IoT
print("Conectando al Broker MQTT de Azure")
mqtt_client.connect()

#Definiendo Topico a publicar
topic = get_telemetry_topic(device_id)
print("Publicando en:",topic)

#Definiendo Topico a suscribirse
subscribe_topic =  get_c2d_topic(device_id)
print("suscrito a:",subscribe_topic)

mqtt_client.set_callback(callback_handler)
t = mqtt_client.subscribe(topic=subscribe_topic) 

pot = ADC(Pin(33))
pot.atten(ADC.ATTN_11DB) 

while True:
    mqtt_client.wait_msg()
    gc.collect()
