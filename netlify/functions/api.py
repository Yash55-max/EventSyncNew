from app import app

def handler(event, context):
    """Netlify serverless function handler"""
    # This is a basic handler - for full Flask support, you might need additional configuration
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': '{"message": "EventSync API is running on Netlify!"}'
    }

if __name__ == '__main__':
    app.run(debug=True)
