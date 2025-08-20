# Gunicorn configuration file for DOI application production deployment
import os
import multiprocessing

# Server socket
bind = "127.0.0.1:5000"
backlog = 2048

# Worker processes
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 100

# Restart workers after this many requests, with up to jitter added, to prevent memory leaks
preload_app = True

# Logging
accesslog = "logs/gunicorn_access.log"
errorlog = "logs/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "doi-app"

# User and group to run as (will be set in deployment)
# user = "doi-app"
# group = "doi-app"

# PID file
pidfile = "/tmp/doi-app.pid"

# Daemonize the Gunicorn process (detach & enter background)
daemon = False

# The maximum size of HTTP request line in bytes
limit_request_line = 4096

# Limit the number of HTTP headers fields in a request
limit_request_fields = 100

# Limit the allowed size of an HTTP request header field
limit_request_field_size = 8190