import requests

from ovos_plugin_manager.phal import PHALPlugin
from ovos_config.config import LocalConf
from ovos_config.locations import get_webcache_location
from ovos_utils.messagebus import Message
from ovos_utils import classproperty
from ovos_utils.process_utils import RuntimeRequirements


class IPGeoPlugin(PHALPlugin):
    def __init__(self, bus=None, config=None):
        super().__init__(bus, "ovos-phal-plugin-ipgeo", config)
        self.location = {}
        self.web_config = LocalConf(get_webcache_location())
        self.bus.on("mycroft.internet.connected", self.on_reset)
        self.bus.on("ovos.ipgeo.update", self.on_reset)
        self.on_reset()  # get initial location data

    @classproperty
    def runtime_requirements(self):
        """ developers should override this if they do not require connectivity
         some examples:
         IOT plugin that controls devices via LAN could return:
            scans_on_init = True
            NetworkRequirements(internet_before_load=False,
                                 network_before_load=scans_on_init,
                                 requires_internet=False,
                                 requires_network=True,
                                 no_internet_fallback=True,
                                 no_network_fallback=False)
         online search plugin with a local cache:
            has_cache = False
            NetworkRequirements(internet_before_load=not has_cache,
                                 network_before_load=not has_cache,
                                 requires_internet=True,
                                 requires_network=True,
                                 no_internet_fallback=True,
                                 no_network_fallback=True)
         a fully offline plugin:
            NetworkRequirements(internet_before_load=False,
                                 network_before_load=False,
                                 requires_internet=False,
                                 requires_network=False,
                                 no_internet_fallback=True,
                                 no_network_fallback=True)
        """
        return RuntimeRequirements(internet_before_load=True,
                                   network_before_load=True,
                                   requires_internet=True,
                                   requires_network=True,
                                   no_internet_fallback=False,
                                   no_network_fallback=False)

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
        if not ip or ip in ["0.0.0.0", "127.0.0.1"]:
            ip = requests.get('https://api.ipify.org').text
        fields = "status,country,countryCode,region,regionName,city,lat,lon,timezone,query"
        data = requests.get("http://ip-api.com/json/" + ip,
                            params={"fields": fields}).json()
        region_data = {"code": data["region"],
                       "name": data["regionName"],
                       "country": {
                           "code": data["countryCode"],
                           "name": data["country"]}}
        city_data = {"code": data["city"],
                     "name": data["city"],
                     "state": region_data}
        timezone_data = {"code": data["timezone"],
                         "name": data["timezone"]}
        coordinate_data = {"latitude": float(data["lat"]),
                           "longitude": float(data["lon"])}
        return {"city": city_data,
                "coordinate": coordinate_data,
                "timezone": timezone_data}


