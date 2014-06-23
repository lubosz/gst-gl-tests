export VIDEOFILE=/home/bmonkey/workspace/ges/data/hd/fluidsimulation.mp4

gst-launch-1.0 filesrc location=$VIDEOFILE ! qtdemux ! avdec_h264 ! glshader location=rotate.frag ! glimagesink
