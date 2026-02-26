#!/usr/bin/env python3
"""
LV55: The Lightship Adventure
A text adventure set aboard Light Vessel 55, Bristol Channel, 1936.
"""

import sys
import textwrap
import random

# ─────────────────────────────────────────────
#  Utilities
# ─────────────────────────────────────────────

def wrap(text):
    for para in text.strip().split('\n'):
        print(textwrap.fill(para, width=72))

def hr():
    print('─' * 72)

def section(title):
    hr()
    print(f'  {title}')
    hr()

# ─────────────────────────────────────────────
#  World data
# ─────────────────────────────────────────────

LOCATIONS = {
    'gangway': {
        'name': 'Gangway',
        'desc': (
            "You stand on the swaying gangway between the dock and the hull "
            "of LV55. Grey Bristol Channel water slaps below. The rust-red "
            "hull looms to your right. Ahead, a hatch leads DOWN to the mess "
            "deck. A ladder climbs UP to the bridge."
        ),
        'exits': {'down': 'mess', 'up': 'bridge', 'back': 'dock'},
    },
    'dock': {
        'name': 'Harbourside Dock',
        'desc': (
            "The stone dock smells of tar and low tide. Gulls argue overhead. "
            "LV55 is moored alongside — her red hull and squat lantern mast "
            "unmistakable. The gangway leads ABOARD."
        ),
        'exits': {'aboard': 'gangway'},
    },
    'bridge': {
        'name': 'Bridge',
        'desc': (
            "The bridge is cluttered with charts, compasses, and a brass "
            "telegraph that hasn't moved in months. Salt-hazed windows look "
            "out over the Channel. A speaking tube leads DOWN to the engine "
            "room. The gangway is AFT."
        ),
        'exits': {'down': 'engine_room', 'aft': 'gangway'},
        'character': 'thorpe',
    },
    'mess': {
        'name': 'Mess Deck',
        'desc': (
            "A long table dominates the low-ceilinged room. The smell of "
            "boiled potatoes and engine oil is inescapable. A shelf holds "
            "several bottles — mostly empty. A door leads FORWARD to the "
            "galley, and a companion-way goes AFT to the aft cabin."
        ),
        'exits': {'forward': 'galley', 'aft': 'aft_cabin', 'up': 'gangway'},
        'character': 'jenkins',
    },
    'galley': {
        'name': 'Galley',
        'desc': (
            "The ship's tiny kitchen. A coal range ticks with heat. Pots "
            "hang from hooks. On the counter sits a basket of provisions. "
            "You can go AFT back to the mess."
        ),
        'exits': {'aft': 'mess'},
        'character': 'cook',
    },
    'engine_room': {
        'name': 'Engine Room',
        'desc': (
            "Enormous reciprocating machinery fills the space, currently "
            "still. Oil drips somewhere rhythmically. A metal ladder goes "
            "UP to the bridge."
        ),
        'exits': {'up': 'bridge'},
    },
    'aft_cabin': {
        'name': "Captain's Aft Cabin",
        'desc': (
            "A snug cabin. A bunk, a writing desk, a porthole showing grey "
            "sky. On the desk: a half-empty bottle of Burgundy and a framed "
            "photograph of two magnificent red cats. A locked CHEST sits "
            "beneath the bunk. The mess deck is FORWARD."
        ),
        'exits': {'forward': 'mess'},
    },
}

ITEMS = {
    'red_wine': {
        'name': 'bottle of red wine',
        'desc': 'A fine Bordeaux, still corked. Thorpe will approve.',
        'location': 'galley',
    },
    'cucumber': {
        'name': 'cucumber',
        'desc': 'A pale, watery cucumber from the provisions basket. Revolting.',
        'location': 'galley',
    },
    'log_book': {
        'name': 'log book',
        'desc': "The ship's log. Entries in Thorpe's cramped hand, ending abruptly in 1929.",
        'location': 'bridge',
    },
    'chest_key': {
        'name': 'chest key',
        'desc': 'A small brass key. Fits the chest in the captain\'s cabin.',
        'location': None,  # given by Thorpe when trust is earned
    },
    'cat_certificate': {
        'name': 'cat breeding certificate',
        'desc': (
            "An official-looking document: 'Certificate of Breeding Intent — "
            "Felis catus, Red (Marmalade), Bristol Fanciers Society.' "
            "Thorpe has been planning this for years."
        ),
        'location': None,  # in chest
    },
    'ship_log_1929': {
        'name': 'secret log entry',
        'desc': (
            "A folded sheet inside the chest. It reads: 'Oct 14, 1929 — "
            "Offered cucumber sandwich by relief crew. Refused. Always refuse. "
            "The cucumber is the enemy of good sense and good digestion.' "
            "Thorpe's philosophy in writing."
        ),
        'location': None,  # in chest
    },
}

