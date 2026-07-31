# PHAL plugin - IPGeo

This plugin sets the default location for OpenVoiceOS based on the IP address of the device. It queries [ip-api.com](https://ip-api.com) and stores the result in the local configuration.

The plugin does not overwrite a location that a user or a backend already set. It only fills in the location if the value is missing.

The `City`, `regionName`, and `country` fields are localized to the active language when possible. Supported languages are `en`, `de`, `es`, `pt`, `fr`, `ja`, `zh`, and `ru`.

## Install

```bash
pip install ovos-phal-plugin-ipgeo
```

## Usage

OVOS loads this plugin through the PHAL plugin manager. No manual setup is required.

The plugin geolocates the device on these bus messages:

- `mycroft.internet.connected`: sent when the device gets an internet connection.
- `ovos.ipgeo.update`: sent to request a location update. Send `overwrite: true` in the message data to replace an existing location.

## Related projects

- [OpenVoiceOS/PHAL](https://github.com/OpenVoiceOS/PHAL): the plugin host that loads this plugin.
- [OpenVoiceOS/ovos-PHAL-plugin-gpsd](https://github.com/OpenVoiceOS/ovos-PHAL-plugin-gpsd): sets the device location from a GPS receiver.
- [OpenVoiceOS/ovos-PHAL-plugin-connectivity-events](https://github.com/OpenVoiceOS/ovos-PHAL-plugin-connectivity-events): reports network connectivity changes on the bus.

## License

Apache-2.0
