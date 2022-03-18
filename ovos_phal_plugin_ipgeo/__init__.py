import requests
from ovos_plugin_manager.phal import PHALPlugin


class IPGeoPlugin(PHALPlugin):
    def __init__(self, bus=None):
        super().__init__(bus, "ip_geolocation")
        self.location = {}
        self.on_reset()  # get initial location data
        self.bus.on("mycroft.internet.connected", self.on_reset)

    def on_reset(self, message=None):
        # geolocate from ip address
        try:
            self.location = self.ip_geolocate()
            # TODO update config
            self.emit("location", self.location)
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


