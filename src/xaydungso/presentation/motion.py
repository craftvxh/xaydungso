"""Short ease-out transitions so panels and dialogs don't pop in abruptly.

Only the *appearing* step is animated: widgets become visible immediately (so
state checks stay simple) and grow/fade in over ~180 ms. Hiding is instant.
"""

from PyQt6.QtCore import QEasingCurve, QPoint, QPropertyAnimation

DURATION = 180
UNLIMITED = 16_777_215  # QWIDGETSIZE_MAX


def _run(widget, prop, start, end, done=None, duration=DURATION):
    animation = QPropertyAnimation(widget, prop, widget)
    animation.setDuration(duration)
    animation.setStartValue(start)
    animation.setEndValue(end)
    animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    if done is not None:
        animation.finished.connect(done)
    widget._xds_animation = animation  # Keep a reference while it runs.
    animation.start()


def slide_in_width(widget, width):
    """Show a fixed-width side panel by growing it from 0 to its width."""
    if widget.isVisible():
        return
    widget.setMinimumWidth(0)
    widget.setMaximumWidth(0)
    widget.setVisible(True)
    _run(widget, b"maximumWidth", 0, width, lambda: widget.setFixedWidth(width))


def unroll_height(widget):
    """Show a bar by growing its height from 0 to its natural height."""
    if widget.isVisible():
        return
    height = max(widget.sizeHint().height(), 1)
    widget.setMaximumHeight(0)
    widget.setVisible(True)
    _run(
        widget,
        b"maximumHeight",
        0,
        height,
        lambda: widget.setMaximumHeight(UNLIMITED),
    )


def fade_in_window(window, rise=10):
    """Fade a top-level window in while it rises a few pixels into place."""
    target = window.pos()
    window.setWindowOpacity(0.0)
    window.move(target + QPoint(0, rise))
    _run(window, b"windowOpacity", 0.0, 1.0)
    position = QPropertyAnimation(window, b"pos", window)
    position.setDuration(DURATION)
    position.setStartValue(target + QPoint(0, rise))
    position.setEndValue(target)
    position.setEasingCurve(QEasingCurve.Type.OutCubic)
    window._xds_rise = position
    position.start()
