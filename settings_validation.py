##### .txt MUST BE IN THIS FILE FORMAT  #####
#####          CASE SENSITIVE           #####
'''
volume=[int]
brush_size=[int]
'''

import time

MIN_VOLUME = 0
MAX_VOLUME = 100
DEFAULT_VOLUME = 50

MIN_BRUSH_SIZE = 1
MAX_BRUSH_SIZE = 20
DEFAULT_BRUSH_SIZE = 3

def check_bounds(value, minimum, maximum):
    if value < minimum: return minimum
    if value > maximum: return maximum
    return value

while True:

    # checks for events every .1 seconds to not kill CPU
    time.sleep(.1)

    # tries to find validation_request.txt and if it isnt made yet,
    # goes back to the top of the loop
    try: 
        with open('validation_request.txt', 'r') as file: 
            request = file.read().strip()
    except FileNotFoundError: continue

    if request == '': continue

    data = {}

    # turns 'volume=70' into key='volume', value='70' in the dict
    # LINES MUST ONLY HAVE ONE '='
    for line in request.splitlines():
        key, value = line.split('=')
        data[key] = value
    
    # gets volume and brush size values, default if none provided
    input_volume = int(data.get('volume', DEFAULT_VOLUME))
    input_brush_size = int(data.get('brush_size', DEFAULT_BRUSH_SIZE))

    new_volume = check_bounds(input_volume, MIN_VOLUME, MAX_VOLUME)
    new_brush_size = check_bounds(input_brush_size, MIN_BRUSH_SIZE, MAX_BRUSH_SIZE)

    response = (
        f'input_volume={input_volume}\n'
        f'new_volume={new_volume}\n'
        f'input_brush_size={input_brush_size}\n'
        f'new_brush_size={new_brush_size}\n'
    )

    # writes debugging info and status code back to main program
    with open('validation_response.txt', 'w') as file: file.write(response)

