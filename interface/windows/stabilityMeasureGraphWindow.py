from interface.windows.graphWindow import GraphWindow


class StabilityMeasureGraphWindow(GraphWindow):
    window_title = "P-IF Graphs"
    graph_title = "Power (IF)"
    y_label = "Power, dBm"
    x_label = "IF, GHz"


class IFPowerDiffGraphWindow(GraphWindow):
    window_title = "Diff P-IF Graphs"
    graph_title = "Power (IF)"
    x_label = "IF, GHz"
    y_label = "Power, dBm"
