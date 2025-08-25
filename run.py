# run.py
from api import create_app

# When running locally, we use the DevelopmentConfig
# This enables debug mode and other development-friendly features
app = create_app('api.config.DevelopmentConfig')

if __name__ == '__main__':
    # We run on 0.0.0.0 to make it accessible from outside the container in the future
    # We use port 5001 to avoid conflicts with other common development ports
    app.run(host='0.0.0.0', port=5001)