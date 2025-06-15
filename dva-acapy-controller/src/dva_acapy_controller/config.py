from os import environ as env


ADMIN_URL = env.get("ADMIN_URL")
ADMIN_LABEL = env.get("ADMIN_LABEL")

PEER_AGENT_URL = env.get("PEER_AGENT_URL")
PEER_CONTROLLER_URL = env.get("PEER_CONTROLLER_URL")
PEER_CONTROLLER_PORT_IN = env.get("PEER_CONTROLLER_PORT_IN")
PEER_CONTROLLER_PORT_OUT = env.get("PEER_CONTROLLER_PORT_OUT")
PEER_LABEL = env.get("PEER_LABEL")

MONGO_URL = env.get("DVA_MONGODB_URL", default="mongodb://localhost:27017")
MONGO_DB = env.get("DVA_MONGODB_DB", default="dva")
MONGO_COLLECTION = env.get("DVA_MONGODB_COLLECTION_REQUESTS", default="requests")

LOG_FILE = "log.json"
