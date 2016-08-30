# Configure Swagger Python client

# Remove basic auth from the configuration.py file in the client package
# Import Settings from settings and set the host default as Settings().***
# Add this file to the client package


def configure_auth(value, prefix='Token', label='Authorization'):
    import configuration
    config = configuration.Configuration()
    config.api_key_prefix.update({label: prefix})
    config.api_key.update({label: value})


def configure_auth_basic(username, password):
    from apis.ops_api import OpsApi

    credentials = {"username": username, "password": password}

    ret = OpsApi().api_token_auth_post(data=credentials)

    token = ret.token

    configure_auth(token)


def configure_host(value):
    import configuration
    config = configuration.Configuration()
    config.host = value
