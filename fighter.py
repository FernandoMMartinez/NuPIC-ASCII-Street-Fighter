
#import game stuff
import curses
from time import sleep

#import NuPIC stuff
from nupic.frameworks.opf.modelfactory import ModelFactory
from nupic.data.inference_shifter import InferenceShifter
import model_params_fighter

#random seed, maybe this isnt needed
#random.seed()

#global game variables
height = 0
width = 0
p1_slugs = []
p2_slugs = []
player_health = 1000 #100
max_bullets = 10

#modified game functions
class Player(object):

    offset = 0

    player_sprite = """ o
/x\\
/ \\"""

    health = player_health

    def __init__(self, player_id, x_pos):
        self.player_id = player_id
        self.x_pos = x_pos

    def render(self, window):
        #drop move if out of space
        height, width= window.getmaxyx()
        new_y_pos_top = 11 + self.offset
        new_y_pos_bottom = 11 + 2 + self.offset
        if new_y_pos_top <= 0:
            self.offset += 1
        if new_y_pos_bottom >= height:
            self.offset -= 1
        for i, line in enumerate(self.player_sprite.splitlines()):
            window.addstr(11 + i + self.offset, self.x_pos, line, 0)



def draw_slugs(window):
    for slug in p1_slugs:
        window.addstr(slug[0], slug[1], '~', 0)
        slug[1] += slug[2]
    for slug in p2_slugs:
        window.addstr(slug[0], slug[1], '~', 0)
        slug[1] += slug[2]

def draw_health(window, player_1, player_2):
    window.addstr(0,0, "Player 1 health: {0} Player 2 health: {1}".format(player_1.health, player_2.health), 0)


def erase_lost_slugs(height, width):
    for i, slug in enumerate(p1_slugs):
        if slug[0] <= 0 or slug[0] >= height or slug[1] <= 0 or slug[1] >= width:
            p1_slugs.pop(i)
    for j, slug in enumerate(p2_slugs):
        if slug[0] <= 0 or slug[0] >= height or slug[1] <= 0 or slug[1] >= width:
            p2_slugs.pop(j)

def detect_collisions(player):
    for i, slug in enumerate(p1_slugs):
        if slug[1] >= player.x_pos \
                and slug[1] <= player.x_pos + 3 \
                and slug[0] >= (11 + player.offset) \
                and slug[0] <= (13 + player.offset):
            player.health -= 1
            p1_slugs.pop(i)
    for j, slug in enumerate(p2_slugs):
        if slug[1] >= player.x_pos \
                and slug[1] <= player.x_pos + 3 \
                and slug[0] >= (11+player.offset) \
                and slug[0] <= (13+player.offset):
            player.health -= 1
            p2_slugs.pop(j)


#my game functions
def set_dimensions(screen):
    global height, width
    height, width= screen.getmaxyx()

def reset_game(player_1, player_2):
    global p1_slugs, p2_slugs
    player_1.health = player_health
    player_2.health = player_health
    player_1.offset = 0
    player_2.offset = 0
    p1_slugs = []
    p2_slugs = []  

def check_victory(window, player_1, player_2):
    global width, height
    while(True):
        #if player_1.health < 1 and player_2.health < 1:
            #tie
        if player_1.health < 1:
            window.erase()
            window.addstr(10, (width / 2) -7, "NuPIC Wins!", 0)
            window.addstr(11, (width / 2) -8, "Press q to quit", 0)
            window.addstr(12, (width / 2) -9, "Press r to rematch", 0)
            key_pressed = window.getch()
            if key_pressed != -1:
                key_pressed = chr(key_pressed)
                if key_pressed == 'q':
                    curses.nocbreak()
                    curses.echo()
                    curses.endwin()
                    exit()
                if key_pressed == 'r':
                    return 0
        elif player_2.health < 1:
            window.erase()
            window.addstr(10, (width / 2) -7, "Player 1 Wins!", 0)
            window.addstr(11, (width / 2) -8, "Press q to quit", 0)
            window.addstr(12, (width / 2) -9, "Press r to rematch", 0)
            key_pressed = window.getch()
            if key_pressed != -1:
                key_pressed = chr(key_pressed)
                if key_pressed == 'q':
                    curses.nocbreak()
                    curses.echo()
                    curses.endwin()
                    exit()
                if key_pressed == 'r':
                    return 0
        else:
            break



