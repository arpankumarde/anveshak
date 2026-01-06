import time
import threading
from flask import Flask, request, jsonify
import socketio

app = Flask(__name__)

# Store active WebSocket connections
active_connections = {}


def create_socketio_client(ws_url: str, connection_id: str):
    """Create and manage a Socket.IO client connection."""
    # Parse the WebSocket URL to get the base URL
    # Handle both ws:// and http:// formats
    if ws_url.startswith('ws://'):
        base_url = ws_url.replace('ws://', 'http://')
    elif ws_url.startswith('wss://'):
        base_url = ws_url.replace('wss://', 'https://')
    else:
        base_url = ws_url
    
    # Remove /socket.io if present in the URL
    if base_url.endswith('/socket.io'):
        base_url = base_url[:-10]
    
    # Remove trailing slash if present
    base_url = base_url.rstrip('/')
    
    print(f"Attempting to connect to: {base_url}")
    
    # Create client with connection options
    sio = socketio.Client(
        reconnection=True,
        reconnection_attempts=5,
        reconnection_delay=1,
        reconnection_delay_max=5
    )
    
    connection_established = threading.Event()
    connection_error = [None]  # Use list to allow modification in nested functions
    
    @sio.event
    def connect():
        print(f"✓ Connected to WebSocket server: {ws_url}")
        active_connections[connection_id]['connected'] = True
        active_connections[connection_id]['error'] = None
        connection_established.set()
    
    @sio.event
    def disconnect():
        print(f"✗ Disconnected from WebSocket server: {ws_url}")
        active_connections[connection_id]['connected'] = False
    
    @sio.event
    def connect_error(data):
        error_msg = str(data) if data else "Unknown connection error"
        print(f"✗ Connection error to {ws_url}: {error_msg}")
        active_connections[connection_id]['connected'] = False
        active_connections[connection_id]['error'] = error_msg
        connection_error[0] = error_msg
        connection_established.set()  # Set event even on error to unblock
    
    @sio.on('*')
    def catch_all(event, *args):
        """Catch all events for logging purposes."""
        print(f"Received event '{event}' from {ws_url}: {args}")
        # Store logs in the connection info
        if connection_id in active_connections:
            if 'logs' not in active_connections[connection_id]:
                active_connections[connection_id]['logs'] = []
            active_connections[connection_id]['logs'].append({
                'event': event,
                'data': args,
                'timestamp': time.time()
            })
    
    try:
        # Store client before connecting
        active_connections[connection_id]['client'] = sio
        
        # Attempt connection
        print(f"Connecting to {base_url}...")
        sio.connect(base_url, wait_timeout=20)
        
        # Wait for connection to be established or fail (with timeout)
        if connection_established.wait(timeout=25):
            if connection_error[0]:
                # Connection failed
                active_connections[connection_id]['error'] = connection_error[0]
                if sio.connected:
                    sio.disconnect()
            else:
                # Connection successful
                print(f"Connection established to {ws_url}")
                
                # Start ping thread to keep connection alive
                def ping_loop():
                    while active_connections.get(connection_id, {}).get('connected', False) and sio.connected:
                        try:
                            time.sleep(30)
                            if active_connections.get(connection_id, {}).get('connected', False) and sio.connected:
                                sio.emit('ping')
                                print(f"Sent ping to {ws_url}")
                        except Exception as e:
                            print(f"Error sending ping to {ws_url}: {e}")
                            break
                
                ping_thread = threading.Thread(target=ping_loop, daemon=True)
                ping_thread.start()
                active_connections[connection_id]['ping_thread'] = ping_thread
        else:
            # Connection timeout
            error_msg = "Connection timeout - server did not respond within 25 seconds"
            print(f"✗ {error_msg}")
            active_connections[connection_id]['connected'] = False
            active_connections[connection_id]['error'] = error_msg
            if sio.connected:
                sio.disconnect()
        
    except Exception as e:
        error_msg = f"Failed to connect to {ws_url}: {str(e)}"
        print(f"✗ {error_msg}")
        active_connections[connection_id]['connected'] = False
        active_connections[connection_id]['error'] = error_msg
        try:
            if sio.connected:
                sio.disconnect()
        except:
            pass  # Ignore disconnect errors if already disconnected


