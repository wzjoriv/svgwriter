"""
Motion over time: scenes, frame rendering and video.

Sub-packages
------------
video
    Scenes, frame rendering through a pluggable renderer, behaviors and
    encoding with ffmpeg.

Notes
-----
The top-level package re-exports this, so ``svg.video`` and ``svg.Scene``
work without this path. The group itself imports nothing.

Examples
--------
>>> from svgwriter.motion.video import Scene
>>> import svgwriter as svg
>>> Scene is svg.Scene
True
"""
