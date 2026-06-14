"""
Server Route Patch - Additional Station Network Endpoints
Add these routes to server.py for extended station network support
"""


def add_georgia_stations_endpoint(app):
    """
    Add Georgia stations endpoint (IRIS GO network)
    Usage: Call this function after Flask app initialization
    """
    from flask import Response
    import requests

    @app.route("/proxy/stations/georgia")
    def georgia_stations():
        """
        Fetch seismic stations from Georgia network (GO)
        Uses IRIS FDSN web service
        """
        url = (
            "https://service.iris.edu/fdsnws/station/1/query"
            "?network=GO"
            "&level=station"
            "&format=text"
            "&nodata=404"
        )

        headers = {
            "User-Agent": "OpenSeismo-Lite/1.0"
        }

        try:
            response = requests.get(url, headers=headers, timeout=25)
            return Response(
                response.text,
                status=response.status_code,
                content_type="text/plain"
            )
        except Exception as e:
            return Response(
                str(e),
                status=502,
                content_type="text/plain"
            )

    return app
