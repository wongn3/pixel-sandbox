##### .txt MUST BE IN THIS FILE FORMAT  #####
#####          CASE SENSITIVE           #####
##### MUST BE RUN IN WINDOWS POWERSHELL #####
'''
event=button_clicked
button_type=[MUST CORRESPOND TO KEY IN SOUND_MAP]
volume=[int]
muted=[true/false]
'''

import time
import pygame

# starts and preps pygames sound thingy
pygame.mixer.init()

# hardcoded dict of sounds. KEY CORRESPONDS TO BUTTON TYPE
SOUND_MAP = {
    'default': 'sounds/default.wav',
    'digital': 'sounds/digital.wav',
    'sand': 'sounds/sand.wav',
    'grass': 'sounds/grass.wav',
    'water': 'sounds/water.ogg',

    # TODO ADD NAMES AND SOUNDS HERE

}

# loads all sound files at startup. 
# basically caches all of them
# to make playing faster on first runs
loaded_sounds = {}
for key, path in SOUND_MAP.items(): 
    loaded_sounds[key] = pygame.mixer.Sound(path)

# will be used later to prevent ear rape
last_request = ''

while True:
    # checks for events every .1 seconds to not kill CPU
    time.sleep(.1)

    # tries to find audio_request.txt and if it isnt made yet,
    # goes back to the top of the loop
    try: 
        with open('audio_request.txt', 'r') as file: 
            request = file.read().strip()
    except FileNotFoundError: continue

    # reloops if its empty and avoids repeated playback
    if request == '' or request == last_request: continue
    last_request = request

    # used to convert the file contents
    # into a dict format
    data = {}

    # turns 'volume=70' into key='volume', value='70' in the dict
    # LINES MUST ONLY HAVE ONE '='
    for line in request.splitlines():
        key, value = line.split('=')
        data[key] = value
    
    button_type = data.get('button_type', 'default')    # default sound is played if no provided button type
    volume = int(data.get('volume', 70))                # 70 is default vol if no provided int
    muted = data.get('muted', 'false') == 'true'        # converts string bools into actual bools

    if muted:
        response = (
            'status=success\n'
            'action=skipped\n'
            'reason=muted'
        )

    elif button_type in loaded_sounds:
        response = (
            'status=success\n'
            'action=played\n'
            f'sound={button_type}\n'
            f'effective_volume={volume / 100}'
        )

    else:
        requested_button_type = button_type
        button_type = 'default'
        response = (
            'status=error\n'
            'action=played_default\n'
            'reason=unknown_button_type\n'
            f'requested_button_type={requested_button_type}\n'
            f'sound={button_type}\n'
            f'effective_volume={volume / 100}'
        )

    if not muted:
        sound = loaded_sounds[button_type]
        effective_volume = volume / 100
        sound.set_volume(effective_volume)
        sound.play()

    # writes debugging info and status code back to main program
    with open('audio_response.txt', 'w') as file: file.write(response)