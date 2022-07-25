# pygame_server_client
A minimal setup with a game server and pygame client. On client connection a rectangle spawns and is controlled by arrow keys. 
The server handles new connections and closed connections by relaying positional data and spawn/kill commands to clients.
For learning purposes. 

If client is on another computer than the server, change HOST_ADDR in settings to the host comupters ip (shown for example in server window).

The networking part and tkinter interface is based heavily on github user effiongcharles tutorial: 
https://github.com/effiongcharles/multi_user_chat_application_in_python
