import tkinter as tk
from tkinter import ttk
from tkinter.colorchooser import askcolor
import socket
import threading
from tkinter import simpledialog  # Import simpledialog for chat

# Server configuration
HOST = '10.1.17.93'
PORT = 5054

class WhiteboardClient:
    def __init__(self, root):
        self.root = root
        self.canvas = tk.Canvas(root, width=800, height=900, bg="white")
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.canvas.bind("<B1-Motion>", self.draw)
        self.canvas.bind("<ButtonRelease-1>", self.release)  # Bind mouse release event
        self.color = "black"
        self.drawing = False
        self.last_x = None
        self.last_y = None

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect_to_server()

        self.chat_client = ChatClient(root, self.client_socket)


    def connect_to_server(self):
        self.client_socket.connect((HOST, PORT))

        # Get username from user
        self.username = simpledialog.askstring("Username", "Enter your username:")
        if not self.username:
            self.username = "Anonymous"
        self.client_socket.send(self.username.encode('utf-8'))

        self.listen_thread = threading.Thread(target=self.receive_data)
        self.listen_thread.start()

    def receive_data(self):
        while True:
            try:
                data = self.client_socket.recv(1024).decode('utf-8')
                if data.startswith("CHAT:"):
                    message = data[5:]
                    self.chat_client.display_message(message)
                elif data.startswith("NEW_ROUND:"):
                    word = data[10:]
                    self.chat_client.display_message(f"New round started! Draw the word: {word}")
                elif data.startswith("TIME_UP:"):
                    word = data[8:]
                    self.chat_client.display_message(f"Time's up! The word was: {word}")
                    self.clear_screen()  # Clear the screen when time is up
                else:
                    try:
                        draw_data = data
                        coords = draw_data.split(",")
                        if len(coords) == 5:  # Ensure it's drawing data
                            x1, y1, x2, y2, color = coords[0], coords[1], coords[2], coords[3], coords[4]
                            self.canvas.create_line(x1, y1, x2, y2, fill=color, width=2)
                    except Exception as e:
                        print(f"Error interpreting drawing data: {e}")
            except Exception as e:
                print(f"Error receiving data: {e}")
                break

    def draw(self, event):
        if self.drawing and self.last_x is not None and self.last_y is not None:
            x, y = event.x, event.y
            self.canvas.create_line(self.last_x, self.last_y, x, y, fill=self.color, width=2)
            draw_data = f"{self.last_x},{self.last_y},{x},{y},{self.color}"
            self.client_socket.send(draw_data.encode('utf-8'))
        self.last_x = event.x
        self.last_y = event.y
        self.drawing = True

    def release(self, event):
        self.drawing = False
        self.last_x = None
        self.last_y = None

    def change_color(self):
        color = askcolor()
        self.color = color[1]

    def clear_screen(self):
        self.canvas.delete("all")  # Clear the canvas

class ChatClient:
    def __init__(self, root, client_socket):
        self.root = root
        self.client_socket = client_socket

        self.chat_display = tk.Text(root, state="disabled", wrap="word")
        self.chat_display.grid(row=1, column=0, sticky="nsew")

        self.entry_frame = tk.Frame(root)
        self.entry_frame.grid(row=2, column=0, sticky="nsew")

        msgbox = tk.Tk()
        msgbox_frame = msgbox  # tk.Frame(msgbox)
        msgbox.title('message box')
        self.message_entry = tk.Entry(msgbox_frame)
        self.message_entry.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        self.send_button = ttk.Button(msgbox_frame, text="Send", command=self.send_message)
        self.send_button.pack(side=tk.RIGHT)

    def send_message(self):
        message = self.message_entry.get().strip()
        if message:
            self.client_socket.send(f"CHAT:{message}".encode('utf-8'))
            self.message_entry.delete(0, tk.END)

    def display_message(self, message):
        self.chat_display.configure(state="normal")
        self.chat_display.insert(tk.END, message + "\n")
        self.chat_display.configure(state="disabled")

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Collaborative Whiteboard")

    whiteboard_client = WhiteboardClient(root)

    color_button = ttk.Button(root, text="Choose Color", command=whiteboard_client.change_color)
    color_button.grid(row=3, column=0, sticky="nsew")
    
    clear_button = ttk.Button(root, text="Clear Screen", command=whiteboard_client.clear_screen)
    clear_button.grid(row=4, column=0, sticky="nsew")


    root.grid_rowconfigure(0, weight=1)
    root.grid_rowconfigure(1, weight=1)
    root.grid_rowconfigure(2, weight=1)
    root.grid_columnconfigure(0, weight=1)

    root.mainloop()
