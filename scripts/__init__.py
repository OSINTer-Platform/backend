from modules import config, misc

misc.create_folder("logs")
config.configure_logger("osinter")

config_options = config.BackendConfig()
