"""Vercel API handler for serverless deployment."""

from app.main import app

# This will be called by Vercel
handler = app
