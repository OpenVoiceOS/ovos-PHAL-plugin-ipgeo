import requests
from ovos_plugin_manager.phal import PHALPlugin
from ovos_utils.configuration import get_webcache_location, LocalConf
from ovos_utils.messagebus import Message
from ovos_backend_client.api import GeolocationApi
from ovos_backend_client.backends import BackendType


class IPGeoPlugin(PHALPlugin):
    def __init__(self, bus=None, config=None):
        super().__init__(bus, "ovos-phal-plugin-ipgeo", config)
        self.location = {}
        self.web_config = LocalConf(get_webcache_location())
        self.bus.on("mycroft.internet.connected", self.on_reset)
        self.bus.on("ovos.ipgeo.update", self.on_reset)
        self.on_reset()  # get initial location data

    def on_reset(self, message=None):
        # we update the remote config to allow
        # both backend and user config to take precedence
        # over ip geolocation
        if self.web_config.get("location") and \
                (message is None or not message.data.get('overwrite')):
            return
        # geolocate from ip address
        try:
            self.location = self.ip_geolocate()
            self.web_config["location"] = self.location
            self.web_config.store()
            self.bus.emit(Message("configuration.updated"))
            if message:
                self.bus.emit(message.response(
                    data={'location': self.location}))
        except:
            pass

    @staticmethod
    def ip_geolocate(ip=None):
        try:
            # configured backend may throw some errors if its down
            api = GeolocationApi()
            return api.get_ip_geolocation(ip)
        except:
            # force offline backend api (direct call)
            api = GeolocationApi(backend_type=BackendType.OFFLINE)
            return api.get_ip_geolocation(ip)
