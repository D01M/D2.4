# ADD THIS INTO server.py

@app.route("/proxy/stations/georgia")
def georgia_stations():

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
        r = requests.get(url, headers=headers, timeout=25)

        return Response(
            r.text,
            status=r.status_code,
            content_type="text/plain"
        )

    except Exception as e:

        return Response(
            str(e),
            status=502,
            content_type="text/plain"
        )
