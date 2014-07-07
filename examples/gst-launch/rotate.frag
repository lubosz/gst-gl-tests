
uniform sampler2D bgl_RenderedTexture;
 
void main() {
    
    vec4 textColor = texture2D(bgl_RenderedTexture, gl_TexCoord[0].xy);
    
    gl_FragColor = textColor;
}
