import socket
import threading
import struct

HOST = '10.206.94.191'
PORT = 5555

# Thread-safe client registry
clients = {}
clients_lock = threading.Lock()

def broadcast(data, sender_socket):
    """Sends data to all connected clients except the sender."""
    with clients_lock:
        for client_id, client_socket in list(clients.items()):
            if client_socket != sender_socket:
                try:
                    client_socket.sendall(data)
                except:
                    print(f"Removing disconnected client: {client_id}")
                    try:
                        client_socket.close()
                    except:
                        pass
                    del clients[client_id]

def handle_client(client_socket, client_address):
    """Listens continuously for incoming packet frames from a specific client."""
    print(f"New connection thread started for {client_address}")
    header_size = 5

    while True:
        try:
            # 1. Extract the 5-byte network header
            header = b""
            while len(header) < header_size:
                chunk = client_socket.recv(header_size - len(header))
                if not chunk:
                    break
                header += chunk
            
            if len(header) < header_size:
                break

            # Unpack: Type (1 byte), Size (4 bytes)
            msg_type, size = struct.unpack("!BL", header)

            # 2. Extract the complete payload based on the header's instructions
            payload = b""
            while len(payload) < size:
                chunk = client_socket.recv(size - len(payload))
                if not chunk:
                    break
                payload += chunk

            if len(payload) < size:
                break

            # 3. Relay the full constructed packet downstream to other clients
            full_packet = header + payload
            broadcast(full_packet, client_socket)

        except ConnectionResetError:
            break
        except Exception as e:
            print(f"Error handling data stream from {client_address}: {e}")
            break

    # Session Teardown
    print(f"Client {client_address} left the session.")
    with clients_lock:
        for client_id, sock in list(clients.items()):
            if sock == client_socket:
                del clients[client_id]
                break
    client_socket.close()

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(10)
    print(f"Zoom Clone Server actively listening on port {PORT}...")

    client_counter = 0
    try:
        while True:
            client_socket, client_address = server.accept()
            client_counter += 1
            print(f"Connection established with {client_address} -> User-{client_counter}")
            
            with clients_lock:
                clients[f"User-{client_counter}"] = client_socket
                
            threading.Thread(target=handle_client, args=(client_socket, client_address), daemon=True).start()
    except KeyboardInterrupt:
        print("\nShutting down server cluster.")
    finally:
        server.close()

if __name__ == "__main__":
    main()
    
    