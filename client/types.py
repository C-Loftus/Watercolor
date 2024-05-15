class WatercolorState:
    enabled: ClassVar[bool] = False
    debug: ClassVar[bool] = False

class A11yElement(TypedDict):
    name: str
    x: int
    y: int