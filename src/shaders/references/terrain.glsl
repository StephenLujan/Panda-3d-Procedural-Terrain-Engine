This shader performs procedural terrain texturing. This shader takes the vertex
height of the terrain and 4 tileable terrain textures and mixes these in the
fragment shader to produce a seamlessly blended terrain texture.

A good article that describes the algorithms used in this shader can be found
here: http://jeff.bagu.org/articles/ptg4heightmaps.html

This shader requires vertices that contain a vertex normal and a sets of
texture coordinates.

The set of texture coordinates is for the height map texture stretched
across the entire terrain mesh. The fragment shader will use this 1st set of
texture coordinates to determine the terrain height at the given fragment
location. 

The vertex shader will generate a second set of texture coordinates. The 2nd
set of texture coordinates is for the tileable terrain textures. These
texture coordinates determines the overall resolution of the resulting
procedural terrain texture. If this set of texture coordinates is not tiled
(i.e., the terrain texture tile is stretched across the entire terrain) or the
repeat factor is very low then the resulting procedural terrain texture will be
very blurred and will look like a very low resolution terrain texture stretched
across the terrain. Increasing the amount of texture repeating will produce a
higher resolution terrain texture. For tileable terrain textures that are
512 x 512 a texture repeat factor of 12 gives pretty good results. There's a
trade off though. If you tile the terrain textures too much then the resulting
procedural terrain texture will look tiled. But this really depends on the
quality of the tileable terrain textures.

The vertex shader is pretty simple and doesn't do much. It transforms the
vertex normal and passes on the 2 sets of texture coordinates for the terrain
geometry. The height of the terrain at each vertex is passed onto the fragment
shader. The height is stored in the normal vector's 'w' component. Passing the
vertex height this way to the fragment shader means that we don't need to look
up the terrain height from the heightmap texture in the fragement shader.

The fragment shader is where all the work is done. Simple diffuse per-fragment
lighting is applied to the terrain mesh. The resulting lit color is then
modulated with the terrain texture color as calculated by the
GenerateTerrainColor() function.

The procedural terrain texture is created using the information stored in the
TerrainRegion structures. A terrain region determines the height range that a
particular type of terrain is found. This shader is hard coded to use 4 terrain
regions.

[vert]

#version 120

uniform float tilingFactor;

varying vec4 normal;

void main()
{
    normal.xyz = normalize(gl_NormalMatrix * gl_Normal);
    normal.w = gl_Vertex.y;

    gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
    gl_TexCoord[0] = gl_MultiTexCoord0 * tilingFactor;
}

[frag]

#version 120

struct TerrainRegion
{
    float min;
    float max;
};

uniform TerrainRegion region1;
uniform TerrainRegion region2;
uniform TerrainRegion region3;
uniform TerrainRegion region4;

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
    regionMin = region1.min;
    regionMax = region1.max;
    regionRange = regionMax - regionMin;
    regionWeight = (regionRange - abs(height - regionMax)) / regionRange;
    regionWeight = max(0.0, regionWeight);
    terrainColor += regionWeight * texture2D(region1ColorMap, gl_TexCoord[0].st);

    // Terrain region 2.
    regionMin = region2.min;
    regionMax = region2.max;
    regionRange = regionMax - regionMin;
    regionWeight = (regionRange - abs(height - regionMax)) / regionRange;
    regionWeight = max(0.0, regionWeight);
    terrainColor += regionWeight * texture2D(region2ColorMap, gl_TexCoord[0].st);

    // Terrain region 3.
    regionMin = region3.min;
    regionMax = region3.max;
    regionRange = regionMax - regionMin;
    regionWeight = (regionRange - abs(height - regionMax)) / regionRange;
    regionWeight = max(0.0, regionWeight);
    terrainColor += regionWeight * texture2D(region3ColorMap, gl_TexCoord[0].st);

    // Terrain region 4.
    regionMin = region4.min;
    regionMax = region4.max;
    regionRange = regionMax - regionMin;
    regionWeight = (regionRange - abs(height - regionMax)) / regionRange;
    regionWeight = max(0.0, regionWeight);
    terrainColor += regionWeight * texture2D(region4ColorMap, gl_TexCoord[0].st);

    return terrainColor;
}

void main()
{   
    vec3 n = normalize(normal.xyz);

    float nDotL = max(0.0, dot(n, gl_LightSource[0].position.xyz));
        
    vec4 ambient = gl_FrontLightProduct[0].ambient;
    vec4 diffuse = gl_FrontLightProduct[0].diffuse * nDotL;
    vec4 color = gl_FrontLightModelProduct.sceneColor + ambient + diffuse;   
    
    gl_FragColor = color * GenerateTerrainColor();
}
