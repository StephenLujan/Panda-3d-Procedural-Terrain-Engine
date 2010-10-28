
uniform float region1min;
uniform float region1max;
uniform float region2min;
uniform float region2max;
uniform float region3min;
uniform float region3max;
uniform float region4min;
uniform float region4max;

uniform sampler2D region1ColorMap;
uniform sampler2D region2ColorMap;
uniform sampler2D region3ColorMap;
uniform sampler2D region4ColorMap;

varying vec4 normal;

vec4 GenerateTerrainColor()
{
    vec4 terrainColor = vec4(0.0, 0.0, 0.0, 1.0);
    float height = normal.w;
    float regionMin = 0.0;
    float regionMax = 0.0;
    float regionRange = 0.0;
    float regionWeight = 0.0;
    
    // Terrain region 1.
    regionRange = region1max - region1min;
    regionWeight = (regionRange - abs(height - region1max)) / regionRange;
    regionWeight = max(0.0, regionWeight);
    terrainColor += regionWeight * texture2D(region1ColorMap, gl_TexCoord[0].st);

    // Terrain region 2.
    regionRange = region2max - region2min;
    regionWeight = (regionRange - abs(height - region2max)) / regionRange;
    regionWeight = max(0.0, regionWeight);
    terrainColor += regionWeight * texture2D(region2ColorMap, gl_TexCoord[0].st);

    // Terrain region 3.
    regionRange = region3max - region3min;
    regionWeight = (regionRange - abs(height - region3max)) / regionRange;
    regionWeight = max(0.0, regionWeight);
    terrainColor += regionWeight * texture2D(region3ColorMap, gl_TexCoord[0].st);

    // Terrain region 4.
    regionRange = region4max - region4min;
    regionWeight = (regionRange - abs(height - region4max)) / regionRange;
    regionWeight = max(0.0, regionWeight);
    terrainColor += regionWeight * texture2D(region4ColorMap, gl_TexCoord[0].st);

    return terrainColor;
}

void main()
{   
    vec3 n = normalize(normal.xyz);

    float nDotL = max(0.0, dot(n, gl_LightSource[0].position.xyz));
        
    vec4 ambient = vec4(0.5, 0.5, 0.5, 1.0);//gl_FrontLightProduct[0].ambient;
    vec4 diffuse = gl_FrontLightProduct[0].diffuse * nDotL;
    vec4 color = gl_FrontLightModelProduct.sceneColor + ambient + diffuse;   
    
    gl_FragColor = color * GenerateTerrainColor();
}
