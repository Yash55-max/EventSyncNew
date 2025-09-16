from app import app
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple

# Vercel serverless function handler
def handler(event, context):
    """Vercel serverless function handler"""
    # This is a basic handler - for full Flask support, you might need additional configuration
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': '{"message": "EventSync API is running on Vercel!"}'
    }

# For local development
if __name__ == '__main__':
    app.run(debug=True)
