"""Debug endpoints for troubleshooting."""
from flask import Blueprint, jsonify, request
from db import db_manager
from log_processor import log_processor
from datetime import datetime, timedelta

debug_bp = Blueprint('debug', __name__)

@debug_bp.route('/api/debug/buffer-status', methods=['GET'])
def buffer_status():
    """Get current buffer status."""
    return jsonify({
        'buffer_size': len(log_processor.log_buffer),
        'is_running': log_processor.is_running,
        'batch_size': log_processor.log_buffer[:10] if log_processor.log_buffer else []
    }), 200

@debug_bp.route('/api/debug/raw-logs-count', methods=['GET'])
def raw_logs_count():
    """Get count of raw logs."""
    try:
        total = db_manager.db.raw_logs.count_documents({})
        processed = db_manager.db.raw_logs.count_documents({'processed': True})
        unprocessed = db_manager.db.raw_logs.count_documents({'processed': False})
        recent = db_manager.db.raw_logs.count_documents({
            'created_at': {'$gte': datetime.utcnow() - timedelta(hours=1)}
        })
        
        return jsonify({
            'total': total,
            'processed': processed,
            'unprocessed': unprocessed,
            'recent_1h': recent
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@debug_bp.route('/api/debug/processed-logs-count', methods=['GET'])
def processed_logs_count():
    """Get count of processed logs."""
    try:
        total = db_manager.db.processed_logs.count_documents({})
        recent = db_manager.db.processed_logs.count_documents({
            'created_at': {'$gte': datetime.utcnow() - timedelta(hours=1)}
        })
        
        return jsonify({
            'total': total,
            'recent_1h': recent
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@debug_bp.route('/api/debug/trigger-processing', methods=['POST'])
def trigger_processing():
    """Manually trigger batch processing."""
    try:
        if log_processor.log_buffer:
            log_processor._process_batch()
            return jsonify({
                'message': 'Processing triggered',
                'buffer_size_before': len(log_processor.log_buffer)
            }), 200
        else:
            return jsonify({
                'message': 'No logs in buffer to process',
                'buffer_size': 0
            }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

