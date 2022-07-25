# This program creates launches a window and creates a server for socket communication.
# It keeps track of client connections and relays positional changes made by the players to all other clients

import tkinter as tk
import socket
import threading
# from figure import Figure
import pickle
from settings import start_pos, HOST_PORT

'''tkinter window'''
window = tk.Tk()
window.title("Server")

# Top frame consisting of two buttons widgets (i.e. btnStart, btnStop)
topFrame = tk.Frame(window)
btnStart = tk.Button(topFrame, text="Connect", command=lambda : start_server())
btnStart.pack(side=tk.LEFT)
btnStop = tk.Button(topFrame, text="Stop", command=lambda : stop_server(), state=tk.DISABLED)
btnStop.pack(side=tk.LEFT)
topFrame.pack(side=tk.TOP, pady=(5, 0))

# Middle frame consisting of two labels for displaying the host and port info
middleFrame = tk.Frame(window)
lblHost = tk.Label(middleFrame, text = "Host: X.X.X.X")
lblHost.pack(side=tk.LEFT)
lblPort = tk.Label(middleFrame, text = "Port:XXXX")
lblPort.pack(side=tk.LEFT)
middleFrame.pack(side=tk.TOP, pady=(5, 0))

# The client frame shows the client area
clientFrame = tk.Frame(window)
lblLine = tk.Label(clientFrame, text="**********Client List**********").pack()
scrollBar = tk.Scrollbar(clientFrame)
scrollBar.pack(side=tk.RIGHT, fill=tk.Y)
tkDisplay = tk.Text(clientFrame, height=15, width=30)
tkDisplay.pack(side=tk.LEFT, fill=tk.Y, padx=(5, 0))
scrollBar.config(command=tkDisplay.yview)
tkDisplay.config(yscrollcommand=scrollBar.set, background="#F4F6F7", highlightbackground="grey", state="disabled")
clientFrame.pack(side=tk.BOTTOM, pady=(5, 10))

'''Network'''
hostname = socket.gethostname()             
HOST_ADDR = socket.gethostbyname(hostname)  # Grabs the ip from router (I believe). Might not work as intended on every network setup.
server = None
client_name = " "
clients = []                                # Will hold all active client connections
clients_names = []                          # For displaying connected clients in server window
client_id = 0
player_pos = {}                             # All connected players positions, used for new clients
connection_player = {}                      # keeping track on which connection corresponds to which player

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print(socket.AF_INET)
    print(socket.SOCK_STREAM)

    server.bind((HOST_ADDR, HOST_PORT))
    server.listen(10)                                            # server is listening for client connection

    threading._start_new_thread(accept_clients, (server, " "))   # start a thread running the accept_clients function

    # Server window
    btnStart.config(state=tk.DISABLED)
    btnStop.config(state=tk.NORMAL)
    lblHost["text"] = "Host: " + HOST_ADDR
    lblPort["text"] = "Port: " + str(HOST_PORT)


# Stop server function
def stop_server():
    '''This is currently only cosmetic'''
    global server
    btnStart.config(state=tk.NORMAL)
    btnStop.config(state=tk.DISABLED)


def accept_clients(the_server, y):
    '''Continuously running function that looks for new client connections'''
    while True:
        client, addr = the_server.accept()
        clients.append(client)
        threading._start_new_thread(send_receive_client_message, (client, addr))    # On new connection, start thread that manages the connection

def send_receive_client_message(client_connection, client_ip_addr):
    global server, client_name, clients, client_id

    '''First connection with client'''
    data = pickle.loads(client_connection.recv(4096))                               # This is the first incoming data from client on establishing connection
    client_name = data['client_name']                                               # Grab client namne
    clients_names.append(client_name)                                               # Add client name to list with active clients
    update_client_names_display(clients_names)                                      # Update client names in server window
    print(f'connected to {client_name}')

    server_msg = {'type':'connect', 'id':str(client_id), 'player_pos':player_pos}   # First respons to client, send player positions
    client_connection.send(pickle.dumps(server_msg))
    connection_player.update({client_connection:str(client_id)})                    # Uppdate dict with connections and client id
    
    player_pos.update({str(client_id):start_pos})                                   # Add new player to player positions

    for c in clients:                                                               # Update existing clients on new player
        if c != client_connection:
            server_msg = {'type':'new_player', 'player':str(client_id)}             # Send data with the new players id, it will spawn in the defult position
            c.send(pickle.dumps(server_msg))

    client_id += 1                                                                  # Increment player id

    '''Continuous communication with client'''
    while True:
        try:
            data = pickle.loads(client_connection.recv(4096))   # Recive client communication
        except Exception as e:                                  # Crashes if client closes application, break loop
            print(e)
            break
        if not data: break

        if data['type'] == 'pos':                               # If the communication is tagged as a positional change
            player_pos.update({data['player']:data['pos']})     # Update the players position in the servers memory
            for c in clients:                                   # Update all other clients on the new position
                if c != client_connection:
                    server_msg = {'type':'pos', 'player':data['player'], 'pos':data['pos']}
                    c.send(pickle.dumps(server_msg))   

    # If connection is broken, remove associated data
    print('Closing connection')
    idx = get_client_index(clients, client_connection)
    del clients_names[idx]
    del clients[idx]
    del player_pos[str(connection_player[client_connection])]

    for c in clients:       # Ask clients to remove disconnected player from game
        if c != client_connection:
            server_msg = {'type':'kill', 'player':connection_player[client_connection]}
            c.send(pickle.dumps(server_msg))   

    client_connection.close()

    update_client_names_display(clients_names)  # update client names display

# Return the index of the current client in the list of clients
def get_client_index(client_list, curr_client):
    idx = 0
    for conn in client_list:
        if conn == curr_client:
            break
        idx = idx + 1

    return idx

# Update client name display when a new client connects OR
# When a connected client disconnects
def update_client_names_display(name_list):
    tkDisplay.config(state=tk.NORMAL)
    tkDisplay.delete('1.0', tk.END)

    for c in name_list:
        tkDisplay.insert(tk.END, c+"\n")
    tkDisplay.config(state=tk.DISABLED)

window.mainloop()