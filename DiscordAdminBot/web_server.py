from flask import Flask, jsonify
import threading
import logging
import os
from datetime import datetime

class WebServer:
    def __init__(self, bot_instance=None):
        self.app = Flask(__name__)
        self.bot = bot_instance
        self.setup_routes()
        
    def setup_routes(self):
        @self.app.route('/')
        @self.app.route('/health')
        def health_check():
            """Health check endpoint for UptimeRobot monitoring"""
            status = {
                'status': 'online',
                'timestamp': datetime.utcnow().isoformat(),
                'service': 'Discord Admin Bot'
            }
            
            # Add bot status if available
            if self.bot:
                status.update({
                    'bot_ready': self.bot.is_ready(),
                    'guilds_count': len(self.bot.guilds) if self.bot.is_ready() else 0,
                    'latency': round(self.bot.latency * 1000, 2) if self.bot.is_ready() else None
                })
            
            return jsonify(status), 200
            
        @self.app.route('/status')
        def detailed_status():
            """Detailed status endpoint"""
            if not self.bot or not self.bot.is_ready():
                return jsonify({
                    'status': 'bot_not_ready',
                    'message': 'Discord bot is not ready yet'
                }), 503
                
            return jsonify({
                'status': 'operational',
                'bot_user': str(self.bot.user),
                'guilds': len(self.bot.guilds),
                'latency_ms': round(self.bot.latency * 1000, 2),
                'uptime': str(datetime.utcnow()),
                'ready': self.bot.is_ready()
            }), 200
    
    def run(self, host='0.0.0.0', port=8080):
        """Run the Flask web server"""
        try:
            # Disable Flask's default logging to avoid conflicts
            log = logging.getLogger('werkzeug')
            log.setLevel(logging.ERROR)
            
            logging.info(f'Starting web server on {host}:{port}')
            self.app.run(host=host, port=port, debug=False, use_reloader=False)
        except Exception as e:
            logging.error(f'Web server error: {e}')
    
    def start_in_thread(self, host='0.0.0.0', port=8080):
        """Start the web server in a separate thread"""
        server_thread = threading.Thread(
            target=self.run,
            args=(host, port),
            daemon=True
        )
        server_thread.start()
        logging.info(f'Web server thread started on {host}:{port}')
        return server_thread
