import requests

from ovos_plugin_manager.phal import PHALPlugin
from ovos_config.config import LocalConf
from ovos_config.locations import get_webcache_location
from ovos_utils.messagebus import Message
from ovos_utils.log import LOG
from ovos_utils import classproperty
from ovos_utils.process_utils import RuntimeRequirements


class IPGeoPlugin(PHALPlugin):
    def __init__(self, bus=None, config=None):
        super().__init__(bus, "ovos-phal-plugin-ipgeo", config)
        self.web_config = LocalConf(get_webcache_location())
        self.bus.on("mycroft.internet.connected", self.on_reset)
        self.bus.on("ovos.ipgeo.update", self.on_reset)
        self.on_reset()  # get initial location data

    @classproperty
    def runtime_requirements(self):
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
            LOG.debug("Skipping overwrite of existing location")
            return
        # geolocate from ip address
        try:
            location = self.ip_geolocate()
            LOG.info(f"Got location: {location}")
            self.web_config["location"] = location
            self.web_config.store()
            self.bus.emit(Message("configuration.updated"))
            if message:
                LOG.debug("Emitting location update response")
                self.bus.emit(message.response(
                    data={'location': location}))
            return
        except ConnectionError as e:
            LOG.error(e)
        except Exception as e:
            LOG.exception(e)
        if message:
            LOG.debug("Emitting error response")
            self.bus.emit(message.response(
                data={'error': True}))

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


