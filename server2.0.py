import socket
import threading
import random
import time

# Server configuration
HOST = '10.1.17.93'
PORT = 5054

# List of Pictionary words
PICTIONARY_WORDS = ['apple', 'banana', 'car', 'dog', 'elephant', 'flower', 'guitar', 'house', 'island', 'jungle']

# Game state
current_word = None
drawing_frequency = {}  # Dictionary to count the frequency of drawing for each user
round_start_time = None
round_duration = 60  # Duration of each round in seconds
drawing_player = None

# Scores
scores = {}

# Create a socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen()

# Store connected clients
clients = []

def handle_client(client_socket, client_address):
    global drawing_frequency, drawing_player, current_word, scores
    
    print(f"New connection from {client_address}")
    client_socket.send("Enter your username: ".encode('utf-8'))
    username = client_socket.recv(1024).decode('utf-8').strip()
    scores[username] = 0
    clients.append((client_socket, username))
    drawing_frequency[username] = 0

    broadcast(f"{username} has joined the game")

    while True:
        try:
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                remove_client(client_socket)
                break
            
            if is_drawing_user(username):
                # Handle drawing data
                broadcast_draw(data)
            else:
                if data.startswith("CHAT:") and not is_drawing_user(username):
                    message = data[5:]
                    broadcast_chat(f"{username}: {message}")
                    if message.lower() == current_word:
                        update_scores(username)
                        broadcast_chat(f"{username} guessed the word correctly!")
                        start_new_round()
                elif data.startswith("CHAT:") and is_drawing_user(username):
                    message = data[5:]
                    broadcast_chat(f"{username}: {message}")
        except Exception as e:
            print(f"Error handling client data: {e}")
            remove_client(client_socket)
            break

    print(f"Connection from {client_address} closed")
    remove_client(client_socket)
    broadcast(f"{username} has left the game")
    update_drawing_frequency(username)
    del drawing_frequency[username]


def broadcast(message):
    for client_socket, _ in clients:
        try:
            client_socket.send(message.encode('utf-8'))
        except Exception as e:
            print(f"Error broadcasting message to client: {e}")
            
def broadcast_to_user(username, message):
    for client_socket, user in clients:
        if user == username:
            try:
                client_socket.send(message.encode('utf-8'))
            except Exception as e:
                print(f"Error broadcasting message to {username}: {e}")

def broadcast_chat(message):
    for client_socket, _ in clients:
        try:
            client_socket.send(f"CHAT:{message}".encode('utf-8'))
        except Exception as e:
            print(f"Error broadcasting chat message to client: {e}")

def broadcast_draw(data):
    for client_socket, _ in clients:
        try:
            client_socket.send(data.encode('utf-8'))
        except Exception as e:
            print(f"Error broadcasting draw data to client: {e}")

def remove_client(client_socket):
    for i, (client, _) in enumerate(clients):
        if client == client_socket:
            clients.pop(i)
            break

def select_word():
    return random.choice(PICTIONARY_WORDS)

def start_new_round():
    global current_word, round_start_time, drawing_player, drawing_frequency
    
    current_word = select_word()
    round_start_time = time.time()
    print("New round\n")
    # Update drawing frequency for the previous drawing player
    if drawing_player:
        drawing_frequency[drawing_player] += 1
    
    # Select new drawing player based on drawing frequency
    drawing_player = select_drawing_player()
    print(drawing_player)
    print(drawing_frequency)
    # Send message with the new round's word only to the drawing user
    broadcast_to_user(drawing_player, f"NEW_ROUND:{current_word}")
    
def select_drawing_player():
    global drawing_frequency
    
    # Find the user with the lowest drawing frequency
    min_frequency = min(drawing_frequency.values())
    eligible_players = [user for user, freq in drawing_frequency.items() if freq == min_frequency]
    
    # If all players have drawn once, reset their frequencies and choose a new drawing player
    if min_frequency > 0:
        drawing_frequency = {user: 0 for user in drawing_frequency}
        return random.choice(list(drawing_frequency.keys()))
    else:
        return random.choice(eligible_players)  # Choose randomly among players with the lowest frequency

def update_scores(username):
    if username in scores:
        scores[username] += 1
            
def end_round():
    global round_start_time
    broadcast(f"TIME_UP: {current_word}")
    round_start_time = None


def update_drawing_frequency(username):
    if username in drawing_frequency:
        drawing_frequency[username] += 1
    else:
        drawing_frequency[username] = 1

def is_drawing_user(username):
    global drawing_player
    if username == drawing_player:
        return True
    else:    
        return False

def game_loop():
    while True:
        if clients:
            start_new_round()

        while round_start_time and time.time() - round_start_time < round_duration:
            time.sleep(1)

        if round_start_time:
            end_round()

        print("Scores:")
        for username, score in scores.items():
            print(f"{username}: {score}")

        scores.clear()
        time.sleep(5)

def start_server():
    print(f"Server is running on {HOST}:{PORT}")
    threading.Thread(target=game_loop).start()

    while True:
        client_socket, client_address = server_socket.accept()
        client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
        client_thread.start()

if __name__ == "__main__":
    start_server()
