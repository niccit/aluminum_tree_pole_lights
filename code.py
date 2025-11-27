import json
import board
import time
import os
import neopixel
import adafruit_logging
import wifi
import supervisor
import adafruit_connection_manager
import adafruit_minimqtt.adafruit_minimqtt
from adafruit_led_animation.group import AnimationGroup
from adafruit_minimqtt.adafruit_minimqtt import MMQTTException
from adafruit_led_animation.sequence import AnimationSequence
from circuitpy_helpers.led_animations import animationBuilder
from circuitpy_helpers.led_animations import controlLights
from circuitpy_helpers.led_animations import updateAnimationData
from circuitpy_helpers.file_helpers import updateFiles
from circuitpy_helpers.calendar_time_helpers import timeHelper
from circuitpy_helpers.network_helpers import wanChecker

# --- Set up logging --- #
logger = adafruit_logging.getLogger("tree_lights")
logger.setLevel(adafruit_logging.INFO)

# --- Get configuration data --- #
try:
    from data import data
    logger.info(f"data imported successfully")
except ImportError as ie:
    logger.error(f"failed to import data: {ie}")
    raise

# Variable assignments
high_limit = data["brightness_high"]
low_limit = data["brightness_low"]
pixel_count = data["num_pixels"]
before_sunset = data["seconds_before_sunset"]
sleep_time = data["sleep_time"]
# Assign stop time in seconds if not set to 0
# If set to 0 never sleep, run constantly
if data["stop_time"] is not "0":
    stop_time = timeHelper.get_time_in_seconds(data["stop_time"])
else:
    stop_time = int(data["stop_time"])
ignore_sunset = bool(data["ignore_sunset"])
running = False
time_in_seconds = None
sunset_in_seconds = None

logger.info(f"test: stop_time: {stop_time} and is of type {type(stop_time)}")
# --- Set up NeoPixels --- #
num_pixels = pixel_count
pixels = neopixel.NeoPixel(board.D15, num_pixels)

# --- MQTT Configuration --- #
radio = wifi.radio
pool = adafruit_connection_manager.get_radio_socketpool(radio)
ssl_context = adafruit_connection_manager.get_radio_ssl_context(radio)

# MQTT feeds
subscribe_list = []
tree_lights = os.getenv("mqtt_tree_lights_feed")
subscribe_list.append(tree_lights)
date_time = os.getenv("mqtt_datetime_feed")
subscribe_list.append(date_time)
sunset = os.getenv("mqtt_sunset_feed")
subscribe_list.append(sunset)

# MQTT specific helpers
def on_connect(mqtt_client, userdata, flags, rc):
    # This function will be called when the mqtt_client is connected
    # successfully to the broker.
    logger.info(f"Connected to MQTT Broker {mqtt_client.broker}!")
    logger.debug(f"Flags: {flags}\n RC: {rc}")
    for topic in subscribe_list:
        mqtt_client.subscribe(topic)

def on_disconnect(mqtt_client, userdata, rc):
    # This method is called when the mqtt_client disconnects
    # from the broker.
    logger.warning(f"{mqtt_client} Disconnected from MQTT Broker!")
    counter = 0
    backoff_sleep = 1
    backoff_increment = 1
    while counter <= 10:
        try:
            mqtt_client.reconnect()
            counter = 11
        except MMQTTException:
            counter += 1
            if counter - 1 == 0:
                time.sleep(backoff_sleep)
            else:
                backoff_sleep += backoff_increment
                time.sleep(backoff_sleep)
            pass

def on_subscribe(mqtt_client, userdata, topic, granted_qos):
    # This method is called when the mqtt_client subscribes to a new feed.
    logger.info(f"Subscribed to {topic} with QOS level {granted_qos}")

def on_unsubscribe(mqtt_client, userdata, topic, pid):
    # This method is called when the mqtt_client unsubscribes from a feed.
    logger.info(f"Unsubscribed from {topic} with PID {pid}")

def on_publish(mqtt_client, userdata, topic, pid):
    # This method is called when the mqtt_client publishes data to a feed.
    logger.info(f"Published to {topic} with PID {pid}")

