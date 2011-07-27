#borrowed from Naith
window-title Infinite Procedural Terrain

# Don't limit us to the arbvp1/arbfp1 shader profiles
basic-shaders-only #f

# please work
#dump-generated-shaders #t

# Automatically determine that the GPU supports textures-power-2...
textures-power-2 up
textures-auto-power-2 #t

# Enable multisampling...
framebuffer-multisample #t
multisamples 1

# Portal support so we can clip large chunks of geometry...
allow-portal-cull 1

# Sound off as there are issues right now...
audio-library-name null

#constrained to a harmonic of 60fps (that is, 60, 30, 20, 15, 12, and so on)
sync-video 0

# windowed
#win-size 800 600
# HD
win-size 1280 720

# fullscreen
#win-size 1920 1080
#fullscreen #t

# The distance below which terrain is guaranteed to be loaded and rendered
#max-view-range 500