@app.route('/api/websocket/add', methods=['POST'])
def add_websocket():
    """Add or update a WebSocket connection."""
    data = request.get_json()
    
    if not data or 'url' not in data:
        return jsonify({'error': 'Missing required field: url'}), 400
    
    ws_url = data['url']
    connection_id = data.get('id', 'default')  # Allow custom IDs for multiple connections
    
    # Validate URL format
    if not (ws_url.startswith('ws://') or ws_url.startswith('wss://') or 
            ws_url.startswith('http://') or ws_url.startswith('https://')):
        return jsonify({'error': 'Invalid URL format. Must start with ws://, wss://, http://, or https://'}), 400
    
    # If connection already exists, disconnect it first
    if connection_id in active_connections:
        existing_conn = active_connections[connection_id]
        if 'client' in existing_conn and existing_conn['client'].connected:
            existing_conn['client'].disconnect()
    
    # Create new connection entry
    active_connections[connection_id] = {
        'url': ws_url,
        'connected': False,
        'error': None,
        'logs': []
    }
    
    # Start connection in a separate thread
    connection_thread = threading.Thread(
        target=create_socketio_client,
        args=(ws_url, connection_id),
        daemon=True
    )
    connection_thread.start()
    
    return jsonify({
        'message': 'WebSocket connection initiated',
        'connection_id': connection_id,
        'url': ws_url,
        'status': 'connecting'
    }), 200


@app.route('/api/websocket/status', methods=['GET'])
def get_websocket_status():
    """Get status of all WebSocket connections."""
    connection_id = request.args.get('id', None)
    
    if connection_id:
        if connection_id not in active_connections:
            return jsonify({'error': 'Connection not found'}), 404
        conn = active_connections[connection_id]
        return jsonify({
            'connection_id': connection_id,
            'url': conn['url'],
            'connected': conn.get('connected', False),
            'error': conn.get('error'),
            'log_count': len(conn.get('logs', []))
        }), 200
    else:
        # Return all connections
        status = {}
        for conn_id, conn in active_connections.items():
            status[conn_id] = {
                'url': conn['url'],
                'connected': conn.get('connected', False),
                'error': conn.get('error'),
                'log_count': len(conn.get('logs', []))
            }
        return jsonify(status), 200


@app.route('/api/websocket/remove', methods=['DELETE'])
def remove_websocket():
    """Remove a WebSocket connection."""
    data = request.get_json() or {}
    connection_id = data.get('id', request.args.get('id', 'default'))
    
    if connection_id not in active_connections:
        return jsonify({'error': 'Connection not found'}), 404
    
    conn = active_connections[connection_id]
    
    # Disconnect if connected
    if 'client' in conn and conn['client'].connected:
        conn['client'].disconnect()
    
    # Remove from active connections
    del active_connections[connection_id]
    
    return jsonify({
        'message': 'WebSocket connection removed',
        'connection_id': connection_id
    }), 200


@app.route('/api/websocket/logs', methods=['GET'])
def get_logs():
    """Get logs from a WebSocket connection."""
    connection_id = request.args.get('id', 'default')
    
    if connection_id not in active_connections:
        return jsonify({'error': 'Connection not found'}), 404
    
    conn = active_connections[connection_id]
    logs = conn.get('logs', [])
    
    # Optionally limit the number of logs returned
    limit = request.args.get('limit', type=int)
    if limit:
        logs = logs[-limit:]
    
    return jsonify({
        'connection_id': connection_id,
        'logs': logs,
        'total_count': len(conn.get('logs', []))
    }), 200


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok'}), 200


def main():
    print("Starting Anveshak server...")
    app.run(host='0.0.0.0', port=8000, debug=True)


if __name__ == "__main__":
    main()
