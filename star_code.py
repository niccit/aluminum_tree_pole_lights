# SPDX-License-Identifier: MIT
import alarm
from alarm import time
import time
import board
import random
import neopixel
import analogio
from rainbowio import colorwheel

# --- Colors --- #
RED = 0xF00000
GREEN = 0x0FF000
BLUE = 0x000F0F  # 0F00FF, 0F0FFF
PINK = 0xFF0F0F
YELLOW = 0xF0F000
ORANGE = 0XF00F00
PURPLE = 0xF00FF0
WHITE = 0xF0F0F0
OFF = 0X000000

# --- CP Blue LEDs --- #
pixels = neopixel.NeoPixel(board.NEOPIXEL, 10)

# --- Light Sensor --- #

light_sensor = analogio.AnalogIn(board.LIGHT)

# --- Read in configurable data from file --- #
try:
    from data import data
except ImportError:
    print("Data file needs to have start stop times")
    raise

LIGHT_THRESHOLD = data["light_threshold"]
PIXEL_BRIGHTNESS = data["pixel_brightness"]
LL_PRINT_ITERATION_ON = data["ll_print_iteration_on"]
LL_PRINT_ITERATION_OFF = data["ll_print_iteration_off"]
MIDDAY_SLEEP_TIME = data["midday_sleep_time"]
STOP_TIME = data["stop_time"]
NIGHT_SLEEP_TIME = data["night_sleep_time"]

# --- Variables --- #
COLOR_ARRAY = [RED, GREEN, BLUE, PINK, YELLOW, ORANGE, PURPLE]
WORKING_COLOR_ARRAY = []
WORKING_ARRAY_LENGTH = (len(WORKING_COLOR_ARRAY))

# --- Modules for the light shows --- #

# Recreate the global working array of colors
def rebuild_color_array():
    global WORKING_COLOR_ARRAY, WORKING_ARRAY_LENGTH

    WORKING_COLOR_ARRAY.clear()
    for a in range(len(COLOR_ARRAY)):
        WORKING_COLOR_ARRAY.append(COLOR_ARRAY[a])
        WORKING_ARRAY_LENGTH = (len(WORKING_COLOR_ARRAY) - 1)


# Will return a random pixel from the full set of pixels
# Does not remove selected pixel from the array
def get_random_pixel():
    total_pixels = len(pixels)
    rando_pixel = random.randint(0, (total_pixels - 1))

    return rando_pixel


# Will return a color that is randomly selected from the working color array
# Will then pop that color off the array to reduce repeats
def get_random_color():
    global WORKING_COLOR_ARRAY, WORKING_ARRAY_LENGTH

    color_int = random.randint(0, WORKING_ARRAY_LENGTH - 1)
    color = WORKING_COLOR_ARRAY[color_int]
    WORKING_COLOR_ARRAY.pop(color_int)
    WORKING_ARRAY_LENGTH = (len(WORKING_COLOR_ARRAY) - 1)

    return color

# Cycle odd/even colors as provided, loop through three times
# Takes two specific colors unless the rand value is True
def color_cycles(color1, color2, rand=False):
    loop = 0

    while loop <= 2:
        if rand:
            color1 = get_random_color()
            color2 = get_random_color()
            rebuild_color_array()
        for i in range(len(pixels)):
            if (i % 2) != 0:  # Odd pixel make it red
                pixels[i] = color1
            else:  # Even make it green
                pixels[i] = color2
            time.sleep(0.1)
        loop += 1

        time.sleep(0.1)
        pixels.fill(OFF)


# Fill the pixels with a color and then blink two times
# Takes three specific colors unless the rand value is True
def color_blink(color1, color2, color3, rand=False):
    blink_counter = 0
    while blink_counter <= 1:
        if rand:
            color1 = get_random_color()
            color2 = get_random_color()
            color3 = get_random_color()
            rebuild_color_array()

        pixels.fill(color1)
        time.sleep(1)
        pixels.fill(OFF)
        time.sleep(0.5)
        pixels.fill(color2)
        time.sleep(1)
        pixels.fill(OFF)
        time.sleep(0.5)
        pixels.fill(color3)
        time.sleep(1)
        pixels.fill(OFF)
        blink_counter += 1
        time.sleep(0.5)


