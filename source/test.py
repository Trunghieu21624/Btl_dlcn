#chọn 3 output của gpio là GPIO 23, 24, 25, 16
#Chân 16 xả tụ
#Hai chân input là GPIO 17, 27
##Chân GPIO 17 là chân start timer
#Chân GPIO 27 là chân stop timer

import RPi.GPIO as GPIO
import gpiozero as gpi
import time
from datetime import datetime
import paho.mqtt.client as mqtt
from fractions import Fraction
import pandas as pd
import os, sys
import json
import threading
import atexit


time.sleep(3) 
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
#GPIO.setmode(GPIO.BOARD)  # Đảm bảo đã chọn chế độ chân
global timer, delta_R, count, count_name, calib_value_a, calib_value_b, calib_value
calib_value_a = 0.001406
calib_value_b = -0.062
calib_value = 0
count_sample_47 = 0
count, count_name, delta_R = 0, 0,0
is_connect_wifi = 0
timer = []
mqtt_topic = "Test/LoadCell/Data" 
t1 = threading.Event() 
t1.set()
t3 = threading.Event()
t3.set()
# t2 = threading.Event()
# t2.set()
connect_wifi_flag = threading.Event()
connect_wifi_flag.clear()
lock = threading.Lock()
atexit.register(GPIO.cleanup) 



#------------------------Khởi tạo GPIO---------------------------------------------------
try: 
    # Thiết lập GPIO 23, 24, 25 là đầu ra
    output_pins = [23, 24, 25, 16]
    for pin in output_pins:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.LOW)
    # Thiết lập GPIO 17, 27 là đầu vào
    input_pins = [17, 27]
    for pin in input_pins:
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)  
    t1.set() 
except Exception as e:
        print("Error in setup: ", e)
        t1.clear()
        GPIO.cleanup()    


#------------------------Du lieu CSV---------------------------------------------------
header_topic_mqtt = '/home/'
# try:
#     with open(header_topic_mqtt + 'pi/mau tai 4.7myu') as store_data:
#         pass
# except FileNotFoundError:
#     with open(header_topic_mqtt + 'pi/mau tai 4.7myu','a+') as store_data:
#         store_data.write('{0},{1},{2}\n'.format('Name', 'RealValue', 'KindofData'))   
def create_excel_file(file_name):
    try:
        with open(header_topic_mqtt + 'pi/' + file_name) as store_data:
            pass
    except FileNotFoundError:
        with open(header_topic_mqtt + 'pi/' + file_name,'w+') as store_data:
            store_data.write('{0},{1},{2}\n'.format('No.','Name','Value'))

save_name_path = header_topic_mqtt + 'pi/' + 'data_loadcell.txt'
try:
    with open(save_name_path) as store_data:
        name_file = store_data.read()
except FileNotFoundError:
    timestamp_ = datetime.now().strftime("%Y_%m_%d-%H_%M_%S")
    name_file = f"stored_data_load_cell_{timestamp_}.csv"
    create_excel_file(name_file)
    with open(save_name_path, "w") as store_data:
        store_data.write(name_file)
    pass

def generate_data_status_lastwill(state, value):
	data = [{
                'name': 'machineStatus',
                'value': value,
	}]
	return (json.dumps(data))  


#------------------------MQTT---------------------------------------------------
#------------------------Set_up MQTT---------------------------------------------------
def on_connect(client: mqtt.Client, userdata, flags, rc):
    global status_old, is_connect_wifi
    print(f'Connected to MQTT broker {rc}')
    is_connect_wifi = 1
    connect_wifi_flag.clear()
    t1.set()
def on_disconnect(client: mqtt.Client, userdata, rc):
    global is_connect_wifi, count, count_name
    if rc != 0:
        print('Unexpected disconnection from MQTT broker')
        is_connect_wifi = 0
        connect_wifi_flag.set()
        t1.clear()
        count, count_name = 0, 0
        for pin in [23, 24, 25]:
            GPIO.output(pin, GPIO.LOW)
        GPIO.output(16, GPIO.HIGH)  # Xả tụ khi mất kết nối
        print("All output GPIOs turned OFF and capacitor discharged.")
#Client
topic_standard = 'Test/LoadCell/'
mqttBroker = '20.41.104.186'
mqttPort = 1883
mqttKeepAliveINTERVAL = 20
client = mqtt.Client()
client.will_set(topic_standard + 'Status/machineStatus',str(generate_data_status_lastwill('Off', 0)),1,1)
client.on_connect = on_connect
client.on_disconnect = on_disconnect
print('Connecting to broker ',mqttBroker)
# Check connection to MQTT Broker 
try:
    client.connect(mqttBroker, mqttPort, mqttKeepAliveINTERVAL)
except:
    print("Can't connect MQTT Broker!")
client.loop_start()
time.sleep(1)
        

def store_and_publish_json_data(changes):
    json_changes = []
    with lock:
        for change in changes:
            Name, RealValue, KindofData = change
            Timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(header_topic_mqtt + 'pi/' + name_file, 'a+') as store_data:
                store_data.write('{0},{1},{2},{3}\n'.format(Name, RealValue, Timestamp, is_connect_wifi))
            if KindofData == "Mean":
                json_changes.append({
                    'Name': Name,
                    'Value': RealValue,
                    'Timestamp': Timestamp,
                })
            else:
                json_changes.append({
                    'Name': Name,
                    'Value': RealValue,
                    'Timestamp': Timestamp,
                })
            if not is_connect_wifi:
                print("Disconnected from MQTT broker, storing data locally")
                with open(header_topic_mqtt + 'pi/stored_disconnectWifi_data.txt', 'a+') as file:
                    file.write(json.dumps(json_changes) + '\n')
        if json_changes and mqtt_topic and is_connect_wifi:
            json_string = json.dumps(json_changes)
            print(json_string)
            client.publish(mqtt_topic+f"/Timer/{Name}", json_string, 1, 1)
    
        
      