CHARACTERS = {
    'thorpe': {
        'name': 'Captain Thorpe',
        'desc': (
            "A broad-shouldered man with dark wavy hair going silver at the "
            "temples, and a neat soul-patch goatee. He regards you with the "
            "measured suspicion of a man who has been let down by newcomers "
            "before. His eyes are quick and dark. He smells faintly of "
            "Burgundy."
        ),
        'trust': 0,        # 0-3; at 3 he gives the chest key
        'talked': False,
    },
    'jenkins': {
        'name': 'Able Seaman Jenkins',
        'desc': (
            "A wiry, sun-leathered man with a gap-toothed grin. He's "
            "nursing a mug of tea and seems pleased to have company."
        ),
        'talked': False,
    },
    'cook': {
        'name': 'Ship\'s Cook, Mrs. Hobbs',
        'desc': (
            "A formidable woman in a flour-dusted apron. She eyes the "
            "provisions basket protectively."
        ),
        'talked': False,
    },
}

# ─────────────────────────────────────────────
#  Game state
# ─────────────────────────────────────────────

class GameState:
    def __init__(self):
        self.location = 'dock'
        self.inventory = set()
        self.visited = set()
        self.flags = {
            'chest_open': False,
            'game_won': False,
            'cucumber_offered': False,
        }
        self.turns = 0

STATE = GameState()

# ─────────────────────────────────────────────
#  Output helpers
# ─────────────────────────────────────────────

def describe_location():
    loc = LOCATIONS[STATE.location]
    section(loc['name'])
    wrap(loc['desc'])

    # items here
    here = [v for v in ITEMS.values()
            if v['location'] == STATE.location]
    if here:
        print()
        print('You can see: ' + ', '.join(i['name'] for i in here) + '.')

    # character here
    char_key = loc.get('character')
    if char_key:
        char = CHARACTERS[char_key]
        print()
        print(f'{char["name"]} is here.')

    # exits
    exits = list(loc['exits'].keys())
    print()
    print('Exits: ' + ', '.join(exits).upper())

# ─────────────────────────────────────────────
#  Command handlers
# ─────────────────────────────────────────────

def do_go(direction):
    loc = LOCATIONS[STATE.location]
    exits = loc['exits']
    if direction not in exits:
        wrap(f'You cannot go {direction.upper()} from here.')
        return
    dest = exits[direction]
    STATE.location = dest
    if dest not in STATE.visited:
        STATE.visited.add(dest)
    describe_location()


def do_look(args):
    if not args:
        describe_location()
        return
    target = ' '.join(args)
    # look at item in room or inventory
    for key, item in ITEMS.items():
        if target in item['name'].lower():
            if item['location'] == STATE.location or key in STATE.inventory:
                wrap(item['desc'])
                return
    # look at character
    for key, char in CHARACTERS.items():
        if target in char['name'].lower():
            if LOCATIONS[STATE.location].get('character') == key:
                wrap(char['desc'])
                return
    wrap("You don't see that here.")


def do_take(args):
    if not args:
        wrap('Take what?')
        return
    target = ' '.join(args)
    for key, item in ITEMS.items():
        if target in item['name'].lower() and item['location'] == STATE.location:
            STATE.inventory.add(key)
            item['location'] = None
            wrap(f'You pick up the {item["name"]}.')
            return
    wrap("You don't see that here.")


def do_inventory():
    if not STATE.inventory:
        wrap('You are carrying nothing.')
        return
    print('You are carrying:')
    for key in STATE.inventory:
        print(f'  - {ITEMS[key]["name"]}')


def do_talk(args):
    loc = LOCATIONS[STATE.location]
    char_key = loc.get('character')
    if not char_key:
        wrap('There is no one here to talk to.')
        return

    char = CHARACTERS[char_key]

    if char_key == 'thorpe':
        _talk_thorpe()
    elif char_key == 'jenkins':
        _talk_jenkins()
    elif char_key == 'cook':
        _talk_cook()