# Twinkle all the lights randomly and with random colors
# Takes the variable loop_count
def twinkle_lights(loop_count):
    loop = 0

    while loop <= loop_count:
        for pixel in range(len(pixels)):
            if WORKING_ARRAY_LENGTH == 0:
                rebuild_color_array()

            color = get_random_color()
            pixels[get_random_pixel()] = color
            time.sleep(0.1)
        loop += 1
    pixels.fill(OFF)
    rebuild_color_array()
    time.sleep(1)

# Use rainbowio for some additional cool effects
def rainbow_cycle(wait):
    for j in range(255):
        for i in range(len(pixels)):
            rc_index = (i * 256 // len(pixels)) + j * 5
            pixels[i] = colorwheel(rc_index & 255)
        pixels.show()
        time.sleep(wait)


def rainbow(wait):
    for j in range(255):
        for i in range(len(pixels)):
            idx = i + j
            pixels[i] = colorwheel(idx & 255)
        pixels.show()
        time.sleep(wait)


# Method to direct which light show methods to use
def play_light_show(cycle_number):
    print("start light show")
    twinkle_lights(10)
    time.sleep(1)
    if (cycle_number % 2) != 0:
        rainbow_cycle(0.1)
        time.sleep(1)
        twinkle_lights(5)
        time.sleep(1)
        color_cycles(None, None, True)
        time.sleep(1)
        twinkle_lights(5)
        time.sleep(1)
        color_blink(None, None, None, True)
        time.sleep(1)
        twinkle_lights(5)
        time.sleep(1)
        color_cycles(None, None, True)
        time.sleep(1)
        twinkle_lights(5)
    else:
        rainbow_cycle(0.1)
        time.sleep(1)
        twinkle_lights(5)
        time.sleep(1)
        color_cycles(RED, GREEN)
        time.sleep(1)
        twinkle_lights(5)
        time.sleep(1)
        color_blink(RED, GREEN, YELLOW)
        time.sleep(1)
        twinkle_lights(5)
        time.sleep(1)
        color_cycles(BLUE, PURPLE)
        time.sleep(1)
        twinkle_lights(5)
    print("end light show")


# --- The Work --- #

# Set pixel brightness
pixels.brightness = PIXEL_BRIGHTNESS

# Ensure our working color array has all our colors
rebuild_color_array()

# Set counter to 0
# This is used to determine if we use hand-picked or random colors
counter = 0

# Set to true to start the light show
lights_on = False

# Mark the point with time.monotonic() that lights start running
start_time = 0

print("starting up!")
print(f"light sensor value is {light_sensor.value}")
while True:

    if not lights_on:
        # If the light threshold is low enough, close to sunset, turn on
        if light_sensor.value <= LIGHT_THRESHOLD or LIGHT_THRESHOLD == 0:
            print(f"light sensor value meets threshold {LIGHT_THRESHOLD}")
            lights_on = True
            play_light_show(counter)
            counter += 1
            start_time = time.monotonic()

    if lights_on:
        if LIGHT_THRESHOLD != 0:
            print(f"light sensor value is {light_sensor.value}")
            # It's morning and time to shut off until sunset-ish
            if light_sensor.value > LIGHT_THRESHOLD:
                print(f"{light_sensor.value} > {LIGHT_THRESHOLD}")
                print(f"{light_sensor.value} it's too bright, sleeping")
                counter = 0
                lights_on = False
                sleep_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + MIDDAY_SLEEP_TIME)
                alarm.exit_and_deep_sleep_until_alarms(sleep_alarm)

            # Sleep for designated time; usually this is overnight
            if time.monotonic() >= start_time + STOP_TIME:
                print(f"{time.monotonic()} is greater than {start_time + STOP_TIME} well it's time to stop sparkling, for now")
                counter = 0
                lights_on = False
                sleep_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + NIGHT_SLEEP_TIME)
                alarm.exit_and_deep_sleep_until_alarms(sleep_alarm)


    time.sleep(0.1)