#------------------------Functions---------------------------------------------------
#Tính thời gian nạp tụ
tmp=0
def detect_time(pin):
    global count, timer
    #nếu có tín hiệu từ chân GPIO 17 thì bắt đầu đếm thời 
    time_temp = [0,0] 
    #print("Waiting for timer start signal...")
    while GPIO.input(17) == GPIO.LOW:
        time.sleep(0.001)
    time_temp[0] = time.perf_counter()
    while GPIO.input(27) == GPIO.LOW:
        time.sleep(0.001)
    time.sleep(0.001)
    time_temp[1] = time.perf_counter()
    elapsed = time_temp[1] - time_temp[0]
    timer.append(elapsed)
    if elapsed <= 0:
        print(f"Lỗi: Thời gian âm ({elapsed}), bỏ qua")
    else:
        print(f"Thời gian nạp tụ: {elapsed:.6f} giây")
    GPIO.output(pin, GPIO.LOW)
    GPIO.output(16, GPIO.HIGH) #xả tụ
    calculator_delta_R()
    #if GPIO.input(17) == GPIO.LOW:
    while GPIO.input(17) == GPIO.HIGH:
        time.sleep(0.001)
        print("Chờ xả tụ...")   
    GPIO.output(16, GPIO.LOW)
    

#Giá trị delta R       
def calculator_delta_R():
    global delta_R, count, timer
    changes= []
    count+=1
    if count <= 3:
        Name = f"Timer_{count}"
        RealValue = timer[count-1] * 100000
        KindofData = f"Timer_{count}"
        store_and_publish_json_data([(Name, RealValue, KindofData)])
    else:
        delta_R = str((timer[2] + timer[0] + timer[1]) / 3 * 100000)
        timer.clear()
        count = 0
        
def cycle(pin):
    GPIO.output(pin, GPIO.HIGH)
    detect_time(pin)
    time.sleep(0.1)

def sample():
    global count, timer,count_name,delta_R
    changes = []
    old_value = -1
    #Nạp xả 1 lần
    try:
        cycle(23)
        timer.clear()
        count = 0 
    except Exception as e:
        print("Error in sample: ", e)
        GPIO.cleanup()
    count_name = 0
    while True: 
        t1.wait()
        try: 
            for pin in output_pins: 
                if pin != 16:
                    cycle(pin)
                Name = "Mean_Timer"
                RealValue = delta_R
                KindofData = "Mean" 
                #write RealValue to file mautai 4.7myu
                #sample_47(Name, RealValue, KindofData)
                calib_value = calib_value_a * float(delta_R) + calib_value_b
                if old_value != RealValue:
                    store_and_publish_json_data([(Name, RealValue, KindofData)])
                    store_and_publish_json_data([("Giá trị của tụ", calib_value, KindofData)])
                old_value = RealValue
                count_name += 1
                if count_name == 3:
                    count_name = 0

            time.sleep(2)
        except Exception as e:
            print("Error in sample loop: ", e)
            GPIO.cleanup()
            break
 

            
# def sample_47(Name, RealValue, KindofData):
#     global count_sample_47
#     count_sample_47 += 1
#     with open(header_topic_mqtt + 'pi/mau tai 4.7myu','a+') as store_data:
#         store_data.write('{0},{1},{2}\n'.format(Name, RealValue, KindofData))
#     if count_sample_47 == 100:
#         #đọc cột RealValue trong file mau tai 4.7myu
#         df = pd.read_csv(header_topic_mqtt + 'pi/mau tai 4.7myu')
#         value_column = df['Value']
#         t1.clear()
#         print(f"Giá trị trung bình của cột RealValue: {mean_value}")
#         with open(header_topic_mqtt + 'pi/mau tai 4.7myu','w') as store_data:
#             pass
#         count_sample_47 = 0


# def calibrate(mean_time):
#     global value_capacitor
#     t3.wait()
#     while True:
        

# def lunn():
#     GPIO.setmode(GPIO.BCM)  # Đảm bảo đã chọn chế độ chân
#     GPIO.setwarnings(False)  # Tắt cảnh báo trùng chân
#     while True:
#         t2.wait()
# #In ra tất cả các trạng thái GPIO in, out bằng lệnh print

#         try:
#             for pin in output_pins:
#                 if GPIO.input(pin) == GPIO.HIGH:
#                     print(f"GPIO {pin} is HIGH")
#                 else:
#                     print(f"GPIO {pin} is LOW")
#             for pin in input_pins:
#                 if GPIO.input(pin) == GPIO.HIGH:
#                     print(f"GPIO {pin} is HIGH")
#                 else:
#                     print(f"GPIO {pin} is LOW")
#             time.sleep(1)
#         except Exception as e:
#             print(f"Error in lunn function: {e}")
    
    
    
#---------------------------------------------------------------------------        
if __name__ == "__main__":
    t1_flag = threading.Thread(target=sample)
    t1_flag.start()
    # t2_flag = threading.Thread(target=lunn)
    # t2_flag.start()
    # t3_flag = threading.Thread(target=calibrate)
    # t3_flag.start()
    



    
    
    
    
    
    



