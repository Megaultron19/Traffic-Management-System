from process_video import crossing

assert crossing(90, 110, 100) == "down"
assert crossing(110, 90, 100) == "up"
assert crossing(90, 100, 100) == "down"   # touching line counts once
assert crossing(100, 105, 100) is None    # already on/below: no double count
assert crossing(80, 95, 100) is None
assert crossing(120, 130, 100) is None
print("ok")
