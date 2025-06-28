class Channel():
    def __init__(self,From,To) -> None:
        self.ID_from = From
        self.ID_to = To
    def __eq__(self, __value: object) -> bool:
        return self.ID_from == __value

ROUTING = [
    Channel(30,808073771532812301),
    Channel(808073771532812301,30),
    Channel(3043,922499261319499867),
    Channel(922499261319499867,3043),
    Channel(28,1233431876870606972),
    Channel(1233431876870606972,28),
    Channel(5,1271220390189990041),
    Channel(1271220390189990041,5),
    Channel(-1,3043),
    Channel(3043,-1),
    Channel(1,-1),
    Channel(30,-1),
    Channel(28,-1),
    Channel(32,-1)
]
