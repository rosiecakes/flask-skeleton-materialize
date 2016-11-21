# project/server/config.py

import os
basedir = os.path.abspath(os.path.dirname(__file__))

GOOGLE_API_KEY = 'AIzaSyB-Q4n0dg9bffHNHU7QSw1Or1ulzJzRP5E'
ZOMATO_API_KEY = '7d38a6c3811607de8a861188875d55d5'

DATABASE_NAME = 'restaurants.db'

zomato_header = {
    'User-agent': 'My User Agent 1.0',
    'Accept': 'application/json',
    'user-key': ZOMATO_API_KEY
}

class BaseConfig(object):
    """Base configuration."""
    SECRET_KEY = 'my_precious'
    DEBUG = False
    BCRYPT_LOG_ROUNDS = 13
    WTF_CSRF_ENABLED = True
    DEBUG_TB_ENABLED = False
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(BaseConfig):
    """Development configuration."""
    DEBUG = True
    BCRYPT_LOG_ROUNDS = 4
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'dev.sqlite')
    DEBUG_TB_ENABLED = True


class TestingConfig(BaseConfig):
    """Testing configuration."""
    DEBUG = True
    TESTING = True
    BCRYPT_LOG_ROUNDS = 4
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///'
    DEBUG_TB_ENABLED = False
    PRESERVE_CONTEXT_ON_EXCEPTION = False


class ProductionConfig(BaseConfig):
    """Production configuration."""
    SECRET_KEY = 'my_precious'
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'postgresql://localhost/example'
    DEBUG_TB_ENABLED = False
