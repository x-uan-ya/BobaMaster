import sys
import os

# Add backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.main import app
from mangum import Mangum

# Create the ASGI handler for Vercel serverless
handler = Mangum(app, lifespan="off")
