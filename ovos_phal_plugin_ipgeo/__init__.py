from ovos_bus_client.util import get_message_lang
from ovos_config.config import update_mycroft_config
from ovos_config import Configuration
from ovos_config.locations import ASSISTANT_CONFIG
from ovos_plugin_manager.phal import PHALPlugin
from ovos_utils import classproperty
from ovos_utils.geolocation import get_ip_geolocation
from ovos_utils.log import LOG
from ovos_bus_client.message import Message
from ovos_utils.process_utils import RuntimeRequirements


class IPGeoPlugin(PHALPlugin):
    def __init__(self, bus=None, config=None):
        super().__init__(bus, "ovos-phal-plugin-ipgeo", config)
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
        # geolocate from ip address
        try:
            location = get_ip_geolocation(lang=get_message_lang(message) or Configuration().get("lang", "en"))
            if not location:
                raise ValueError("IP geolocation returned empty location")
            LOG.info(f"IP geolocation: {location}")

            update_mycroft_config(config={"location": location}, bus=self.bus)

            LOG.debug(f"Updated config: {ASSISTANT_CONFIG}")
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

