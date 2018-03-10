# -*- encoding: utf-8 -*-
"""
Python Aplication Template
Licence: GPLv3
"""

from flask import Flask
from flask.ext.bootstrap import Bootstrap
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.pymongo import PyMongo
from flask.ext.login import LoginManager
from flask_socketio import SocketIO
import Queue, pika, threading
import eventlet
eventlet.monkey_patch()

app = Flask(__name__)

app.config['SECRET_KEY'] = 'secret!'
#Configuration of application, see configuration.py, choose one and uncomment.
#app.config.from_object('configuration.ProductionConfig')
app.config.from_object('app.configuration.DevelopmentConfig')
#app.config.from_object('configuration.TestingConfig')

bs = Bootstrap(app) #flask-bootstrap
db = SQLAlchemy(app) #flask-sqlalchemy
socketio = SocketIO(app, async_mode='eventlet')

lm = LoginManager()
lm.setup_app(app)
lm.login_view = 'login'
q = Queue.Queue(100)

def create_connection():
    credentials = pika.PlainCredentials('apps', 'xxx')
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbit.kubernete.cn', credentials=credentials))
    return connection

def create_channel():
    # should separate two functions
    conn = create_connection()
    channel = conn.channel()
    # drone to control center - uplink
    channel.exchange_declare(exchange='flightctl-uplink', exchange_type='fanout')
    result = channel.queue_declare(exclusive=True)
    queue_name = result.method.queue
    channel.queue_bind(exchange='flightctl-uplink', queue=queue_name)
    channel.basic_consume(callback, queue=queue_name, no_ack=True)
    thread = threading.Thread(target=start_consuming,args=(channel,)).start()
    print ("start consumming ...")
    return channel

def callback(ch, method, properties, body):
    global q
    print "CALLBACK: %s" % body
    q.put(body)

def start_consuming(channel):
        channel.start_consuming()

channel = create_channel()

from app import views, models