def _talk_thorpe():
    thorpe = CHARACTERS['thorpe']
    trust = thorpe['trust']

    if not thorpe['talked']:
        thorpe['talked'] = True
        wrap(
            '"You\'re new," says Thorpe. It is not a warm observation. He '
            'crosses his arms and surveys you from boot to cap. "This is my '
            'vessel. I run a tidy ship. I don\'t know you, which means I don\'t '
            'trust you. Earn it." He turns back to his charts.'
        )
        return

    if trust == 0:
        wrap(
            'Thorpe glances at you sideways. "Still here? Hmph. Talk to the '
            'crew if you\'re at a loose end. And if you\'re thinking of '
            'bringing any cucumber aboard — don\'t."'
        )
    elif trust == 1:
        wrap(
            '"You\'re not entirely useless," Thorpe concedes, refilling his '
            'glass. "I\'ll give you that much."'
        )
    elif trust == 2:
        wrap(
            'Thorpe nods slowly. "Almost there. Do right by me once more '
            'and I might show you something worth seeing."'
        )
    elif trust >= 3:
        if not STATE.flags['chest_open']:
            wrap(
                'Thorpe reaches into his breast pocket and produces a small '
                'brass key. "You\'ve proved yourself. Chest under the bunk in '
                'my cabin. Take a look. But mind — don\'t touch the Burgundy."'
            )
            ITEMS['chest_key']['location'] = None
            STATE.inventory.add('chest_key')
            wrap('You receive the chest key.')
        else:
            wrap(
                '"Fine work," says Thorpe simply. He pours two glasses and '
                'hands one to you without a word.'
            )


def _talk_jenkins():
    jenkins = CHARACTERS['jenkins']
    if not jenkins['talked']:
        jenkins['talked'] = True
        wrap(
            '"Ahh, new face! Grand." Jenkins shuffles along the bench to make '
            'room. "Don\'t mind the Captain — he\'s alright once he knows you. '
            'Tip: he loves a decent red. Hates newcomers who don\'t pull their '
            'weight. And whatever you do, don\'t mention cucumbers. I once saw '
            'a man offer him a cucumber sandwich and I still can\'t talk about '
            'what happened next." He sips his tea with great significance.'
        )
    else:
        wrap(
            '"The Captain\'s got this dream, see," Jenkins says conspiratorially. '
            '"Wants to breed red cats. Proper red ones — not ginger, mind. Red. '
            'He\'s been writing to the Bristol Fanciers Society for years. Don\'t '
            'laugh — he takes it very seriously."'
        )


def _talk_cook():
    cook = CHARACTERS['cook']
    if not cook['talked']:
        cook['talked'] = True
        wrap(
            '"Help yourself to anything in the basket," Mrs. Hobbs says, '
            '"except the cucumber. I was going to throw it out anyway — the '
            'Captain won\'t have them aboard. Threw the last one overboard in '
            '\'31. Said it was an affront to serious drinking." She gestures '
            'at the wine bottle on the shelf. "That Bordeaux there — he\'s been '
            'saving it. But if you were to present it to him properly, I think '
            'he\'d warm to you."'
        )
    else:
        wrap('"The wine, dearie. That\'s the ticket."')


def do_give(args):
    if not args:
        wrap('Give what to whom?')
        return

    loc = LOCATIONS[STATE.location]
    char_key = loc.get('character')
    if not char_key:
        wrap('There is no one here to give anything to.')
        return

    target = ' '.join(args)
    item_key = None
    for key in STATE.inventory:
        if target in ITEMS[key]['name'].lower():
            item_key = key
            break

    if not item_key:
        wrap("You don't have that.")
        return

    if char_key == 'thorpe':
        _give_thorpe(item_key)
    else:
        wrap(f'{CHARACTERS[char_key]["name"]} shakes their head politely.')


