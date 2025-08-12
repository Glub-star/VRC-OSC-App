from pythonosc import dispatcher, osc_server

def print_message(address, *args):
    print(f"Received {address}: {args}")

dispatcher = dispatcher.Dispatcher()
dispatcher.map("/*", print_message)  # catch everything for debugging

ip = "127.0.0.1"
port = 9001  # VRChat's OSC output

print(f"Listening for OSC messages on {ip}:{port}...")
server = osc_server.BlockingOSCUDPServer((ip, port), dispatcher)
server.serve_forever()
