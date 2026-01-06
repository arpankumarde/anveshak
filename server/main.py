import time
import threading
import logging
import os
from flask import Flask, request, jsonify
from bson import ObjectId
from datetime import datetime, timedelta
from typing import Optional
import socketio
from log_processor import log_processor
from db import db_manager
from debug_endpoints import debug_bp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = Flask(__name__)

# Register debug blueprint
app.register_blueprint(debug_bp)

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
            log_entry = {
                'event': event,
                'data': args,
                'timestamp': time.time()
            }
            active_connections[connection_id]['logs'].append(log_entry)
            
            # Send to log processor for analysis
            try:
                log_processor.add_log(log_entry, connection_id)
            except Exception as e:
                print(f"Error processing log: {e}")
    
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


# ==================== Clusters Endpoints ====================

@app.route('/api/clusters', methods=['GET'])
def get_clusters():
    """Get clusters with optional filtering."""
    try:
        cluster_type = request.args.get('type')  # pii, debug, error, etc.
        limit = request.args.get('limit', type=int, default=100)
        skip = request.args.get('skip', type=int, default=0)
        requires_review = request.args.get('requires_review', type=bool)
        
        query = {}
        if cluster_type:
            query['cluster_type'] = cluster_type
        if requires_review is not None:
            query['requires_review'] = requires_review
        
        clusters = list(db_manager.db.clusters.find(query)
                       .sort('created_at', -1)
                       .skip(skip)
                       .limit(limit))
        
        # Convert ObjectId to string
        for cluster in clusters:
            cluster['_id'] = str(cluster['_id'])
            if 'log_ids' in cluster:
                cluster['log_ids'] = [str(log_id) for log_id in cluster['log_ids']]
        
        total = db_manager.db.clusters.count_documents(query)
        
        return jsonify({
            'clusters': clusters,
            'total': total,
            'limit': limit,
            'skip': skip
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/clusters/<cluster_id>', methods=['GET'])
def get_cluster(cluster_id):
    """Get a specific cluster by ID."""
    try:
        cluster = db_manager.db.clusters.find_one({'_id': ObjectId(cluster_id)})
        if not cluster:
            return jsonify({'error': 'Cluster not found'}), 404
        
        cluster['_id'] = str(cluster['_id'])
        if 'log_ids' in cluster:
            cluster['log_ids'] = [str(log_id) for log_id in cluster['log_ids']]
        
        return jsonify(cluster), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Insights Endpoints ====================

@app.route('/api/insights', methods=['GET'])
def get_insights():
    """Get insights with optional filtering."""
    try:
        insight_type = request.args.get('type')  # periodic, error, etc.
        limit = request.args.get('limit', type=int, default=50)
        skip = request.args.get('skip', type=int, default=0)
        hours = request.args.get('hours', type=int)  # Get insights from last N hours
        
        query = {}
        if insight_type:
            query['insight_type'] = insight_type
        if hours:
            query['created_at'] = {'$gte': datetime.utcnow() - timedelta(hours=hours)}
        
        insights = list(db_manager.db.insights.find(query)
                       .sort('created_at', -1)
                       .skip(skip)
                       .limit(limit))
        
        # Convert ObjectId to string
        for insight in insights:
            insight['_id'] = str(insight['_id'])
        
        total = db_manager.db.insights.count_documents(query)
        
        return jsonify({
            'insights': insights,
            'total': total,
            'limit': limit,
            'skip': skip
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/insights/<insight_id>', methods=['GET'])
def get_insight(insight_id):
    """Get a specific insight by ID."""
    try:
        insight = db_manager.db.insights.find_one({'_id': ObjectId(insight_id)})
        if not insight:
            return jsonify({'error': 'Insight not found'}), 404
        
        insight['_id'] = str(insight['_id'])
        return jsonify(insight), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/insights/latest', methods=['GET'])
def get_latest_insight():
    """Get the latest insight."""
    try:
        insight = db_manager.db.insights.find_one(sort=[('created_at', -1)])
        if not insight:
            return jsonify({'error': 'No insights found'}), 404
        
        insight['_id'] = str(insight['_id'])
        return jsonify(insight), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Errors Endpoints ====================

@app.route('/api/errors', methods=['GET'])
def get_errors():
    """Get errors with optional filtering."""
    try:
        severity_min = request.args.get('severity_min', type=int)
        severity_max = request.args.get('severity_max', type=int)
        priority = request.args.get('priority')  # HIGH, MEDIUM, LOW
        resolved = request.args.get('resolved', type=bool)
        limit = request.args.get('limit', type=int, default=100)
        skip = request.args.get('skip', type=int, default=0)
        hours = request.args.get('hours', type=int)  # Get errors from last N hours
        
        query = {}
        if severity_min is not None or severity_max is not None:
            query['severity'] = {}
            if severity_min is not None:
                query['severity']['$gte'] = severity_min
            if severity_max is not None:
                query['severity']['$lte'] = severity_max
        if priority:
            query['priority'] = priority
        if resolved is not None:
            query['resolved'] = resolved
        if hours:
            query['created_at'] = {'$gte': datetime.utcnow() - timedelta(hours=hours)}
        
        errors = list(db_manager.db.errors.find(query)
                     .sort('created_at', -1)
                     .skip(skip)
                     .limit(limit))
        
        # Convert ObjectId to string
        for error in errors:
            error['_id'] = str(error['_id'])
        
        total = db_manager.db.errors.count_documents(query)
        
        return jsonify({
            'errors': errors,
            'total': total,
            'limit': limit,
            'skip': skip
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/errors/<error_id>', methods=['GET'])
def get_error(error_id):
    """Get a specific error by ID."""
    try:
        error = db_manager.db.errors.find_one({'_id': ObjectId(error_id)})
        if not error:
            return jsonify({'error': 'Error not found'}), 404
        
        error['_id'] = str(error['_id'])
        return jsonify(error), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/errors/<error_id>/resolve', methods=['POST'])
def resolve_error(error_id):
    """Mark an error as resolved."""
    try:
        result = db_manager.db.errors.update_one(
            {'_id': ObjectId(error_id)},
            {'$set': {'resolved': True, 'resolved_at': datetime.utcnow()}}
        )
        if result.matched_count == 0:
            return jsonify({'error': 'Error not found'}), 404
        
        return jsonify({'message': 'Error marked as resolved'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Crashes Endpoints ====================

@app.route('/api/crashes', methods=['GET'])
def get_crashes():
    """Get crashes with optional filtering."""
    try:
        severity_min = request.args.get('severity_min', type=int)
        severity_max = request.args.get('severity_max', type=int)
        crash_type = request.args.get('type')
        resolved = request.args.get('resolved', type=bool)
        limit = request.args.get('limit', type=int, default=100)
        skip = request.args.get('skip', type=int, default=0)
        hours = request.args.get('hours', type=int)  # Get crashes from last N hours
        
        query = {}
        if severity_min is not None or severity_max is not None:
            query['severity'] = {}
            if severity_min is not None:
                query['severity']['$gte'] = severity_min
            if severity_max is not None:
                query['severity']['$lte'] = severity_max
        if crash_type:
            query['crash_type'] = crash_type
        if resolved is not None:
            query['resolved'] = resolved
        if hours:
            query['created_at'] = {'$gte': datetime.utcnow() - timedelta(hours=hours)}
        
        crashes = list(db_manager.db.crashes.find(query)
                      .sort('created_at', -1)
                      .skip(skip)
                      .limit(limit))
        
        # Convert ObjectId to string
        for crash in crashes:
            crash['_id'] = str(crash['_id'])
        
        total = db_manager.db.crashes.count_documents(query)
        
        return jsonify({
            'crashes': crashes,
            'total': total,
            'limit': limit,
            'skip': skip
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/crashes/<crash_id>', methods=['GET'])
def get_crash(crash_id):
    """Get a specific crash by ID."""
    try:
        crash = db_manager.db.crashes.find_one({'_id': ObjectId(crash_id)})
        if not crash:
            return jsonify({'error': 'Crash not found'}), 404
        
        crash['_id'] = str(crash['_id'])
        return jsonify(crash), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/crashes/<crash_id>/resolve', methods=['POST'])
def resolve_crash(crash_id):
    """Mark a crash as resolved."""
    try:
        result = db_manager.db.crashes.update_one(
            {'_id': ObjectId(crash_id)},
            {'$set': {'resolved': True, 'resolved_at': datetime.utcnow()}}
        )
        if result.matched_count == 0:
            return jsonify({'error': 'Crash not found'}), 404
        
        return jsonify({'message': 'Crash marked as resolved'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Processed Logs Endpoints ====================

@app.route('/api/processed-logs', methods=['GET'])
def get_processed_logs():
    """Get processed logs with optional filtering."""
    try:
        cluster_type = request.args.get('cluster_type')
        severity_min = request.args.get('severity_min', type=int)
        severity_max = request.args.get('severity_max', type=int)
        connection_id = request.args.get('connection_id')
        requires_review = request.args.get('requires_review', type=bool)
        limit = request.args.get('limit', type=int, default=100)
        skip = request.args.get('skip', type=int, default=0)
        hours = request.args.get('hours', type=int)
        
        query = {}
        if cluster_type:
            query['cluster_type'] = cluster_type
        if severity_min is not None or severity_max is not None:
            query['severity'] = {}
            if severity_min is not None:
                query['severity']['$gte'] = severity_min
            if severity_max is not None:
                query['severity']['$lte'] = severity_max
        if connection_id:
            query['connection_id'] = connection_id
        if requires_review is not None:
            query['requires_review'] = requires_review
        if hours:
            query['created_at'] = {'$gte': datetime.utcnow() - timedelta(hours=hours)}
        
        logs = list(db_manager.db.processed_logs.find(query)
                   .sort('created_at', -1)
                   .skip(skip)
                   .limit(limit))
        
        # Convert ObjectId to string
        for log in logs:
            log['_id'] = str(log['_id'])
        
        total = db_manager.db.processed_logs.count_documents(query)
        
        return jsonify({
            'logs': logs,
            'total': total,
            'limit': limit,
            'skip': skip
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/processed-logs/<log_id>', methods=['GET'])
def get_processed_log(log_id):
    """Get a specific processed log by ID."""
    try:
        log = db_manager.db.processed_logs.find_one({'_id': ObjectId(log_id)})
        if not log:
            return jsonify({'error': 'Processed log not found'}), 404
        
        log['_id'] = str(log['_id'])
        return jsonify(log), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Raw Logs Endpoints ====================

@app.route('/api/raw-logs', methods=['GET'])
def get_raw_logs():
    """Get raw logs with optional filtering."""
    try:
        connection_id = request.args.get('connection_id')
        processed = request.args.get('processed', type=bool)
        limit = request.args.get('limit', type=int, default=100)
        skip = request.args.get('skip', type=int, default=0)
        hours = request.args.get('hours', type=int)
        
        query = {}
        if connection_id:
            query['connection_id'] = connection_id
        if processed is not None:
            query['processed'] = processed
        if hours:
            query['created_at'] = {'$gte': datetime.utcnow() - timedelta(hours=hours)}
        
        logs = list(db_manager.db.raw_logs.find(query)
                   .sort('created_at', -1)
                   .skip(skip)
                   .limit(limit))
        
        # Convert ObjectId to string
        for log in logs:
            log['_id'] = str(log['_id'])
        
        total = db_manager.db.raw_logs.count_documents(query)
        
        return jsonify({
            'logs': logs,
            'total': total,
            'limit': limit,
            'skip': skip
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/raw-logs/<log_id>', methods=['GET'])
def get_raw_log(log_id):
    """Get a specific raw log by ID."""
    try:
        log = db_manager.db.raw_logs.find_one({'_id': ObjectId(log_id)})
        if not log:
            return jsonify({'error': 'Raw log not found'}), 404
        
        log['_id'] = str(log['_id'])
        return jsonify(log), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Statistics Endpoint ====================

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get overall statistics."""
    try:
        hours = request.args.get('hours', type=int, default=24)
        since = datetime.utcnow() - timedelta(hours=hours)
        
        stats = {
            'time_range_hours': hours,
            'raw_logs': {
                'total': db_manager.db.raw_logs.count_documents({}),
                'processed': db_manager.db.raw_logs.count_documents({'processed': True}),
                'unprocessed': db_manager.db.raw_logs.count_documents({'processed': False}),
                'recent': db_manager.db.raw_logs.count_documents({'created_at': {'$gte': since}})
            },
            'processed_logs': {
                'total': db_manager.db.processed_logs.count_documents({}),
                'recent': db_manager.db.processed_logs.count_documents({'created_at': {'$gte': since}}),
                'by_cluster_type': {}
            },
            'clusters': {
                'total': db_manager.db.clusters.count_documents({}),
                'recent': db_manager.db.clusters.count_documents({'created_at': {'$gte': since}}),
                'by_type': {}
            },
            'errors': {
                'total': db_manager.db.errors.count_documents({}),
                'unresolved': db_manager.db.errors.count_documents({'resolved': False}),
                'recent': db_manager.db.errors.count_documents({'created_at': {'$gte': since}}),
                'high_severity': db_manager.db.errors.count_documents({'severity': {'$gte': 7}})
            },
            'crashes': {
                'total': db_manager.db.crashes.count_documents({}),
                'unresolved': db_manager.db.crashes.count_documents({'resolved': False}),
                'recent': db_manager.db.crashes.count_documents({'created_at': {'$gte': since}}),
                'critical': db_manager.db.crashes.count_documents({'severity': {'$gte': 8}})
            },
            'insights': {
                'total': db_manager.db.insights.count_documents({}),
                'recent': db_manager.db.insights.count_documents({'created_at': {'$gte': since}})
            }
        }
        
        # Get cluster type breakdown
        cluster_types = db_manager.db.processed_logs.distinct('cluster_type')
        for cluster_type in cluster_types:
            stats['processed_logs']['by_cluster_type'][cluster_type] = \
                db_manager.db.processed_logs.count_documents({'cluster_type': cluster_type})
        
        # Get cluster breakdown by type
        cluster_type_counts = db_manager.db.clusters.aggregate([
            {'$group': {'_id': '$cluster_type', 'count': {'$sum': 1}}}
        ])
        for item in cluster_type_counts:
            stats['clusters']['by_type'][item['_id']] = item['count']
        
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok'}), 200


def main():
    print("Starting Anveshak server...")
    
    # Start log processor
    try:
        log_processor.start()
        print("✓ Log processor started")
    except Exception as e:
        print(f"✗ Failed to start log processor: {e}")
    
    # Register shutdown handler
    import atexit
    atexit.register(log_processor.stop)
    
    # Use debug=False in production to avoid auto-restarts
    # Set FLASK_DEBUG=1 in .env if you need debug mode
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host='0.0.0.0', port=8000, debug=debug_mode)


if __name__ == "__main__":
    main()