def _give_thorpe(item_key):
    thorpe = CHARACTERS['thorpe']
    item = ITEMS[item_key]

    if item_key == 'red_wine':
        STATE.inventory.remove(item_key)
        item['location'] = 'bridge'
        thorpe['trust'] = min(thorpe['trust'] + 2, 3)
        wrap(
            'Thorpe\'s eyes light up — just briefly — as you present the '
            'Bordeaux. He takes it with both hands, examines the label, and '
            'gives a single approving nod. "Good vintage. Good instincts." '
            'He uncorks it on the spot. Trust gained.'
        )
        _check_win()

    elif item_key == 'cucumber':
        STATE.flags['cucumber_offered'] = True
        wrap(
            'Thorpe stares at the cucumber in your outstretched hand. The '
            'silence on the bridge becomes geological. His left eye twitches. '
            '"Get. That. Off. My. Ship." His voice is very quiet, which is '
            'somehow worse than shouting. "And don\'t come back to this bridge '
            'until you\'ve disposed of it properly."'
        )
        thorpe['trust'] = max(thorpe['trust'] - 1, 0)

    elif item_key == 'log_book':
        wrap(
            'Thorpe takes the log book, opens it, and closes it again '
            'immediately. Something crosses his face — regret, maybe. '
            '"Where did you find this?" He sets it carefully on the chart '
            'table. "Leave it." A pause. "...Thank you."'
        )
        STATE.inventory.remove(item_key)
        item['location'] = 'bridge'
        thorpe['trust'] = min(thorpe['trust'] + 1, 3)
        _check_win()

    else:
        wrap('Thorpe looks at it. "I have no use for that."')


def do_open(args):
    if not args:
        wrap('Open what?')
        return
    target = ' '.join(args)
    if 'chest' in target:
        if STATE.location != 'aft_cabin':
            wrap("There's no chest here.")
            return
        if 'chest_key' not in STATE.inventory:
            wrap(
                'The chest is locked. You need a key.'
            )
            return
        if STATE.flags['chest_open']:
            wrap('The chest is already open.')
            return
        STATE.flags['chest_open'] = True
        wrap(
            'You fit the brass key to the lock and the chest opens with a '
            'satisfying click. Inside you find two items.'
        )
        ITEMS['cat_certificate']['location'] = 'aft_cabin'
        ITEMS['ship_log_1929']['location'] = 'aft_cabin'
        describe_location()
        _check_win()
    else:
        wrap("You can't open that.")


def do_drop(args):
    if not args:
        wrap('Drop what?')
        return
    target = ' '.join(args)
    for key in list(STATE.inventory):
        if target in ITEMS[key]['name'].lower():
            STATE.inventory.remove(key)
            ITEMS[key]['location'] = STATE.location
            wrap(f'You drop the {ITEMS[key]["name"]}.')
            if key == 'cucumber' and STATE.location != 'bridge':
                wrap('Good riddance, probably.')
            return
    wrap("You're not carrying that.")


def do_throw(args):
    if not args:
        wrap('Throw what?')
        return
    target = ' '.join(args)
    for key in list(STATE.inventory):
        if target in ITEMS[key]['name'].lower():
            if 'cucumber' in key:
                STATE.inventory.remove(key)
                ITEMS[key]['location'] = None
                wrap(
                    'You hurl the cucumber over the rail. It hits the grey '
                    'Channel water with a dull plop and sinks immediately, as '
                    'cucumbers deserve to.'
                )
                if STATE.flags['cucumber_offered']:
                    wrap(
                        'Somewhere above, you hear Thorpe grunt. It might '
                        'be approval.'
                    )
            else:
                wrap(f'You give the {ITEMS[key]["name"]} a little toss. Satisfying.')
            return
    wrap("You're not carrying that.")


def _check_win():
    thorpe = CHARACTERS['thorpe']
    if thorpe['trust'] >= 3 and STATE.flags['chest_open']:
        STATE.flags['game_won'] = True
        print()
        hr()
        wrap(
            'That evening, Thorpe sits across from you in the mess with two '
            'glasses of Burgundy. The lantern sways. Jenkins is singing '
            'something tuneless in the galley.'
        )
        print()
        wrap(
            '"You\'ll do," says Thorpe at last. High praise. He raises his '
            'glass. "To red cats. To LV55. And to never, ever cucumbers."'
        )
        print()
        wrap('You drink. The Channel rolls on outside.')
        print()
        wrap(
            'Somewhere in the Bristol Fanciers Society records, a letter '
            'is already being drafted about the classification of a new '
            'breed. Captain Thorpe\'s dream is one step closer.'
        )
        print()
        section('YOU HAVE WON — LV55 END')
        sys.exit(0)


