attribute vec4 position;
attribute vec2 uv;
uniform mat4 mvp;
varying vec2 out_uv;

void main()
{
         gl_Position = mvp * position;
         out_uv = uv;
}