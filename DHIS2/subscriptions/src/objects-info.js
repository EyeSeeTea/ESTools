const objectsInfo = [
    {
        type: "MAP",
        field: "map",
        appPath: "dhis-web-mapping",
        visualizationType: "image",
        apiModel: "maps",
    },
    {
        type: "REPORT_TABLE",
        field: "reportTable",
        appPath: "dhis-web-pivot",
        apiModel: "reportTables",
        visualizationType: "html",
    },
    {
        type: "CHART",
        field: "chart",
        appPath: "dhis-web-visualizer",
        apiModel: "charts",
        visualizationType: "image",
    },
    {
        type: "EVENT_REPORT",
        field: "eventReport",
        appPath: "dhis-web-event-reports",
        apiModel: "eventReports",
        visualizationType: "none",
    },
    {
        type: "EVENT_CHART",
        field: "eventChart",
        appPath: "dhis-web-event-visualizer",
        apiModel: "eventCharts",
        visualizationType: "image",
    },
];

module.exports = {objectsInfo};