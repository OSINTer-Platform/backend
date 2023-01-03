from dotenv import load_dotenv
from modules import config, misc

load_dotenv()

misc.create_folder("logs")
config.configure_logger("osinter")

config_options = config.BackendConfig()
