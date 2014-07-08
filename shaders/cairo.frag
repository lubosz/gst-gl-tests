varying vec2 out_uv;
uniform sampler2DRect cairoSampler;

void main()
{
        vec4 cairo = texture2DRect (cairoSampler, out_uv);
        gl_FragColor =  cairo; // + vec4(1.0,0,0,0.1) * (1.0 - cairo.w);
}