def on_message(client, topic, message):
    global time_in_seconds, sunset_in_seconds
    logger.info(f"New message for {client} on topic {topic}: {message}")
    # Support changes to the light configurations in the data.py file
    if "tree" in topic:
        received_message = json.loads(message)
        # since the name of the name/value pair is known, use this in the MQTT message
        # it will be transformed to the actual value in the data file before calling updater.update_data_file
        search_string = received_message["search_string"]
        received_message['search_string'] = str(data[received_message["search_string"]])
        updated_message = json.dumps(received_message)
        updateFiles.update_data_file(updated_message, search_string)
        supervisor.reload()
    if "time" in topic:
        received_time = message
        time_in_seconds = timeHelper.get_time_in_seconds(received_time)
    if "sunset" in topic:
        sunset_time = message
        sunset_in_seconds = timeHelper.get_time_in_seconds(sunset_time)

    if time_in_seconds and sunset_in_seconds:
        global running
        if not running:
            controlLights.sleep_before_set_time(time_in_seconds, sunset_in_seconds, before_sunset, ignore_sunset, pixels)
            running = True
        else:
            controlLights.shutdown(time_in_seconds, stop_time, sunset_in_seconds, sleep_time, before_sunset, pixels)

mqtt_local_broker = os.getenv("mqtt_local_server")
mqtt_local_port = os.getenv("mqtt_local_port")
mqtt_local_username = os.getenv("mqtt_local_username")
mqtt_local_key = os.getenv("mqtt_local_key")
local_mqtt = adafruit_minimqtt.adafruit_minimqtt.MQTT(
    broker=mqtt_local_broker
    ,port = mqtt_local_port
    ,username=mqtt_local_username
    ,password=mqtt_local_key
    ,socket_pool=pool
    ,ssl_context=ssl_context
    ,is_ssl=False
)

# Connect callback handlers for local mqtt_client
local_mqtt.on_connect = on_connect
local_mqtt.on_disconnect = on_disconnect
local_mqtt.on_subscribe = on_subscribe
local_mqtt.on_unsubscribe = on_unsubscribe
local_mqtt.on_publish = on_publish
local_mqtt.on_message = on_message

# Connect
try:
    local_mqtt.connect()
except adafruit_minimqtt.adafruit_minimqtt.MMQTTException:
    logger.error("Failed to connect to MQTT broker!")


# --- Build Animations --- #
# Animations defined in animation.json
# Custom colors defined in data.py
chosen_animations = data["animations"]
animation_group = []
color = None
override_array = ["sparkles", "speed", "rate", "count", "period", "tail_length", "step", "reverse", "spacing", "size",
                  "bounce"]
# Read in all animations from json file
# And build the animation objects and append them to the array
with open('circuitpy_helpers/led_animations/animations.json', 'r') as infile:
    adata = json.load(infile)
    for item in adata['animations']:
        if item['name'] in chosen_animations:
            # Check for any animation overrides and update the JSON object
            item_with_overrides = updateAnimationData.override_default_settings(data, override_array, item)
            # Set the color choice
            logger.info(f"item with overrides: {item_with_overrides}")
            updated_item = updateAnimationData.set_color(data, item_with_overrides)
            logger.info(f"item to send is {updated_item}")
            obj = animationBuilder.build_animation(pixels, updated_item)
            animation_group.append(obj)

if len(animation_group) > 1:
    animations = AnimationSequence(
        AnimationGroup(
            *(x for x in animation_group))
        ,advance_interval=5
    )
else:
    animations = AnimationSequence(
        AnimationGroup(
            *(x for x in animation_group))
        ,advance_interval=0
    )

# --- Settings for Non-Blocking(ish) Hack provided by Mikey Sklar from Adafruit Forums! --- #
FRAME_DELAY = 0.01    # 100 FPS (20 ms per frame)
MQTT_POLL_EVERY = 100 # poll MQTT every 100 frames (~2 seconds at 50 FPS)
frame_counter = 0

# --- Main --- #
logger.info("Christmas Tree Lights starting up")
while True:
    # Start animations
    animations.animate()

    frame_counter += 1

    if frame_counter >= MQTT_POLL_EVERY:
        # Check WAN connectivity
        wan_state = wanChecker.cpy_wan_active()

        # if MQTT_POLL_EVERY criterion is met, loop mqtt for 1 second
        if wan_state:
            try:
                local_mqtt.loop(timeout=1)
            except OSError as e:
                print("MQTT error:", e)
                pass
                # optional reconnect logic here
                # We're using the on_disconnect method
        frame_counter = 0

    time.sleep(FRAME_DELAY)