#NuPIC functions go here
def createModel():
  return ModelFactory.create(model_params_fighter.MODEL_PARAMS)


#main game initialization and loop
def game_loop(screen):
    #global and local variables
    global height, width
    p1_prev_action = 0
    p2_prev_action = 0
    position_data = []

    #setup nupic
    model = createModel()
    model.enableInference({'predictionSteps': [57], 'predictedField': 'p1_pos', 'numRecords': 4000})
    inf_shift = InferenceShifter();

    #Set up window
    curses.curs_set(0)
    set_dimensions(screen)
    window = curses.newwin(height, width, 0, 0)
    window.nodelay(1)
    player_1 = Player(1, 10)
    player_2 = Player(2, width-10)
    player_1.render(window)
    player_2.render(window)

    #main game loop
    while(True):
        #check victory conditions
        if(check_victory(window, player_1, player_2) == 0):
            reset_game(player_1, player_2)


        #Do NuPIC input, output
        window.addstr(0,44, "Inputs: {0} {1} {2} {3}".format(player_1.offset, p1_prev_action, player_2.offset, p2_prev_action), 0)

        record = {'p1_pos': player_1.offset, 'p1_prevaction': p1_prev_action, 'p2_pos': player_2.offset, 'p2_prevaction': p2_prev_action}
        result = inf_shift.shift(model.run(record))

        inferred = result.inferences['multiStepBestPredictions'][57]

        #right now only tries to predict opponents position, nothing else
        if isinstance(inferred, float) == True:
            window.addstr(1,0, "NuPIC Output: {0}".format(inferred), 0)
            #ai goes here
            if(inferred > player_2.offset):
                player_2.offset += 1
            elif(inferred < player_2.offset):
                player_2.offset -= 1
            elif(inferred == player_2.offset):
                if(len(p2_slugs) < max_bullets):
                    p2_slugs.append([11 + 1 + player_2.offset, width-14, -1])


        #get input
        p1_prev_action = 0 #default is no action
        key_pressed = window.getch()
        if key_pressed != -1:
            key_pressed = chr(key_pressed)
            if key_pressed == 'q':
                curses.nocbreak()
                curses.echo()
                curses.endwin()
                exit()
            if key_pressed == 'e':
                #Move player 1 up
                player_1.offset -= 1
                p1_prev_action = -1 #says -1 at the boundary despite not being able to move anymore
            if key_pressed == 'd':
                #Fire a slug
                if(len(p1_slugs) < max_bullets): 
                    p1_slugs.append([11 + 1 + player_1.offset, 14, 1])
                    p1_prev_action = 2
            if key_pressed == 'c':
                #Move player 1 down
                player_1.offset += 1
                p1_prev_action = 1 #says 1 at the boundary despite not being able to move anymore
            if key_pressed == 'o':
                #Move player 1 up
                player_2.offset -= 1
            if key_pressed == 'k':
                #Fire a slug
                if(len(p2_slugs) < max_bullets):
                    p2_slugs.append([11 + 1 + player_2.offset, width-14, -1])
            if key_pressed == 'm':
                #Move player 1 down
                player_2.offset += 1

        #draw current frame
        window.erase()
        player_1.render(window)
        player_2.render(window)
        erase_lost_slugs(height, width)
        draw_slugs(window)
        detect_collisions(player_1)
        detect_collisions(player_2)
        draw_health(window, player_1, player_2)

        #grab variables for future use on NuPIC
        #position_data.append([])
        
        #delay to keep a constant 60 fps
        sleep(0.0167) #0.0167 translates to 60 fps


if __name__ == "__main__":
    curses.wrapper(game_loop)

