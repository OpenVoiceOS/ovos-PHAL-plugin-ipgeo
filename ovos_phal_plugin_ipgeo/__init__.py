from ovos_bus_client.util import get_message_lang
from ovos_config.config import LocalConf
from ovos_config import Configuration
from ovos_config.locations import get_webcache_location
from ovos_plugin_manager.phal import PHALPlugin
from ovos_utils import classproperty
from ovos_utils.geolocation import get_ip_geolocation
from ovos_utils.log import LOG
from ovos_utils.messagebus import Message
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
            location = get_ip_geolocation(lang=get_message_lang(message) or Configuration().get("lang", "en"))
            if not location:
                raise ValueError("IP geolocation returned empty location")
            LOG.info(f"IP geolocation: {location}")
            self.web_config["location"] = location
            self.web_config.store()
            LOG.debug(f"Updated config: {self.web_config.path}")
            self.bus.emit(Message("configuration.updated"))
            if message:
                self.bus.emit(message.response(data={'location': location}))
            return
        except ConnectionError as e:
            LOG.error(e)
        except Exception as e:
            LOG.exception(e)
        if message:
            self.bus.emit(message.response(data={'error': True}))

