# Firefox

* In some situations, in order for Firefox to output the proper a11y tree, the user may need to launch Firefox **after** the call to initialize the atspi registry. (i.e. so launching Firefox after running `make run` in this repo)
* seems to cache elements from other tabs and still gives them `VISIBLE` and `SHOWING` even though they aren't on the current page. Unclear if this is a Firefox issue or if it is due to `gi.repository.Atspi.Accessible.clear_cache()` doesn't work properly to clear atspi state

# Nautilus

Has both `VISIBLE` and `SHOWING` for the sidebar even when certain sidebar elements are hidden.

# Atspi itself

`gi.repository.GLib.GError: atspi_error: The process appears to be hung. (1)`
