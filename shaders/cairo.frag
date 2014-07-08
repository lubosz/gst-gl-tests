varying vec2 out_uv;
uniform sampler2DRect cairoSampler;

void main()
{
        gl_FragColor = texture2DRect (cairoSampler, out_uv);
}