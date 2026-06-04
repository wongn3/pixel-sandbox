##### .txt MUST BE IN THIS FILE FORMAT  #####
#####          CASE SENSITIVE           #####
'''
material=[material]
'''

import time

MATERIAL_CATEGORIES = {
    # primary materials
    'sand': 'granular',
    'water': 'liquid',
    'grass': 'solid',

    # secondary materials
    'wet_sand': 'solid',
    'mud': 'solid',
}

MATERIAL_DESCRIPTIONS = {
    # primary materials
    'sand': 'Crushed rock and shells... Crunchy.',
    'water': 'H2O. Essential for life and mixing... And instant ramen.',
    'grass': 'Green. Go touch some, it feels nice.',

    # secondary materials
    'wet_sand': 'An even bigger pain to get rid of from your clothes than regular sand.',
    'mud': "Don't step in it. It might not be mud.",
}

VALID_MATERIALS = {
    # primary materials
    'sand',
    'water',
    'grass',

    # secondary materials
    'wet_sand',
    'mud',
}

while True:

    # checks for events every .1 seconds to not kill CPU
    time.sleep(.1)

    # tries to find validation_request.txt and if it isnt made yet,
    # goes back to the top of the loop
    try: 
        with open('material_info_request.txt', 'r') as file: 
            request = file.read().strip()
    except FileNotFoundError: continue

    if request == '': continue

    data = {}

    # turns 'volume=70' into key='volume', value='70' in the dict
    # LINES MUST ONLY HAVE ONE '='
    for line in request.splitlines():
        key, value = line.split('=')
        data[key] = value
    
    # gets queried material name, N/A if none provided
    material = str(data.get('material', 'N/A'))

    if material not in VALID_MATERIALS:
        response = (
            'status=error\n'
            f'input_material={material}\n'
            'reason=invalid_material'
        )
    else:
        material_category = str(MATERIAL_CATEGORIES.get(material))
        material_description = str(MATERIAL_DESCRIPTIONS.get(material))

        response = (
            'status=success\n'
            f'input_material={material}\n'
            f'material_category={material_category}\n'
            f'material_description={material_description}\n'
        )

    # writes debugging info and status code back to main program
    with open('material_info_response.txt', 'w') as file: file.write(response)
