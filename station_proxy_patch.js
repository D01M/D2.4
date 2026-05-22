// Replace direct station API URLs like:
// https://service.iris.edu/fdsnws/station/1/query...
// with:
// /proxy/stations/iris
//
// Replace GFZ/GEOFON station URLs with:
// /proxy/stations/geofon
//
// Example:
const stationSources = [
    {
        name: "IRIS/SAGE",
        url: "/proxy/stations/iris",
        format: "fdsn-text"
    },
    {
        name: "GFZ/GEOFON",
        url: "/proxy/stations/geofon",
        format: "fdsn-text"
    }
];