# ─────────────────────────────────────────────
#  Command parser
# ─────────────────────────────────────────────

DIRECTION_ALIASES = {
    'n': 'north', 's': 'south', 'e': 'east', 'w': 'west',
    'u': 'up', 'd': 'down', 'f': 'forward', 'a': 'aft', 'b': 'back',
    'north': 'north', 'south': 'south', 'east': 'east', 'west': 'west',
    'up': 'up', 'down': 'down', 'forward': 'forward', 'aft': 'aft',
    'back': 'back', 'aboard': 'aboard',
}

def parse(raw):
    words = raw.strip().lower().split()
    if not words:
        return
    verb = words[0]
    args = words[1:]

    if verb in DIRECTION_ALIASES:
        do_go(DIRECTION_ALIASES[verb])
    elif verb in ('go', 'move', 'walk', 'head'):
        if args:
            do_go(DIRECTION_ALIASES.get(args[0], args[0]))
        else:
            wrap('Go where?')
    elif verb in ('look', 'l', 'examine', 'x', 'inspect'):
        # strip 'at' from "look at X"
        if args and args[0] == 'at':
            args = args[1:]
        do_look(args)
    elif verb in ('take', 'get', 'pick', 'grab'):
        if args and args[0] == 'up':
            args = args[1:]
        do_take(args)
    elif verb in ('drop', 'put', 'place'):
        do_drop(args)
    elif verb in ('throw', 'hurl', 'toss', 'chuck'):
        do_throw(args)
    elif verb in ('inv', 'i', 'inventory', 'bag', 'pockets'):
        do_inventory()
    elif verb in ('talk', 'speak', 'chat', 'ask'):
        do_talk(args)
    elif verb in ('give', 'offer', 'hand', 'present'):
        do_give(args)
    elif verb in ('open', 'unlock'):
        do_open(args)
    elif verb in ('help', '?', 'h'):
        do_help()
    elif verb in ('quit', 'exit', 'q'):
        wrap('You step back onto the dockside. The Channel rolls on.')
        sys.exit(0)
    else:
        responses = [
            "That doesn't seem to do anything.",
            "You consider it, then think better of it.",
            "Perhaps not.",
            "The ship offers no response.",
        ]
        wrap(random.choice(responses))


def do_help():
    section('COMMANDS')
    commands = [
        ('NORTH / SOUTH / UP / DOWN / FORWARD / AFT', 'Move in a direction'),
        ('LOOK [thing]',      'Describe your surroundings or examine something'),
        ('TAKE [thing]',      'Pick something up'),
        ('DROP [thing]',      'Put something down'),
        ('THROW [thing]',     'Hurl something (ideal for cucumbers)'),
        ('INVENTORY / I',     'Check what you\'re carrying'),
        ('TALK',              'Talk to whoever is in the room'),
        ('GIVE [thing]',      'Give something to the person in the room'),
        ('OPEN [thing]',      'Open something'),
        ('QUIT',              'Leave the ship'),
    ]
    for cmd, desc in commands:
        print(f'  {cmd:<40} {desc}')
    hr()


# ─────────────────────────────────────────────
#  Main
# ─────────────────────────────────────────────

def intro():
    print()
    print('  ┌──────────────────────────────────────────────────────────┐')
    print('  │                                                          │')
    print('  │              L V 5 5 : T H E  L I G H T S H I P        │')
    print('  │                                                          │')
    print('  │          Bristol Channel  •  Autumn 1936                 │')
    print('  │                                                          │')
    print('  └──────────────────────────────────────────────────────────┘')
    print()
    wrap(
        'The tide is out. LV55 sits low on the grey water, her red hull '
        'dulled with salt. You\'ve been sent aboard as replacement crew — '
        'or so your papers say. Nobody on this ship knows you yet, and '
        'that matters more than you might think.'
    )
    print()
    wrap(
        'Win the trust of Captain Thorpe and discover the secrets of LV55. '
        'Type HELP for commands.'
    )
    print()


def main():
    intro()
    STATE.visited.add('dock')
    describe_location()

    while True:
        print()
        try:
            raw = input('> ').strip()
        except (EOFError, KeyboardInterrupt):
            print()
            wrap('You step back onto the dockside. The Channel rolls on.')
            break
        if raw:
            parse(raw)
            STATE.turns += 1


if __name__ == '__main__':
    main()
