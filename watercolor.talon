os: linux
# and not tag: user.rango_direct_clicking
# and tag: browser
-

^(watercolor | color) toggle$:
    user.watercolor_toggle_hats()

color refresh:
    user.watercolor_refresh()

color <user.watercolor_hint>:
    user.watercolor_action("click", user.watercolor_hint)

# Dump the a11y element to the log for debugging purposes
inspect <user.watercolor_hint>:
    user.watercolor_action("inspect", user.watercolor_hint)
