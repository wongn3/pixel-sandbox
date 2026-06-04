##### .txt MUST BE IN THIS FILE FORMAT #####
#####          CASE SENSITIVE          #####
'''
material_a=[material name]
material_b=[material name]
'''

import time

# each reaction rule maps a pair of materials to a result
# frozenset() makes order not matter hehe i love documentation:
# sand + water == water + sand
REACTION_RULES = {
    frozenset(['sand', 'water']): 'wet_sand',
    frozenset(['grass', 'water']): 'mud',
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

    # tries to find reaction_request.txt and if it isnt made yet,
    # goes back to the top of the loop
    try:
        with open('reaction_request.txt', 'r') as file:
            request = file.read().strip()
    except FileNotFoundError: continue

    # reloops if its empty
    if request == '': continue

    data = {}

    # turns 'material_a=mud' into key='material_a', value='mud' in the dict
    # LINES MUST ONLY HAVE ONE '='
    for line in request.splitlines():
        key, value = line.split('=')
        data[key] = value

    material_a = data.get('material_a')
    material_b = data.get('material_b')

    # ERROR CHECKING
    if not material_a or not material_b:
        response = (
            'status=error\n'
            'reaction=none\n'
            'reason=missing_material\n'
        )
    elif material_a not in VALID_MATERIALS:
        response = (
            'status=error\n'
            'reaction=none\n'
            f'reason=unknown_material\n'
            f'material={material_a}\n'
        )
    elif material_b not in VALID_MATERIALS:
        response = (
            'status=error\n'
            'reaction=none\n'
            f'reason=unknown_material\n'
            f'material={material_b}\n'
        )

    # SUCCESSFUL PAIRING
    else:
        material_pair = frozenset([material_a, material_b])

        if material_pair in REACTION_RULES:
            reaction = REACTION_RULES[material_pair]

            response = (
                'status=success\n'
                f'material_a={material_a}\n'
                f'material_b={material_b}\n'
                f'reaction={reaction}\n'
                f'message={material_a} and {material_b} react into {reaction}\n'
            )
        else:
            response = (
                'status=success\n'
                f'material_a={material_a}\n'
                f'material_b={material_b}\n'
                'reaction=none\n'
                'message=no reaction\n'
            )

    # writes debugging info and status code back to main program
    with open('reaction_response.txt', 'w') as file: file.write(response)
