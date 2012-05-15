
#http://www.panda3d.org/manual/index.php/Configuring_Panda3D

window-title Infinite Procedural Terrain

# Don't limit us to the arbvp1/arbfp1 shader profiles
basic-shaders-only #f

# Dump all shaders
#dump-generated-shaders #t

show-frame-rate-meter #t
show-occlusion 0
show-tex-mem 0

#constrained to a harmonic of 60fps (that is, 60, 30, 20, 15, 12, and so on)
sync-video 0

# windowed
# 4:3
#win-size 800 600
# small 16:9
win-size 1067 600
# HD
#win-size 1280 720

# fullscreen full HD
#win-size 1920 1080
#fullscreen #t

# field of view of screen Y in degrees (panda default is 30)
# A larger fov brings more local detail in the picture and makes the limit of
# the terrain a bit less noticeable.
default-fov 60

# Camera clipping distance
default-far 10000
default-near 0.01

# Portal support so we can clip large chunks of geometry...
allow-portal-cull 1

# Automatically determine that the GPU supports textures-power-2...
textures-power-2 up
textures-auto-power-2 #t

# Enable multisampling...
framebuffer-multisample #t
multisamples 1

#http://www.panda3d.org/manual/index.php/Multithreaded_Render_Pipeline
threading-model Cull/Draw

# Sound off as there are issues right now...
audio-library-name null

############################################################################
# --- Terrain Engine Specific Settings ---

# The distance below which terrain is guaranteed to be loaded and rendered
max-view-range 100
max-terrain-height 300.0
terrain-horizontal-stretch 1.0

save-height-maps #f
save-slope-maps #f
save-texture-maps #f
save-vegetation-maps #f

thread-load-terrain #f
brute-force-tiles #t