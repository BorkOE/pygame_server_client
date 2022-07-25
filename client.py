import socket
import threading
import pygame as pg
import pickle
from settings import HOST_ADDR, HOST_PORT, start_pos

class Figure(pg.sprite.Sprite):
    '''This is the rectangle that the player get to controll'''
    def __init__(self, id, pos=start_pos):
        self.id = id
        self.image = pg.Surface((20, 20))
        self.image.fill('black')
        self.rect = self.image.get_rect()
        self.rect.topleft = pos
        self.speed = 7
    
    def update(self):
        move = False
        if pg.key.get_pressed()[pg.K_LEFT]:
            self.rect.x -= self.speed
            move = True
        if pg.key.get_pressed()[pg.K_RIGHT]:
            self.rect.x += self.speed
            move = True
        if pg.key.get_pressed()[pg.K_UP]:
            self.rect.y -= self.speed
            move = True
        if pg.key.get_pressed()[pg.K_DOWN]:
            self.rect.y += self.speed
            move = True
        return move 

    def draw(self, screen):
        screen.blit(self.image, self.rect)

# network client
client = None
if HOST_ADDR == "": 
    hostname = socket.gethostname()
    HOST_ADDR = socket.gethostbyname(hostname)
id = None
player_pos = {}
other_players = {}

def connect_to_server():
    global client, HOST_PORT, HOST_ADDR, id, player_pos
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
        client.connect((HOST_ADDR, HOST_PORT))                      # Connect to server

        client_name = socket.gethostname()
        client_msg = {'type':'connect', 'client_name':client_name}
        client.send(pickle.dumps(client_msg))                       # Send this computers name to server after connecting
        data = pickle.loads(client.recv(4096))                      # First respons from server is dict with out id and all currently connected players. (Empty dict if we are the first connection)
        id = data['id']
        player_pos = data['player_pos']

        # start a thread to keep receiving message from server
        threading._start_new_thread(receive_message_from_server, (client, "m"))
    except Exception as e:
        print(e)

def receive_message_from_server(sck, m):
    global player_pos
    while True:
        data = pickle.loads(sck.recv(4096))
        if not data: break

        if data['type'] == 'pos':                                       # Another player has moved, update their position
            other_players[data['player']].rect.topleft = data['pos']
        elif data['type'] == 'new_player':                              # A new player has joined
            instantiate_new_player(data['player'])
        elif data['type'] == 'kill':                                    # A player has left    
            del other_players[data['player']]

    sck.close()

def send_pos_to_server(pos):
    global id, client
    client_msg = {'type':'pos', 'player':id, 'pos':pos}
    client.send(pickle.dumps(client_msg))

def instantiate_other_players(player_pos):
    '''This instantiates already connected players'''
    global other_players
    for player, pos in player_pos.items():
        other_players.update({player:Figure(player, pos)})

def instantiate_new_player(id):
    '''This instantiates players that join while client is running'''
    print('A new player has connected!')
    other_players.update({str(id):Figure(id)})

def main():
    global player_pos
    # Pygame init
    pg.init()
    clock = pg.time.Clock()
    flags = pg.RESIZABLE
    screen = pg.display.set_mode((400, 300), flags)
    running = True
    pg.display.set_caption(f'Client')
    connect_to_server()

    player_figure = Figure(id)                  # Instantiate player figure
    instantiate_other_players(player_pos)       # Instantiate other players figures
    
    while running:
        screen.fill('white')

        for event in pg.event.get():
            if event.type == pg.QUIT:
                exit()
                break

        if player_figure.update():                          # Looks for user input, returns True if player moved figure
            send_pos_to_server(player_figure.rect.topleft)  # At input: send new position to server
        player_figure.draw(screen)                          # Draws player-figure on screen
        for other_player, figure in other_players.items():  # Draws other players on screen
            figure.draw(screen)


        pg.display.update()
        clock.tick(30) 

    pg.quit()


main()